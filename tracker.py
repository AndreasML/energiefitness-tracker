
import csv
from datetime import datetime
from time import sleep
from bs4 import BeautifulSoup
import requests
from lxml import html
from bs4 import BeautifulSoup
import os
from local_config import secrets, URL_MEMBERS_LOCAL_GYM

URL_LOGIN = 'https://members.energiefitness.com/login/'
URL_LOGIN_API = 'https://members.energiefitness.com/account/login/'
DATA_SUBDIRECTORY = "data"
CHECK_INTERVAL_MINUTES = 5

def get_token(session):
    headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        }
    r = session.get(URL_LOGIN, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    token = soup.select('input[name="__RequestVerificationToken"]')[0]['value']
    return token

def login():

    # Persistent login session
    session = requests.session()

    
    # # Get login auth token
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
        'Email': secrets.email,
        'Password': secrets.password,
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
    print(num)
    return num


def write_data(scrape_datetime, num_people, output_file):
    f = open(output_file, 'a', newline='')
    w = csv.writer(f)
    w.writerow([scrape_datetime.date(), scrape_datetime.strftime("%A"), scrape_datetime.strftime("%H:%M"), num_people])


def track(login_session):
    scrape_datetime = datetime.utcnow()
    no_of_members = get_number(login_session)
    outfile_name = 'members.csv'
    full_outfile_path = os.path.join(os.path.dirname(__file__), DATA_SUBDIRECTORY, outfile_name)
    write_data(scrape_datetime, no_of_members, full_outfile_path)
    return no_of_members

if __name__ == "__main__":

    login_session = login()
    track(login_session)