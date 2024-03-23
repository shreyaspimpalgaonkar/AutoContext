import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
import base64

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

SENDERS = ["alphasignal"]

SENDERS_STR = ', '.join(SENDERS)

def get_emails(service, query):
    """Retrieves emails matching the given query."""
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    emails = []
    for message in messages:
        msg = service.users().messages().get(userId="me", id=message["id"]).execute()
        payload = msg["payload"]
        headers = payload["headers"]
        for header in headers:
            if header["name"] == "Subject":
                subject = header["value"]
            if header["name"] == "From":
                sender = header["value"]
        if "data" in payload["body"]:
            data = payload["body"]["data"]
        else:
            data = None
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"]["data"]
                    break
        if data:
            text = base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8")
            emails.append({"subject": subject, "sender": sender, "content": text})
    return emails


def filter_emails(emails):
    """Filters emails to only include those from the given sender."""
    filtered_emails = []
    for email in emails:
        if email["sender"] in SENDERS_STR:
            filter_emails.append(email)
    return filtered_emails
            

def get_list_of_emails():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    # get yesterday's emails
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y/%m/%d")
    query = f"after:{yesterday}"
    # results = service.users().messages().list(userId="me", q=query).execute()
    emails = get_emails(service, query)
    
    filtered_emails = filter_emails(emails)
    
    return filtered_emails

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
    get_list_of_emails()