import time

import util
from falcon import resolve_label_id  # noqa: F401 — re-exported for callers


def apply_label_changes(falcon_client, mail_id, original_label_ids, mail_processed):
    """Apply label changes to Gmail based on diff between original and current LabelIds."""
    current_label_ids = mail_processed["LabelIds"]
    add_label_ids = list(current_label_ids - original_label_ids)
    remove_label_ids = list(original_label_ids - current_label_ids)

    if add_label_ids or remove_label_ids:
        falcon_client.gmail.add_remove_labels(mail_id, add_label_ids, remove_label_ids)


def trash_email(falcon_client, mail_id):
    """Move a single email to trash."""
    falcon_client.gmail.move_to_trash(mail_id)


def consolidate_spam(falcon_client):
    """Move all spam to trash."""
    query = "in:spam"
    mails = falcon_client.gmail.list_mails(query=query, max_pages=10000)
    for mail in mails:
        falcon_client.gmail.move_to_trash(mail["id"])
        time.sleep(0.5)
