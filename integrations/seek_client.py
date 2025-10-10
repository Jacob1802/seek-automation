from integrations.mail_handler import MailClient
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

AUTH0_CLIENT = 'eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4yOC4wIn0='
CLIENTID = "yGBVge66K5NJpSN5u71fU90VcTlEASNu"
SEEK_LOGIN_SENDER = "noreply@seek.com.au"

class SeekClient:
    def __init__(self, mail_client: MailClient):
        self.mail_client = mail_client


    def login(self):
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            'auth0-client': AUTH0_CLIENT,
            'content-type': 'application/json',
            'origin': 'https://login.seek.com',
            'priority': 'u=1, i',
            'referer': 'https://login.seek.com/',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Brave";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'x-request-language': 'en-au',
        }

        user_email = os.getenv("EMAIL_ADDRESS")
        with requests.Session(impersonate="chrome", headers=headers, allow_redirects=True) as session:
            json_data = {
                'client_id': CLIENTID,
                'connection': 'email',
                'send': 'link',
                'email': user_email,
                'authParams': {
                    'response_type': 'code',
                    'redirect_uri': 'https://www.seek.com.au/oauth/callback/',
                    'scope': 'openid profile email offline_access',
                    'audience': 'https://seek/api/candidate',
                },
            }

            response = session.post('https://login.seek.com/passwordless/start', json=json_data)
            code = self.mail_client.fetch_code(SEEK_LOGIN_SENDER)
            json_data = {
                'connection': 'email',
                'verification_code': code,
                'email': user_email,
                'client_id': CLIENTID,
            }

            response = session.post('https://login.seek.com/passwordless/verify', json=json_data)
            params = {
                'client_id': CLIENTID,
                'response_type': 'code',
                'redirect_uri': 'https://www.seek.com.au/oauth/callback/',
                'scope': 'openid profile email offline_access',
                'audience': 'https://seek/api/candidate',
                '_intstate': 'deprecated',
                'protocol': 'oauth2',
                'connection': 'email',
                'verification_code': code,
                'email': user_email,
                'auth0Client': AUTH0_CLIENT,
            }
            
            response = session.get('https://login.seek.com/passwordless/verify_redirect', params=params, headers=headers)
            auth_code = self._parse_auth_code(response.url)

            if not auth_code:
                logging.error("Authorization code not found, cannot proceed")
                return
            
            json_data = {
                'client_id': CLIENTID,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': 'https://www.seek.com.au/oauth/callback/',
            }

            response = session.post('https://login.seek.com/oauth/token', json=json_data)
            data = response.json()
            logging.info(data)
            bearer = data['access_token']

            # TODO: save tokens

    def _parse_auth_code(self, url):
        if "code=" in url:            
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            auth_code = params.get('code', [None])[0]
            return auth_code
        return
