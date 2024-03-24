import os.path

import datetime
import base64
from modal import Image, method

import io
import tempfile

from modal import Image, method, enter, Dict

from .common import stub

import logging
from typing import Optional

logger = logging.getLogger(__name__)



DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
DEFAULT_TASK_PROMPT = """
## Task:
Answer the query given immediately below given the context which follows later. Use line item references to like [1], [2], ... refer to specifically numbered items in the provided context. Pay close attention to the title of each given source to ensure it is consistent with the query.

### Query:
{query}

### Context:
{context}

### Query:
{query}

REMINDER - Use line item references to like [1], [2], ... refer to specifically numbered items in the provided context.
## Response:
"""


embedding_image = (
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
        'r2r[parsing,eval]',
        'qdrant-client',
        extra_index_url="https://download.pytorch.org/whl/cu117",
    )
    .pip_install("git+https://github.com/metavoicexyz/tortoise-tts")
    .run_commands(
        'export QDRANT_HOST=https://99d0bcc3-42b3-43ff-ad05-8d8ced544803.us-east4-0.gcp.cloud.qdrant.io',
        'export QDRANT_PORT=6333',
        'export QDRANT_API_KEY=nyA91hNvud9ZSIUYqeZdIP3kk4Tqv79qr_StSKrz_C5yuGyz3Mj6sw',
        'export OPEN_API_KEY=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',
        'export OPENAI_API_KEY=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',
    )
    # .run_function(download_models)
)

@stub.cls(
    image=embedding_image,
    container_idle_timeout=300,
    timeout=180,
)  
class RAG_Pipeline:
    
    @enter()
    def enter_func(self):
        
        import json 
        # cfg = {
        #     "vector_database": {
        #     "provider": "qdrant",
        #     "collection_name": "demo-v1-test"
        #     },
        #     "evals": {
        #     "provider": "deepeval",
        #     "frequency": 0.25
        #     },
        #     "embedding": {
        #     "provider": "openai",
        #     "model": "text-embedding-3-small",
        #     "dimension": 1536,
        #     "batch_size": 32
        #     },
        #     "text_splitter": {
        #     "chunk_size": 512,
        #     "chunk_overlap": 20
        #     },
        #     "language_model": {
        #     "provider": "litellm",
        #     "model": "gpt-4-0125-preview",
        #     "temperature": 0.1,
        #     "top_p": 0.9,
        #     "top_k": 128,
        #     "max_tokens_to_sample": 1024,
        #     "do_stream": False
        #     },
        #     "logging_database": {
        #     "provider": "local",
        #     "level": "INFO",
        #     "name": "r2r",
        #     "database": "demo_logs_v1"
        #     }
        # }
        cfg = {
            "embedding": {
                "provider": "openai",
                "model": "text-embedding-3-small",
                "dimension": 768,
                "batch_size": 32
            },
            "evals": {
                "provider": "deepeval",
                "frequency": 1.0
            },
            "language_model": {
                "provider": "litellm"
            },
            "logging_database": {
                "provider": "local",
                "collection_name": "demo_logs",
                "level": "INFO"
            },
            "ingestion":{
                "provider": "local",
                "text_splitter": {
                "type": "recursive_character",
                "chunk_size": 512,
                "chunk_overlap": 20
                }
            },
            "vector_database": {
                "provider": "qdrant",
                "collection_name": "coll"
            },
            "app": {
                "max_logs": 100,
                "max_file_size_in_mb": 100
            }
            }
                    
        with open('config.json', 'w') as f:
            json.dump(cfg, f)        

        from r2r.pipelines import BasicIngestionPipeline, BasicEmbeddingPipeline, BasicRAGPipeline
        from r2r.main.factory import E2EPipelineFactory
        
        
        import os
        os.environ['OPENAI_API_KEY'] = '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'
        os.environ['QDRANT_HOST'] = 'https://99d0bcc3-42b3-43ff-ad05-8d8ced544803.us-east4-0.gcp.cloud.qdrant.io'
        os.environ['QDRANT_PORT'] = '6333'
        os.environ['QDRANT_API_KEY'] = 'nyA91hNvud9ZSIUYqeZdIP3kk4Tqv79qr_StSKrz_C5yuGyz3Mj6sw'
        os.environ['OPEN_API_KEY'] = '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'
        os.environ['OPENAI_API_KEY'] = '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'
        os.environ['LOCAL_DB_PATH'] = 'local_db'
        
        # self.app = E2EPipelineFactory.create_pipeline(
        #     # override with your own custom ingestion pipeline
        #     ingestion_pipeline_impl=BasicIngestionPipeline,
        #     # override with your own custom embedding pipeline
        #     embedding_pipeline_impl=BasicEmbeddingPipeline,
        #     # override with your own custom RAG pipeline
        #     rag_pipeline_impl=BasicRAGPipeline,
        #     # override with your own config.json
        #     config_path='config.json',
        # )

        # print(self.app)

        # from r2r.client import R2RClient
        
        base_url = "https://99d0bcc3-42b3-43ff-ad05-8d8ced544803.us-east4-0.gcp.cloud.qdrant.io"  # Replace with your actual deployed API URL
        self.client = R2RClient(base_url)
        
        self.my_dict = Dict.ephemeral("my_persisted_dict")

    @method()
    def add_entry(self, entry):
        """
        Add a new entry to the database.
        """
        
        import uuid
        import json
        print('Adding entry')
        
        print(entry)
        
        entry = entry.decode('utf-8').replace("'", '"')
        
        print(entry)

        json_body = json.loads(entry)
        print(json_body)
        
        file_path = json_body['url']

        
        user_id_0 = str(uuid.uuid5(uuid.NAMESPACE_DNS, "user_0"))
        
        document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_path))
        metadata = {"user_id": user_id_0, "chunk_prefix": ''}
        settings: dict = {}
        upload_response = self.client.add_entry(
            document_id, {'txt': json_body['body']}, metadata, settings
        )

        print(upload_response)
        
        ret = self.client.add_entry(str(uuid.uuid5(uuid.NAMESPACE_DNS, json_body['url'])),  # document_id
            {"txt": json_body['body']},
            {"tags": ["example", "test"]},
            do_upsert=True,)
        
        print(ret)

        return self.my_dict