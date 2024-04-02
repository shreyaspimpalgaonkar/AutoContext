# ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
# anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

import os
import uuid
from r2r.client import R2RClient
from modal import Image
from bs4 import BeautifulSoup


class AutoContextRAGClient:
    def __init__(self):
        self.client = R2RClient(os.environ["R2R_ENDPOINT"])

    def clean_text(self, text):

        def clean_string(input_string):
            import re
            cleaned_string = re.sub(r'\s+', ' ', input_string).strip()
            unicode_pattern = re.compile('[^\x00-\x7F]+')
            cleaned_string = unicode_pattern.sub('', cleaned_string)
            return cleaned_string

        soup = BeautifulSoup(text, 'html.parser')

        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()

        return text

    def add_entry(self, url, text):
        """
        Add a new entry to the database.
        """

        text = self.clean_text(text)

        entry = {
            "document_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{url}")),
            "blobs": {"txt": text},
            "metadata": {"url": url},
        }

        bulk_upsert_response = self.client.add_entry(entry, do_upsert=True)
        return bulk_upsert_response

    def get_entry(self, txt):
        return self.client.search(txt, 5)