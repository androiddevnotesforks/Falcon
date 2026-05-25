import base64

from bs4 import BeautifulSoup
from dateutil.parser import parse
from google_py_apis.gmail_api import GmailAPI

import util
from params import root_dir
from util import get_key
from datetime import datetime, timedelta


def resolve_label_id(label_name, created_label_names, created_label_ids, falcon_client):
    """Resolve a label name to its Gmail ID, creating nested labels as needed."""
    prev_node = ""
    label_id = None
    for label_node in label_name.split("/"):
        if len(prev_node) > 0:
            label_node = f"{prev_node}/{label_node}"

        label_id = created_label_names.get(label_node, None)
        if label_id is None:
            util.log(f"Label [{label_node}] not found, creating it.")
            label_id = falcon_client.gmail.create_label(label_node)["id"]
            created_label_names[label_node] = label_id
            created_label_ids[label_id] = label_node

        prev_node = label_node

    return label_id


def process_gmail_dic(mail):
    mail_id = mail["id"]

    sender = None
    subject = None
    text = None
    date_time = None
    unsubscribe_option = None
    files = []
    attachment_ids = []
    html_parts = []

    for part in mail["payloads"]:

        for header in part.get("headers", []):
            header_name = header["name"].lower()
            header_value = header["value"]

            # Get sender email
            if header_name == "from":
                sender = header_value.split(" ")[-1].strip("<>")
                sender = util.clean_sender(sender)

            elif header_name == "subject":
                subject = header_value

            elif header_name == "date":
                date_time = parse(header_value)

            elif header_name == "list-unsubscribe":
                unsubscribe_option = header_value

        mime_type = get_key(part, ["mimeType"])
        data = get_key(part, ["body", "data"])
        attachment_id = get_key(part, ["body", "attachmentId"])
        filename = get_key(part, ["filename"], "")

        if len(filename) > 0:
            files.append(filename)
            attachment_ids.append(attachment_id)
            continue

        if data is None:
            continue

        data = base64.urlsafe_b64decode(data).decode()
        if "html" in mime_type:
            while len(data) > 0:
                html_end = data.find("</html>")
                if html_end == -1:
                    data.find("</HTML>")
                if html_end == -1:
                    break
                html_end = html_end + len("</html>")
                html_part = data[:html_end]
                html_parts.append(html_part)
                data = data[html_end:]

            for html_part in html_parts:
                soup = BeautifulSoup(html_part, "lxml")
                text = soup.text

                # double check in html content to see if something's found
                if unsubscribe_option is None:
                    checklist = [
                        "opt-out",
                        "unsubscribe",
                        "edit your notification settings",
                    ]
                    for link in soup.find_all("a", href=True):
                        link_text = link.text.strip().lower()
                        if any(item in link_text for item in checklist):
                            unsubscribe_option = link["href"]
                            break

        elif mime_type == "text/plain":
            if text is None:
                text = data
        else:
            util.log(f"Unseen mime-type found [{mime_type}].")

    if unsubscribe_option is not None and len(unsubscribe_option) == 0:
        unsubscribe_option = None

    processed_data = {
        "Id": str(mail_id),
        "Sender": sender,
        "Subject": subject,
        "Text": text,
        "Unsubscribe": unsubscribe_option,
        "Files": files,
        "AttachmentIds": attachment_ids,
        "DateTime": date_time,
        "Htmls": html_parts,
        "Snippet": mail["snippet"],
        "LabelIds": {i for i in mail.get("labelIds", [])},
    }

    return processed_data


def iterate_gmail_messages(falcon_client, get_query, num_days):
    if get_query is None:
        get_query = ""

    after = datetime.now() - timedelta(days=num_days)

    get_query += f" after:{after.strftime('%Y/%m/%d')}"
    get_query += " -in:sent"
    get_query += " -in:trash"
    get_query.strip()

    mails = falcon_client.gmail.list_mails(query=get_query, max_pages=10000)
    for mail in mails:
        try:
            mail_id = mail["id"]

            mail_full = falcon_client.gmail.get_mail(mail_id)
            mail_processed = process_gmail_dic(mail_full)

            yield mail_id, mail_full, mail_processed
        except Exception as e:
            util.error(f"Error processing mail with id [{mail_id}]. Error: {str(e)}")


class FalconClient:
    def __init__(self, email, key):
        self.email = email
        self.gmail = GmailAPI(self.email, root_dir, key)
        self.gmail.auth()
