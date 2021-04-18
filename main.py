"""
    Named "main.py" for the purpose of Google Cloud Function.
"""
import datetime
import time
from bs4 import BeautifulSoup
import requests
from lxml import html
import os
from collections import namedtuple
import json
from google.cloud import bigquery, secretmanager
from config import *


def get_secret(secret):
    secrets_client = secretmanager.SecretManagerServiceClient()
    request = {"name": f"projects/{PROJECT_ID}/secrets/{secret}/versions/latest"}
    response = secrets_client.access_secret_version(request)
    secret_string = response.payload.data.decode("UTF-8")
    return secret_string


def get_token(session):
    headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        }        
    r = session.get(URL_LOGIN, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    token = soup.select('input[name="__RequestVerificationToken"]')[0]['value']
    ## Report successful token discovery
    print("Initial GET request Successful: ", r.ok)
    print("Token: ", token)
    return token


def login():

    # Persistent login session
    session = requests.session()

    # Get login auth token
    token = get_token(session)

    headers = {
        'authority': 'members.energiefitness.com',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'origin': 'https://members.energiefitness.com',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'referer': URL_LOGIN,
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }


    payload = {
        'Email': get_secret(SECRET_EMAIL),
        'Password': get_secret(SECRET_PASSWORD),
        '__RequestVerificationToken': token
    }

    # Perform login
    result = session.post(
        URL_LOGIN_API,
        data=payload,
        headers=headers
    )
    
    # Report successful login
    print("Login succeeded: ", result.ok)
    print("Status code:", result.status_code)

    return session


def get_number(session):
    page = session.get(URL_MEMBERS_LOCAL_GYM)
    soup = BeautifulSoup(page.content, 'html.parser')
    num = int(soup.find('div', {'class': 'column'}).find('h1').text)
    return num


def write_data_to_bq(row):

    # Instantiates a client
    bigquery_client = bigquery.Client()

    # Prepares a reference to the dataset
    dataset_ref = bigquery_client.dataset(BQ_DATASET_ID)

    table_ref = dataset_ref.table(BQ_TABLE_ID)
    table = bigquery_client.get_table(table_ref)  # API call

    rows_to_insert = [row]
    errors = bigquery_client.insert_rows(table, rows_to_insert)  # API request
    assert errors == []


def track(event, context):

    login_session = login()
    
    d = datetime.datetime.utcnow()
    date_string = d.strftime("%A") 
    time_string = time.strftime("%H:%M")

    no_of_members = get_number(login_session)
    
    GymData = namedtuple('GymData', 'date day time members')
    result = GymData(date = str(d.date()), day = d.strftime("%A"), time = time_string, members = no_of_members)

    write_data_to_bq(result)
    
    return json.dumps(result._asdict()), 200, {'ContentType': 'application/json'}
