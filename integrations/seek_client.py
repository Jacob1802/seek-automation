from integrations.mail_handler import MailClient
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests
from dotenv import load_dotenv
import logging
import time
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


class SeekClient:
    AUTH0_CLIENT = 'eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4yOC4wIn0='
    CLIENT_ID = "yGBVge66K5NJpSN5u71fU90VcTlEASNu"
    SEEK_LOGIN_SENDER = "noreply@seek.com.au"
    USER_EMAIL = os.getenv("EMAIL_ADDRESS")

    def __init__(self, mail_client: MailClient):
        self.mail_client = mail_client
    
    def __enter__(self):
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            'auth0-client': self.AUTH0_CLIENT,
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

        self.session = requests.Session(impersonate="chrome", headers=headers, allow_redirects=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def login(self):
        json_data = {
            'client_id': self.CLIENT_ID,
            'connection': 'email',
            'send': 'link',
            'email': self.USER_EMAIL,
            'authParams': {
                'response_type': 'code',
                'redirect_uri': 'https://www.seek.com.au/oauth/callback/',
                'scope': 'openid profile email offline_access',
                'audience': 'https://seek/api/candidate',
            },
        }
        response = self.session.post('https://login.seek.com/passwordless/start', json=json_data)
        logging.info("Waiting 10 seconds for login code email to arrive")
        time.sleep(10)

        code = self.mail_client.fetch_code(self.SEEK_LOGIN_SENDER)
        json_data = {
            'connection': 'email',
            'verification_code': code,
            'email': self.USER_EMAIL,
            'client_id': self.CLIENT_ID,
        }

        response = self.session.post('https://login.seek.com/passwordless/verify', json=json_data)
        params = {
            'client_id': self.CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': 'https://www.seek.com.au/oauth/callback/',
            'scope': 'openid profile email offline_access',
            'audience': 'https://seek/api/candidate',
            '_intstate': 'deprecated',
            'protocol': 'oauth2',
            'connection': 'email',
            'verification_code': code,
            'email': self.USER_EMAIL,
            'auth0Client': self.AUTH0_CLIENT,
        }
        
        response = self.session.get('https://login.seek.com/passwordless/verify_redirect', params=params)
        auth_code = self._parse_auth_code(response.url)

        if not auth_code:
            logging.error("Authorization code not found, cannot proceed")
            return
        
        json_data = {
            'client_id': self.CLIENT_ID,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'https://www.seek.com.au/oauth/callback/',
        }

        response = self.session.post('https://login.seek.com/oauth/token', json=json_data)
        data = response.json()
        # logging.info(data)
        bearer = data['access_token']
        # TODO: save tokens

    # def login_with_refresh_token(self):
    #     refresh_token = ""
        
    #     json_data = {
    #         'client_id': self.CLIENT_ID,
    #         'refresh_token': refresh_token,
    #         # 'identity_sdk_version': "9.4.0",
    #         'grant_type': 'refresh_token',
    #         # 'redirect_uri': 'https://www.seek.com.au/oauth/callback/',
    #     }

    #     response = self.session.post('https://login.seek.com/oauth/token', json=json_data)
    #     data = response.json()

    def _parse_auth_code(self, url):
        if "code=" in url:            
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            auth_code = params.get('code', [None])[0]
            return auth_code
        return


if __name__ == "__main__":
    mail_client = MailClient("gmail.com")
    with SeekClient(mail_client) as seek_client:
        seek_client.login()