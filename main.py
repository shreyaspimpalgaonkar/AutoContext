from datetime import datetime, timedelta

import httpx
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI()

# Your Slack app's credentials (don't check these in in a real app)
client_id = "6313369380099.6850939569699"
client_secret = "ebb3c76d1df0c4d918130f564d4a6b1a"
# Your registered redirect URI
redirect_uri = "https://localhost:8000/auth/slack/callback"

access_token = None


@app.get("/")
async def root():
    return {"message": "Hello World"}


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
            return RedirectResponse(url="/")
        else:
            # Handle error from Slack
            raise HTTPException(status_code=400, detail=f"Slack API error: {auth_response.get('error')}")
    else:
        # HTTP request failed
        raise HTTPException(status_code=response.status_code, detail="Failed to exchange code for access token.")


@app.get("/summarize")
async def summarize(request: Request):
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


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
