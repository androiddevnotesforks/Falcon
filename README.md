#### Rule based email processing.

###### How to set it up

- Run `pip install -r requirements.txt`
- Build the desktop_credentials.json file for GMail API.
    - Follow [these](https://gist.github.com/siddhantkushwaha/42ebc0a6d3348b0f62fb4b5e769876ed) steps to build the
      credentials.
    - Move it inside config/.
- Add emails.json inside `data/`, it should look like data/emails_templates.json
- Run `python/manage.py --update_rules` to push rules from `data/rules.csv` to SQL db.
- Run `python/cleanup.py`

###### Adding more rules to rules.csv

- The rules csv has below fields
    * `type` - If given query applies to true, this command type will be applied.
        * `blacklist` - Move to trash.
        * `whitelist` - Falcon will skip this email.
        * `-label:<label-name>` - Given label will be removed from email.
        * `+label:<label-name>` - Given label will be added to the email. A new label is created if one does not exist already.
    * `query` - A python expression that needs to evaluate to true for this rule to be applied. Some variables available for us to work with
      * `sender` - Email ID.
      * `labels` - Label names associated with given email.
      * `tags` - 
      * `subject` - Email subject.
      * `snippet` - Email snippet.
      * `text` - Email body text.
      * `subject_snippet` - Email subject plus snippet.
      * `content` - Entire email content in text.
      * `timediff` - How old in the email in seconds.
      * `day` - Duration of a day in seconds.
      * `week` - Duration of a week in seconds.
    * `apply_to` - A coma separated list of email ids or `all`.
    * `order` - Order in which rules will be evaluated for a given email.
    * `args` - Miscellaneous arguments, coma separated.
        * `skip others` - If given rule evaluates to true, other rules will be skipped.
- Some sample rules
  *
