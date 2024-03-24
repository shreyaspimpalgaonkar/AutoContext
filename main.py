import json
import os
from datetime import datetime, timedelta

import anthropic
import httpx
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Your Slack app's credentials (don't check these in in a real app)
client_id = "6313369380099.6850939569699"
client_secret = "ebb3c76d1df0c4d918130f564d4a6b1a"
# Your registered redirect URI
redirect_uri = "https://localhost:8000/auth/slack/callback"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")  # never check this in!

access_token = None

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


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
    code = request.query_params.get('code')
    if not code:
        raise HTTPException(status_code=400, detail="Slack OAuth callback didn't return a code.")
    # Exchange the code for a token
    # Make sure to handle errors and securely store the access token for the user
    # post to https://slack.com/api/oauth.v2.access, passing in code as a query param

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
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
            access_token = auth_response['authed_user']["access_token"]
            print("access token: ", access_token)
            return RedirectResponse(url="/")
        else:
            # Handle error from Slack
            raise HTTPException(status_code=400, detail=f"Slack API error: {auth_response.get('error')}")
    else:
        # HTTP request failed
        raise HTTPException(status_code=response.status_code, detail="Failed to exchange code for access token.")


async def get_recent_messages():
    global access_token

    # Assuming `token` is the access token you obtained through OAuth
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get("https://slack.com/api/conversations.list", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch channels from Slack")

    if not response.json().get("ok"):
        raise HTTPException(status_code=400,
                            detail=f"Failed to fetch channels from Slack, error: {response.json().get('error')}")

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
            response = await client.post("https://slack.com/api/conversations.history", data=data, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch messages from Slack")

        if not response.json().get("ok"):
            raise HTTPException(status_code=400,
                                detail=f"Failed to fetch messages from Slack, error: {response.json().get('error')}")

        for message in response.json().get("messages", []):
            if message['user'] not in users:
                async with httpx.AsyncClient() as client:
                    user_response = await client.get(f"https://slack.com/api/users.info?user={message['user']}",
                                                     headers=headers)

                if user_response.status_code != 200:
                    raise HTTPException(status_code=user_response.status_code,
                                        detail="Failed to fetch user info from Slack")
                if not user_response.json().get("ok"):
                    raise HTTPException(status_code=400,
                                        detail=f"Failed to fetch user info from Slack, error: {user_response.json().get('error')}")
                users[message['user']] = user_response.json().get("user", {})['profile']['real_name']
            messages.append({
                "channel": channel_name,
                "user": users[message['user']],
                "text": message.get("text", ""),
            })
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
        ]
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


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
