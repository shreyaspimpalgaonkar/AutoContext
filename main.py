import json
import os
from datetime import datetime, timedelta

import anthropic
import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

load_dotenv()  # This loads the environment variables from .env.

client_id = os.environ.get("SLACK_CLIENT_ID")
client_secret = os.environ.get("SLACK_CLIENT_SECRET")
redirect_uri = os.environ.get("SLACK_REDIRECT_URI")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

access_token = None

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class RAG_Pipeline:
    def __init__(self):
        import os

        from r2r.client import R2RClient

        os.environ["OPENAI_API_KEY"] = (
            "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"
        )
        os.environ["QDRANT_HOST"] = (
            "https://99d0bcc3-42b3-43ff-ad05-8d8ced544803.us-east4-0.gcp.cloud.qdrant.io"
        )
        os.environ["QDRANT_PORT"] = "6333"
        os.environ["QDRANT_API_KEY"] = (
            "nyA91hNvud9ZSIUYqeZdIP3kk4Tqv79qr_StSKrz_C5yuGyz3Mj6sw"
        )
        os.environ["OPEN_API_KEY"] = (
            "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"
        )
        os.environ["OPENAI_API_KEY"] = (
            "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"
        )
        os.environ["LOCAL_DB_PATH"] = "local_db"

        self.client = R2RClient(
            "https://sciphi-cc1d7a62-67a3-41f7-8cd5-a42862fdf25f-qwpin2swwa-ue.a.run.app"
        )

    def add_entry(self, url, text):
        """
        Add a new entry to the database.
        """

        import uuid

        print("Adding entry")

        # chunk into 2048 char
        chunks = [text[i : i + 2048] for i in range(0, len(text), 2048)]

        entries = []
        for i, txt in enumerate(chunks):
            entries.append(
                {
                    "document_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"doc {i}")),
                    "blobs": {"txt": txt},
                    "metadata": {"url": url},
                }
            )
        # entries = [
        #     {
        #         "document_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "doc 2")),
        #         "blobs": {"txt": "Second test entry"},
        #         "metadata": {"url": url},
        #     },
        #     {
        #         "document_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "doc 3")),
        #         "blobs": {"txt": "Third test entry"},
        #         "metadata": {"tags": url='url'},
        #     },
        # ]
        bulk_upsert_response = self.client.add_entries(entries, do_upsert=True)

        # try:
        #     user_id_0 = str(uuid.uuid5(uuid.NAMESPACE_DNS, "user_0"))
        #     document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, url))
        #     metadata = {"user_id": user_id_0, "chunk_prefix": ''}
        #     settings: dict = {}
        #     upload_response = self.client.add_entry(
        #         document_id, {'txt': text},
        #         do_upsert = True,
        #     )
        #     print(upload_response)
        # except Exception as e:
        #     print(e)
        #     return {"error": str(e)}

        # return upload_response

    def get_entry(self, txt):
        return self.client.search(txt, 5)


rag_pipeline = RAG_Pipeline()


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/auth/slack")
async def auth_slack():
    # Redirect the user to Slack's authorization page
    slack_auth_url = f"https://slack.com/oauth/v2/authorize?client_id={client_id}&user_scope=channels:history,channels:read,users:read&redirect_uri={redirect_uri}"
    return RedirectResponse(url=slack_auth_url)


@app.get("/auth/slack/callback")
async def auth_slack_callback(request: Request):
    # Handle the callback from Slack, including error handling and exchanging the code for an access token
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=400, detail="Slack OAuth callback didn't return a code."
        )
    # Exchange the code for a token
    # Make sure to handle errors and securely store the access token for the user
    # post to https://slack.com/api/oauth.v2.access, passing in code as a query param

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    # Make the asynchronous POST request to exchange the code for a token
    async with httpx.AsyncClient() as client:
        response = await client.post("https://slack.com/api/oauth.v2.access", data=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response JSON
        auth_response = response.json()

        if auth_response.get("ok"):
            global access_token
            # Successfully obtained access token, handle it according to your application's logic
            # Example: return {"access_token": auth_response["access_token"]}
            # return auth_response
            access_token = auth_response["authed_user"]["access_token"]
            print("access token: ", access_token)
            return RedirectResponse(url="/")
        else:
            # Handle error from Slack
            raise HTTPException(
                status_code=400, detail=f"Slack API error: {auth_response.get('error')}"
            )
    else:
        # HTTP request failed
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to exchange code for access token.",
        )


async def get_recent_messages():
    global access_token

    # Assuming `token` is the access token you obtained through OAuth
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/conversations.list", headers=headers
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch channels from Slack",
        )

    if not response.json().get("ok"):
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch channels from Slack, error: {response.json().get('error')}",
        )

    messages = []
    users = {}

    for channel in response.json().get("channels", []):
        if channel["is_member"] is not True:
            continue
        channel_id = channel["id"]
        channel_name = channel["name"]

        data = {
            "channel": channel_id,
            "limit": 999,
            "oldest": (datetime.now() - timedelta(days=1)).timestamp(),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/conversations.history",
                data=data,
                headers=headers,
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch messages from Slack",
            )

        if not response.json().get("ok"):
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch messages from Slack, error: {response.json().get('error')}",
            )

        for message in response.json().get("messages", []):
            if message["user"] not in users:
                async with httpx.AsyncClient() as client:
                    user_response = await client.get(
                        f"https://slack.com/api/users.info?user={message['user']}",
                        headers=headers,
                    )

                if user_response.status_code != 200:
                    raise HTTPException(
                        status_code=user_response.status_code,
                        detail="Failed to fetch user info from Slack",
                    )
                if not user_response.json().get("ok"):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch user info from Slack, error: {user_response.json().get('error')}",
                    )
                users[message["user"]] = user_response.json().get("user", {})[
                    "profile"
                ]["real_name"]
            messages.append(
                {
                    "channel": channel_name,
                    "user": users[message["user"]],
                    "text": message.get("text", ""),
                }
            )
    return messages


@app.get("/messages")
async def get_messages(request: Request):
    return json.dumps(await get_recent_messages())


@app.get("/summarize")
async def summarize(request: Request):
    message = anthropic_client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        temperature=0.0,
        system="The user will provide a Slack transcript in the form of a list of messages with three attributes each: the channel name, the sender name, and the message text. Summarize the messages for the user, capturing the most important content, in no more than a few paragraphs.",
        messages=[
            {"role": "user", "content": json.dumps(await get_recent_messages())},
        ],
    )

    return {"summary": message.content}


@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <html>
        <head>
            <title>Slack Integration</title>
        </head>
        <body>
            <button id="connect-slack">Connect to Slack</button>
            <button id="summarize-slack">Summarize Yesterday's Messages</button>
            <script src="/static/main.js"></script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/add_entry")
async def get_embedding(request: Request):
    print("inside add_entry")
    # url = request.query_params['url']
    # convert % to space
    # text = request.query_params['text']
    req = await request.json()
    result = rag_pipeline.add_entry(req["text"], req["url"])
    return result


@app.post("/get_entry")
async def get_embedding(request: Request):
    # text = request.query_params['text']
    # result = rag_pipeline.client.search(text, 1)
    req = await request.json()

    search_response = rag_pipeline.client.search(
        req["text"],
        5,
        # filters={"user_id": self.user_id},
    )
    all_txt = []
    for i, response in enumerate(search_response):
        text = response["metadata"]["text"]
        # title, body = text.split("\n", 1)
        # print(f"Result {i + 1}: {title}")
        # print(body[:500])
        # print("\n")
        all_txt.append(text)

    return "".join(all_txt)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        port=8000,
        reload=True,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
    )
    # create a DB locally
