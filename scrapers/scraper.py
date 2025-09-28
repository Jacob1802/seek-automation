
from apify_client import ApifyClientAsync
from dotenv import load_dotenv
import logging
import asyncio
import os
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class JobScraper:
    def __init__(self, run_config):
        self.run_config = run_config
        self.client = ApifyClientAsync(os.getenv("APIFY_KEY"))
        
    async def scrape(self, actor):
        try:
            all_data = []
            tasks = []
            for query in self.run_config['searchTerms']:
                config = {k: v for k, v in self.run_config.items() if k != 'searchTerms'}
                config['searchTerm'] = query
                tasks.append(self.client.actor(actor).call(run_input=config))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for response in responses:
                if isinstance(response, Exception):
                    continue
                all_data.extend(await self._get_dataset(response))

            return all_data
        except Exception as e:
            logging.error(e)
            return []

    async def _get_dataset(self, run):
        data = await self.client.dataset(run["defaultDatasetId"]).list_items()
        return data.items