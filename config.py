
import os

URL_LOGIN = 'https://members.energiefitness.com/login/'
URL_LOGIN_API = 'https://members.energiefitness.com/account/login/'

# Runtime environment variables from GCP
URL_MEMBERS_LOCAL_GYM = os.environ.get('URL_MEMBERS_LOCAL_GYM')
BQ_DATASET_ID = os.environ.get('BQ_DATASET_ID')
BQ_TABLE_ID = os.environ.get("BQ_TABLE_ID")
PROJECT_ID = os.environ.get("PROJECT_ID")

# secrets to fetch
SECRET_EMAIL = "my-email"
SECRET_PASSWORD = "my-energiefitness-password"
SECRET_REQUEST_TOKEN = "my-request-verification-token"
