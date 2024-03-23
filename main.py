from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn
import httpx

app = FastAPI()

# Your Slack app's credentials (don't check these in in a real app)
client_id = "6313369380099.6850939569699"
client_secret = "ebb3c76d1df0c4d918130f564d4a6b1a"
# Your registered redirect URI
redirect_uri = "https://localhost:8000/auth/slack/callback"

# The URL for the Slack OAuth access endpoint
access_token_url = "https://slack.com/api/oauth.v2.access"

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
    slack_auth_url = f"https://slack.com/oauth/v2/authorize?client_id={client_id}&user_scope=channels:history&redirect_uri={redirect_uri}"
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
        response = await client.post(access_token_url, data=data)

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


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
