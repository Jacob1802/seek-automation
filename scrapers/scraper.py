
from apify_client import ApifyClient
from dotenv import load_dotenv
from typing import Dict, List
import os
load_dotenv()

class JobScraper:
    def __init__(self, run_config: Dict):
        self.run_config = run_config
        self.client = ApifyClient(os.getenv("APIFY_KEY"))
        
    def scrape(self, actor: str) -> List[Dict]:
        run = self.client.actor(actor).call(run_input=self.run_config)
        return self.get_dataset(run)
    
    def get_dataset(self, run: Dict) -> List[Dict]:
        data = self.client.dataset(run["defaultDatasetId"]).list_items().items
        return data