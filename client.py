# ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
# anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

import os
import uuid
from bs4 import BeautifulSoup
import requests

class AutoContextRAGClient:
    def __init__(self):
        self.base_url = os.environ["R2R_ENDPOINT"]

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

    def add_entry(self, entry):
        """
        Add a new entry to the database.
        """
        metadata = {
            "url": entry["content"]["url"],
            "title": entry["content"]["title"],
            "time": entry["content"]["time"],
            "domain": entry["domain"],
            "user_uuid": entry["user_uuid"]
        }
        
        document_id =  str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{metadata['url']}"))
        url = f"{self.base_url}/add_entry/"
        json_data = {
            "entry": {
                "document_id": document_id,
                "blobs": { 'html' : entry['content']['text']},
                "metadata": metadata or {},
            },
            "settings": {"embedding_settings": {"do_upsert": True}},
        }
        response = requests.post(url, json=json_data)
        print(response.json())
        return response.json()

    def get_entry(self, entry):
        
        url = f"{self.base_url}/search/"
        
        query = entry['text']
        user_uuid = entry['user_uuid']
        
        filters = {'user_uuid': user_uuid}
        settings = None
        
        json_data = {
            "query": query,
            "filters": filters or {},
            "limit": 5,
            "settings": settings or {},
        }
        response = requests.post(url, json=json_data)
        print("hiohifahds")
        print(response.json())
        return response.json()