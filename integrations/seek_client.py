from integrations.mail_handler import MailClient
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests, CurlMime
from dotenv import load_dotenv
import logging
import uuid
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
        try:
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
            response.raise_for_status()
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
            response.raise_for_status()
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
            response.raise_for_status()
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
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get('access_token')
            self.refresh_token = data.get('refresh_token')
            self.token_expiry = time.time() + data.get('expires_in', 0)
            self.session.headers.update({'authorization': f'Bearer {self.access_token}'})

        except Exception as e:
            logging.error(f"Error during login: {e}")
    
    def _renew_token(self):
        json_data = {
            'client_id': self.CLIENT_ID,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
        }

        response = self.session.post('https://login.seek.com/oauth/token', json=json_data)
        data = response.json()
        self.access_token = data.get('access_token')
        self.refresh_token = data.get('refresh_token')
        self.token_expiry = time.time() + data.get('expires_in', 0)

    def _parse_auth_code(self, url):
        if "code=" in url:            
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            auth_code = params.get('code', [None])[0]
            return auth_code
        return

    def apply(self, job_id, resume_path, cover_letter_path):
        try:
            resume_uri = self._upload_attachment('Resume', resume_path)
            cover_letter_uri = self._upload_attachment('CoverLetter', cover_letter_path)
            json_data = [
                {
                    'operationName': 'ApplySubmitApplication',
                    'variables': {
                        'input': {
                            'jobId': job_id,
                            'correlationId': str(uuid.uuid4()),
                            'zone': 'anz-1',
                            'profilePrivacyLevel': 'Standard',
                            'resume': {
                                'uri': resume_uri,
                            },
                            'coverLetter': {
                                'uri': cover_letter_uri,
                            },
                            'mostRecentRole': {
                            },
                        },
                        'locale': 'en-AU',
                    },
                    'query': 'mutation ApplySubmitApplication($input: SubmitApplicationInput!, $locale: Locale) {\n  submitApplication(input: $input) {\n    ... on SubmitApplicationSuccess {\n      applicationId\n      __typename\n    }\n    ... on SubmitApplicationFailure {\n      errors {\n        message(locale: $locale)\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}',
                },
            ]

            response = self.session.post('https://www.seek.com.au/graphql', json=json_data)
            response.raise_for_status()
            logging.info(f"successfully applied to job {job_id}")
        except Exception as e:
            logging.error(f"Error during job application: {e}")

    def _upload_attachment(self, type, file_path):
        try:
            mp = CurlMime()
            json_data = [
                {
                    'operationName': 'GetDocumentUploadData',
                    'variables': {
                        'id': str(uuid.uuid4()),
                    },
                    'query': 'query GetDocumentUploadData($id: UUID!) {\n  viewer {\n    documentUploadFormData(id: $id) {\n      link\n      key\n      formFields {\n        key\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}',
                },
            ]

            response = self.session.post('https://www.seek.com.au/graphql', json=json_data)
            response.raise_for_status()
            response_data = response.json()
            link = response_data[0]['data']['viewer']['documentUploadFormData']['link']
            uuid_key = response_data[0]['data']['viewer']['documentUploadFormData']['key']
            for item in response_data[0]['data']['viewer']['documentUploadFormData']['formFields']:
                mp.addpart(name=item['key'], data=item['value'])
                    
            mp.addpart(
                name="file",
                content_type="application/pdf",
                filename=file_path,
                local_path=file_path,
            )

            response = self.session.post(
                link,
                multipart=mp,
                impersonate="chrome",
            )
            response.raise_for_status()
            time.sleep(5) # Wait for S3 to process the upload
            if type == "CoverLetter":
                json_data = self._process_cover_letter(uuid_key)
            elif type == "Resume":
                json_data = self._process_resume(uuid_key)
            else:
                raise ValueError("Invalid attachment type")
            
            response = self.session.post('https://www.seek.com.au/graphql', json=json_data)
            response.raise_for_status()
            data = response.json()
            uri = data[0]['data']['processUploadedAttachment']['uri']
            return uri
        except Exception as e:
            logging.error(f"Error during attachment upload: {e}")
        finally:
            mp.close()

    def _process_resume(self, uuid_key):
        json_data = [
            {
                'operationName': 'ApplyProcessUploadedResume',
                'variables': {
                    'input': {
                        'id': uuid_key,
                        'isDefault': False,
                        'parsingContext': {
                            'id': str(uuid.uuid4()),
                        },
                        'zone': 'anz-1',
                    },
                },
                'query': 'mutation ApplyProcessUploadedResume($input: ProcessUploadedResumeInput!) {\n  processUploadedResume(input: $input) {\n    resume {\n      ...resume\n      __typename\n    }\n    viewer {\n      _id\n      resumes {\n        ...resume\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment resume on Resume {\n  id\n  createdDateUtc\n  isDefault\n  fileMetadata {\n    name\n    size\n    virusScanStatus\n    sensitiveDataInfo {\n      isDetected\n      __typename\n    }\n    uri\n    __typename\n  }\n  origin {\n    type\n    __typename\n  }\n  __typename\n}',
            },
        ]
        return json_data

    def _process_cover_letter(self, uuid_key):
        json_data = [
            {
                'operationName': 'ApplyProcessUploadedAttachment',
                'variables': {
                    'input': {
                        'id': uuid_key,
                        'attachmentType': "CoverLetter",
                    },
                },
                'query': 'mutation ApplyProcessUploadedAttachment($input: ProcessUploadedAttachmentInput!) {\n  processUploadedAttachment(input: $input) {\n    uri\n    __typename\n  }\n}',
            },
        ]
        return json_data

if __name__ == "__main__":
    mail_client = MailClient("gmail.com")
    with SeekClient(mail_client) as seek_client:
        seek_client.login()