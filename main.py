import os
import uuid

import anthropic
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from modal import Image, Mount, Stub, asgi_app
from r2r.client import R2RClient

from slack_integration import router as slack_router

load_dotenv()  # This loads the environment variables from .env.

web_app = FastAPI()
web_app.mount("/static", StaticFiles(directory="static"), name="static")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

web_app.include_router(slack_router)


class RAG_Pipeline:
    def __init__(self):
        self.client = R2RClient(os.environ["R2R_ENDPOINT"])

    def add_entry(self, url, text):
        """
        Add a new entry to the database.
        """
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

        bulk_upsert_response = self.client.add_entries(entries, do_upsert=True)
        return bulk_upsert_response

    def get_entry(self, txt):
        return self.client.search(txt, 5)


rag_pipeline = RAG_Pipeline()


@web_app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@web_app.post("/add_entry")
async def add_embedding(request: Request):
    print("inside add_entry")
    # url = request.query_params['url']
    # convert % to space
    # text = request.query_params['text']
    req = await request.json()
    result = rag_pipeline.add_entry(req["text"], req["url"])
    return result


@web_app.post("/get_entry")
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


stub = Stub()
image = Image.from_registry("python:3.11")
image = image.pip_install_from_requirements("requirements.txt")


@stub.function(
    image=image,
    mounts=[
        Mount.from_local_dir("./static", remote_path="/root/static"),
        Mount.from_local_file(".env", "/root/.env"),
    ],
)
@asgi_app()
def fastapi_app():
    return web_app
