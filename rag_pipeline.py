
from modal import Image, build, enter, method
from common import stub

rag_pipeline_image = Image.from_dockerfile("Dockerfile")

with rag_pipeline_image.imports():
    import os
    import uuid
    from r2r.client import R2RClient
    from dotenv import load_dotenv

@stub.cls(image=rag_pipeline_image, container_idle_timeout=300)
class RAG_Pipeline:
    
    @enter()
    def enter_func(self):        
        load_dotenv('assets/.env')
        self.client = R2RClient(os.environ["R2R_ENDPOINT"])
        

    @method()
    async def add_entry(self, url, text):
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
