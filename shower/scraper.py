import os.path

import datetime
import base64
from modal import Image, method

import io
import tempfile

from modal import Image, method, enter

from .common import stub


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

SENDERS = ["alphasignal"]

SENDERS_STR = ', '.join(SENDERS)

def get_emails(service, query):
    
    """Retrieves emails matching the given query."""
    print("Getting emails")
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
    
  from google.auth.transport.requests import Request
  from google.oauth2.credentials import Credentials
  from google_auth_oauthlib.flow import InstalledAppFlow
  from googleapiclient.discovery import build
  from googleapiclient.errors import HttpError
  
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  
  # install credentials manually
  import json
  cred = {"installed":{"client_id":"133373018966-8g5bdc22v64hi140eh1j74mvna5ivjlj.apps.googleusercontent.com","project_id":"robotic-code-414000","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["http://localhost"]}}
  # save credentials to file
  with open("credentials.json", "w") as f:
    json.dump(cred, f)
    
  token = {"token": "ya29.a0Ad52N3_xO7ChdMto_OMCctcTowdv2gqC44Ax15Ppd_GubwJQGkh1fqtIDFiL3CD7vmcnNTMS_qcfjGhWZ1ATSRnuxRyVs7Hap6UmQvlQUi6KrgccIdxfJxCMBOa8sktcmJ9WvuOF6MLQdEhTxUqm3RPTSUN1Q9_6RDenaCgYKARcSARASFQHGX2MiyTXN0gNlbintSBTP7i_LJA0171", "refresh_token": "1//05Q73DxqdBwmSCgYIARAAGAUSNwF-L9Irm5mmjPoIdD2wjAozBsQCBb4EtbwjDkxHlK8_1RfHVWRGhlXFZNDru_a_N7ZRo2JH2wI", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "133373018966-8g5bdc22v64hi140eh1j74mvna5ivjlj.apps.googleusercontent.com", "client_secret": "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", "scopes": ["https://www.googleapis.com/auth/gmail.readonly"], "universe_domain": "googleapis.com", "account": "", "expiry": "2024-03-23T20:00:52.181415Z"}
    # save token to file
  with open("token.json", "w") as f:
    json.dump(token, f)
  
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
    
    filtered_emails = emails # filter_emails(emails)
    
    return filtered_emails

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


def download_models():
    from tortoise.api import MODELS_DIR, TextToSpeech

    tts = TextToSpeech(models_dir=MODELS_DIR)
    tts.get_random_conditioning_latents()


tortoise_image = (
    Image.debian_slim(python_version="3.10.8")  # , requirements_path=req)
    .apt_install("git", "libsndfile-dev", "ffmpeg", "curl")
    .pip_install(
        "torch==2.0.0",
        "torchvision==0.15.1",
        "torchaudio==2.0.1",
        "pydub==0.25.1",
        "transformers==4.25.1",
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'anthropic',
        extra_index_url="https://download.pytorch.org/whl/cu117",
    )
    .pip_install("git+https://github.com/metavoicexyz/tortoise-tts")
    .run_function(download_models)
)


@stub.cls(
    image=tortoise_image,
    container_idle_timeout=300,
    timeout=180,
)  
class Scraper:
        
    # @enter()
    @method()
    def get_claude_prompt(self):
                
        self.emails = get_list_of_emails()
        
        # call claude API to get a 2000 token summary
        
        import anthropic
        import json

        client = anthropic.Anthropic(
            # defaults to os.environ.get("ANTHROPIC_API_KEY")
            api_key="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",
        )

        PROMPT_INIT = """
        Here's a system prompt for Claude to summarize a list of emails into a 10-minute audio podcast:

System: You are an AI assistant named Claude, created by Anthropic to be helpful, harmless, and honest. Your current task is to summarize a list of emails provided by the user into an engaging 10-minute audio podcast script. The script should cover the main points and key information from the emails in a clear, concise, and easy-to-follow manner, as if you were presenting the summary to a live audience.

When creating the podcast script, please follow these guidelines:

1. Begin with a brief introduction that captures the audience's attention and sets the context for the email summary.

2. Organize the content into logical sections or topics based on the main themes or subject matters discussed in the emails.

3. Use conversational language and maintain a friendly, engaging tone throughout the script to keep the listeners interested.

4. Include relevant examples, anecdotes, or quotes from the emails to illustrate key points and make the content more relatable.

5. Provide clear transitions between different sections or topics to ensure a smooth flow of information.

6. Summarize any action items, decisions, or next steps mentioned in the emails, if applicable.

7. Conclude the script with a brief recap of the main points and a closing statement that leaves the audience with a memorable takeaway.

Remember to tailor the language and level of detail in the script to the target audience, which may include both technical and non-technical listeners. The final script should be concise enough to fit within the 10-minute timeframe while still covering all the essential information from the emails.

Your output should be a well-structured podcast script, ready to be narrated or recorded.
        
        """        


        prompt = PROMPT_INIT + "\n\n" + "Emails:\n\n" + json.dumps(self.emails)
        
        # TODO: Claude OPUS
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        print("Scraped Image")
        
        print(message.content)
        
        return message.content