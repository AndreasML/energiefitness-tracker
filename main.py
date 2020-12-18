"""
    Named "main.py" for the purpose of Google Cloud Function.
"""
from datetime import datetime
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


def login():

    # Persistent login session
    session = requests.session()

    # Get login auth token
    result = session.get(URL_LOGIN)
    tree = html.fromstring(result.text)

    headers = {
        'authority': 'members.energiefitness.com',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'origin': 'https://members.energiefitness.com',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://members.energiefitness.com/login/',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cookie': 'OptanonAlertBoxClosed=2020-10-10T10:53:05.398Z; .AspNetCore.Antiforgery.RuGnUm8OIDw=CfDJ8J4QTDSFntBOk5KNSaeuQStASOpek_zO7iLwba91NO1MHvyr-uQQYjWUrM7RZEiqU1H1CN60W1i2zj4x2cbMy9v6vfznCcOE-tEs0Fc82ZPR9kXsVJ_zxTfyb1CNN61TUa3JlP0DIC7PexYq77Lg5-Y; .AspNetCore.Identity.Application=CfDJ8J4QTDSFntBOk5KNSaeuQSuUmjGnB2eTztyOXvIG_W4KSIaxoUQw5A5s_wZ3nGlHtmleM0ShR0fdB592mYcj3Jyx10XX83BbgSSl5jaa7HvE-aWQv4PHQU2DZ5okg-wwE9O9lxIcxqGDt0s4074x5FUnxm9iYuLj7lhweh-k76jaWBwMcmb0suY46FdSOXI97_8AXjzBFY-MuJJpXWfpklKt8wk5RkSJZepjaSh1SlNJT0IdpNQzrC4faBo6gEAkWHzRh_PlLpu2TKuIoE_Vb9eQgsD_h6vRC0NTJvSi_8bHJ3QHt05rksBzVRxDXAtUT07g9UCD0-BmvOci9NHHXvA8R_aMqq8Zso-gNEcr5BWpE0Hb5jXqFaTq-xQT4yG6h5mpYv6Yb0-hgUbKf-9ABJrmCwF4aNeO4Qa07LtFTl0p2tSW-Q1LAsD6SKbqlqDUxRROdHBQscIkEaP6q10kaIAyqp_WoZ9JFVl9efh9Pp9x7N8eVelchUcLcCbPkRNHWCA_4h1xUFXfDi3isFyVX7C0T1KHWGAIKXnE4Ufye_HBH5Jfr8sP3y96p1wACUpX4RvAZ1NrOZanRUUM2r-TUH49ZpRlwX503FP5ItcPtsyf; OptanonConsent=landingPath=NotLandingPage&datestamp=Wed+Oct+28+2020+12%3A00%3A03+GMT%2B0000+(Greenwich+Mean+Time)&version=3.6.28&groups=1%3A1%2C2%3A1%2C4%3A1%2C0_51523%3A1%2C0_51522%3A1&AwaitingReconsent=false',
    }

    payload = {
        'Email': get_secret(SECRET_EMAIL),
        'Password': get_secret(SECRET_EMAIL),
        '__RequestVerificationToken': get_secret(SECRET_REQUEST_TOKEN)
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
    
    d = datetime.utcnow()
    date_string = d.strftime("%A") 
    time_string = d.strftime("%H:%M")

    no_of_members = get_number(login_session)
    
    GymData = namedtuple('GymData', 'date day time members')
    result = GymData(date = str(d.date()), day = d.strftime("%A"), time = time_string, members = no_of_members)

    write_data_to_bq(result)
    
    return json.dumps(result._asdict()), 200, {'ContentType': 'application/json'}
