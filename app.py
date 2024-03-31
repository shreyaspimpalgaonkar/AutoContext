import os
import uuid

from modal import asgi_app, Mount
from common import stub
from pathlib import Path

from rag_pipeline import RAG_Pipeline   

# from slack_integration import router as slack_router

static_path = Path('./env').resolve()

@stub.function(
    mounts=[Mount.from_local_dir('.', remote_path="/app")],
    container_idle_timeout=300,
    timeout=600,
)
@asgi_app()
def web():
    from fastapi import FastAPI, Request
    from fastapi.responses import Response, StreamingResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI()
    rag_pipeline = RAG_Pipeline()

    # app.include_router(slack_router)

    @app.get("/hello/{name}")
    async def say_hello(name: str):
        return {"message": f"Hello {name}"}


    @app.post("/add_entry")
    async def add_embedding(request: Request):
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

    app.mount("/", StaticFiles(directory="/env", html=True))
