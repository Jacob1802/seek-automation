from common.utils import load_json_file, write_json_file
from integrations.mail_handler import MailClient
from requests_toolbelt import MultipartEncoder
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests
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
    REFRESH_TOKEN_PATH = "credentials/seek_refresh_token.json"

    def __init__(self, mail_client: MailClient):
        self.mail_client = mail_client
        self.is_logged_in = False
    
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
        self.refresh_token = load_json_file(self.REFRESH_TOKEN_PATH).get("refresh_token")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.session:
            self.session.close()
        if self.refresh_token:
            write_json_file(self.REFRESH_TOKEN_PATH, {"refresh_token": self.refresh_token})

    def login(self):
        try:
            if self.refresh_token:
                success = self._renew_token()
                if success:
                    self.is_logged_in = True
                    return success

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
            logging.info("Waiting 5 seconds for login code email to arrive")
            time.sleep(5)

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
            self.refresh_token = data.get('refresh_token')
            self.token_expiry = time.time() + data.get('expires_in', 0)
            self.session.headers.update({'authorization': f'Bearer {data.get('access_token')}'})
            self.is_logged_in = True
            logging.info("Successfully logged in to seek")
            return True

        except Exception as e:
            logging.error(f"Error during login: {e}")
            return False

    def _check_and_renew(self):
        if not self.is_logged_in:
            success = self.login()
            return success
        
        if self.token_expiry-300 > time.time():
            success = self._renew_token()
            return success

        return True

    def _renew_token(self):
        json_data = {
            'client_id': self.CLIENT_ID,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
        }
        try:
            response = self.session.post('https://login.seek.com/oauth/token', json=json_data)
            response.raise_for_status()
            data = response.json()

            if not data.get('access_token'):
                raise ValueError("No access_token in response")
            
            self.session.headers.update({'authorization': f'Bearer {data.get('access_token')}'})
            self.refresh_token = data.get('refresh_token')
            self.token_expiry = time.time() + data.get('expires_in', 0)
            return True
        except Exception as e:
            logging.error(f'Error refreshing token {e}')
            self.is_logged_in = False
            return False

    def _parse_auth_code(self, url):
        if "code=" in url:            
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            auth_code = params.get('code', [None])[0]
            return auth_code
        return

    def apply(self, job_id, resume_path, cover_letter_path, show_recent_role=True):
        try:
            if not self._check_and_renew():
                return False

            resume_uri = self._upload_attachment('Resume', resume_path)
            cover_letter_uri = self._upload_attachment('CoverLetter', cover_letter_path)
            if show_recent_role:
                recent_role = self.get_most_recent_role()
            else:
                recent_role = {}
            
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
                            'mostRecentRole': recent_role
                        },
                        'locale': 'en-AU',
                    },
                    'query': 'mutation ApplySubmitApplication($input: SubmitApplicationInput!, $locale: Locale) {\n  submitApplication(input: $input) {\n    ... on SubmitApplicationSuccess {\n      applicationId\n      __typename\n    }\n    ... on SubmitApplicationFailure {\n      errors {\n        message(locale: $locale)\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}',
                },
            ]

            response = self.session.post('https://www.seek.com.au/graphql', json=json_data)
            # logging.info(f"Application response: {response.text}")
            response.raise_for_status()
            data = response.json()
            assert data[0]['data']['submitApplication']['__typename'] == 'SubmitApplicationSuccess', f"Application failed: {data[0]['data']['submitApplication'].get('errors', [])}"
            logging.info(f"Successfully processed application via seek")
            return True
        except Exception as e:
            logging.error(f"Error during job application: {e}")
            return False

    def _upload_attachment(self, type, file_path):
        try:
            actual_filename = os.path.basename(file_path)
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
            document_form_data = response_data[0]['data']['viewer']['documentUploadFormData']
            link = document_form_data['link']
            uuid_key = document_form_data['key']
            
            fields = {item['key']: item['value'].replace('${filename}', actual_filename) if '${filename}' in item['value'] else item['value'] 
                    for item in document_form_data['formFields']}
            with open(file_path, 'rb') as f:
                fields['file'] = (actual_filename, f, 'application/pdf')
                mp = MultipartEncoder(fields=fields)

                response = requests.post(
                    link,
                    data=mp.to_string(),
                    headers={'Content-Type': mp.content_type}
                    
                )

            response.raise_for_status()
            time.sleep(5)
            
            if type == "CoverLetter":
                json_data = self._process_cover_letter(uuid_key)
            elif type == "Resume":
                json_data = self._process_resume(uuid_key)
            else:
                raise ValueError("Invalid attachment type")
            
            response = self.session.post('https://www.seek.com.au/graphql', json=json_data)
            response.raise_for_status()
            data = response.json()
            if type == "CoverLetter":
                uri = data[0]['data']['processUploadedAttachment']['uri']
            elif type == "Resume":
                uri = data[0]['data']['processUploadedResume']['resume']['fileMetadata']['uri']
            
            return uri
        except Exception as e:
            logging.error(f"Error during attachment upload: {e}")
            return None

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
    
    def handle_role_requirements(self, job_id):
        # Not yet implemented
        try:
            json_data = [
                {
                    'operationName': 'GetJobApplicationProcess',
                    'variables': {
                        'jobId': job_id,
                        'isAuthenticated': True,
                        'locale': 'en-AU',
                    },
                    'query': 'query GetJobApplicationProcess($jobId: ID!, $isAuthenticated: Boolean!, $locale: Locale!) {\n  jobApplicationProcess(jobId: $jobId) {\n    ...LocationFragment\n    ...ClassificationFragment\n    ...DocumentsFragment\n    ...QuestionnaireFragment\n    job {\n      ...JobFragment\n      __typename\n    }\n    linkOut\n    extractedRoleTitles\n    __typename\n  }\n}\n\nfragment LocationFragment on JobApplicationProcess {\n  location {\n    id\n    name\n    __typename\n  }\n  state {\n    id\n    __typename\n  }\n  area {\n    id\n    name\n    __typename\n  }\n  __typename\n}\n\nfragment ClassificationFragment on JobApplicationProcess {\n  classification {\n    id\n    name\n    subClassification {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment DocumentsFragment on JobApplicationProcess {\n  documents {\n    lastAppliedResumeIdPrefill @include(if: $isAuthenticated)\n    selectionCriteriaRequired\n    lastWrittenCoverLetter @include(if: $isAuthenticated) {\n      content\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment QuestionnaireFragment on JobApplicationProcess {\n  questionnaire {\n    questions @include(if: $isAuthenticated) {\n      id\n      text\n      __typename\n      ... on SingleChoiceQuestion {\n        lastAnswer {\n          id\n          text\n          uri\n          __typename\n        }\n        options {\n          id\n          text\n          uri\n          __typename\n        }\n        __typename\n      }\n      ... on MultipleChoiceQuestion {\n        lastAnswers {\n          id\n          text\n          uri\n          __typename\n        }\n        options {\n          id\n          text\n          uri\n          __typename\n        }\n        __typename\n      }\n      ... on PrivacyPolicyQuestion {\n        url\n        options {\n          id\n          text\n          uri\n          __typename\n        }\n        __typename\n      }\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment JobFragment on Job {\n  id\n  createdAt {\n    shortLabel\n    __typename\n  }\n  content\n  title\n  advertiser {\n    id\n    name(locale: $locale)\n    __typename\n  }\n  abstract\n  source\n  products {\n    branding {\n      id\n      logo {\n        url\n        __typename\n      }\n      __typename\n    }\n    displayTags {\n      label(locale: $locale)\n      __typename\n    }\n    __typename\n  }\n  tracking {\n    isPrivateAdvertiser\n    hasRoleRequirements\n    __typename\n  }\n  __typename\n}',
                },
            ]

            response = self.session.post('https://www.seek.com.au/graphql', json=json_data)
            # TODO: check response for errors as status always seems to be 200
            response.raise_for_status()
            data = response.json()
            questions = data[0]['data']['jobApplicationProcess']['questionnaire']['questions']
            options = {}
            for question in questions:
                options[f"{question['id']--question['text']}"] = [(option['id'], option['text']) for option in question.get('options', [])]
            

        except Exception as e:
            logging.error(f"Error during role requirements handling: {e}")

    def get_most_recent_role(self):
        try:
            json_data = [
                {
                    'operationName': 'GetRoles',
                    'variables': {},
                    'query': 'query GetRoles {\n  viewer {\n    _id\n    roles {\n      ...role\n      __typename\n    }\n    yearsOfExperience {\n      newToWorkforce\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment role on Role {\n  id\n  title {\n    text\n    ontologyId\n    __typename\n  }\n  company {\n    text\n    ontologyId\n    __typename\n  }\n  seniority {\n    text\n    ontologyId\n    __typename\n  }\n  from {\n    year\n    month\n    __typename\n  }\n  to {\n    year\n    month\n    __typename\n  }\n  achievements\n  tracking {\n    events {\n      key\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}',
                }
            ]

            response = self.session.post('https://www.seek.com.au/graphql', json=json_data)
            response.raise_for_status()
            # TODO: check response for errors as status always seems to be 200
            data = response.json()
            roles = data[0]['data']['viewer']['roles']
            if roles:
                most_recent_role = {
                    'company': roles[0]['company']['text'] if roles[0]['company'] else '',
                    'title': roles[0]['title']['text'] if roles[0]['title'] else '',
                    'started': {
                        "year": roles[0]['from']['year'] if roles[0]['from'] else '',
                        "month": roles[0]['from']['month'] if roles[0]['from'] else '',
                    },
                }
                if roles[0]['to']:
                    most_recent_role['finished'] = {
                        "year": roles[0]['to']['year'] if roles[0]['to'] else '',
                        "month": roles[0]['to']['month'] if roles[0]['to'] else '',
                    }
                return most_recent_role
            return {}
        except Exception as e:
            logging.error(f"Error fetching most recent role: {e}")


if __name__ == "__main__":
    mail_client = MailClient("gmail.com")
    with SeekClient(mail_client) as seek_client:
        seek_client.login()
        # resume_uri = seek_client._upload_attachment('CoverLetter', "application_pipeline/application_materials/electrical resume.pdf")
        # logging.info(f"Uploaded resume, got uri: {resume_uri}")