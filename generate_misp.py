#!/usr/bin/env python3

import requests
import json
from collections import defaultdict
import datetime
from calendar import monthrange, day_name
import time

import geoip2.database

from config import misp as misp_conf
from config import all as all_conf

DIR = misp_conf['DIR']
BASE_URL = misp_conf['baseurl']
AUTHKEY = misp_conf['authkey']
HOST_ORG = misp_conf['MISP.host_org']
GEOLOCATION_PATH = all_conf['geolocation_path']
START_YEAR = all_conf['start_year']
HEADERS = {
    'Authorization': AUTHKEY,
    'Accept': 'application/json',
    'Content-type': 'application/json',
}

TIMER = 0


reader = geoip2.database.Reader(GEOLOCATION_PATH)

def getCountryFromIp(ip):
    try:
        record = reader.country(ip)
        return record.country.iso_code
    except (geoip2.errors.AddressNotFoundError, ValueError):
        return 'no-ip'

def log(text):
    print(text)

def start_timer():
    global TIMER
    TIMER = time.time()

def print_duration():
    global TIMER
    print(f' Took {int(time.time() - TIMER)} secondes')

def fetch_data():
    endpoint = '/admin/logs/index'
    userData = {
        "model": "User",
        "action": "add"
    }
    log('Collecting user data')
    start_timer()
    r = requests.post(BASE_URL + endpoint, data=json.dumps(userData), headers=HEADERS)
    print_duration()
    userResponse = r.json()

    endpoint = '/admin/logs/index'
    userData = {
        "model": "Organisation",
        "action": "add"
    }
    log('Collecting organisation data')
    start_timer()
    r = requests.post(BASE_URL + endpoint, data=json.dumps(userData), headers=HEADERS)
    print_duration()
    orgsResponse = r.json()

    endpoint = '/admin/logs/index'
    userData = {
        "model": "User",
        "action": "login"
    }
    log('Collecting login data')
    start_timer()
    r = requests.post(BASE_URL + endpoint, data=json.dumps(userData), headers=HEADERS)
    print_duration()
    loginResponse = r.json()

    data = {
        'users': userResponse,
        'orgs': orgsResponse,
        'login': loginResponse,
    }
    return data

def compile_data(rawData):
    log('Compiling user data')
    start_timer()
    userCreation = defaultdict(int)
    for entry in rawData['users']:
        entry = entry['Log']
        dateYearStr = entry['created'][:4]
        if int(dateYearStr) < START_YEAR:
            continue
        dateStr = entry['created'][:7]
        userCreation[dateStr] += 1

    print_duration()
    log('Compiling organisation data')
    start_timer()
    orgAllCreation = defaultdict(int)
    orgLocalCreation = defaultdict(int)
    orgKnownCreation = defaultdict(int)
    for entry in rawData['orgs']:
        entry = entry['Log']
        dateYearStr = entry['created'][:4]
        if int(dateYearStr) < START_YEAR:
            continue
        dateStr = entry['created'][:7]
        orgAllCreation[dateStr] += 1
        if entry['org'] == HOST_ORG:
            orgLocalCreation[dateStr] += 1
        else:
            orgKnownCreation[dateStr] += 1

    print_duration()
    log('Compiling login data')
    start_timer()
    today = datetime.date.today()
    userLoginMonth = defaultdict(int)
    userLoginMonthName = defaultdict(set)
    userLoginDay = defaultdict(int)
    userLoginDayName = defaultdict(set)
    userLoginYearCountry = defaultdict(lambda: defaultdict(int))
    userLoginYearCountryName = defaultdict(set)
    userLoginHour = {
        year: {
            day: {
                h: 0 for h in range(0, 24)
            } for day in day_name
        } for year in range(START_YEAR, today.year+1)
    }
    userLoginHourName = {
        year: {
            day: set() for day in day_name
        } for year in range(START_YEAR, today.year+1)
    }
    for entry in rawData['login']:
        entry = entry['Log']
    
        dateYearStr = entry['created'][:4]
        if int(dateYearStr) < START_YEAR:
            continue
        if entry['model_id'] not in userLoginYearCountry[dateYearStr]:
            ip = entry['ip'].split(',')[0]
            country = getCountryFromIp(ip)
            userLoginYearCountry[dateYearStr][country] += 1
            userLoginYearCountryName[dateYearStr].add(entry['model_id'])
    
        dateStr = entry['created'][:10]
        if entry['model_id'] not in userLoginDayName[dateStr]:
            userLoginDay[dateStr] += 1
            userLoginDayName[dateStr].add(entry['model_id'])

        dateStrMonth = entry['created'][:7]
        if entry['model_id'] not in userLoginMonthName[dateStrMonth]:
            userLoginMonth[dateStrMonth] += 1
            userLoginMonthName[dateStrMonth].add(entry['model_id'])

        date = datetime.datetime.fromisoformat(entry['created'])
        dayName = day_name[date.weekday()]
        if entry['model_id'] not in userLoginHourName[date.year][dayName]:
            userLoginHour[date.year][dayName][date.hour] += 1
            userLoginHourName[date.year][dayName].add(entry['model_id'])

    for y in range(START_YEAR, today.year+1):
        for m in range(1, 13):
            if y == today.year and m == today.month+1:
                break
            dateStr = f'{y}-{str(m).zfill(2)}'
            userCreation[dateStr] += 0
            orgAllCreation[dateStr] += 0
            orgLocalCreation[dateStr] += 0
            orgKnownCreation[dateStr] += 0
            userLoginMonth[dateStr] += 0
            for d in range(1, monthrange(y, m)[1]+1):
                dateStrDay = dateStr + f'-{d}'
                userLoginDay[dateStrDay] += 0

    print_duration()
    data = {
        'users': userCreation,
        'orgs_all': orgAllCreation,
        'orgs_local': orgLocalCreation,
        'orgs_known': orgKnownCreation,
        'login_month': userLoginMonth,
        'login_hour': userLoginHour,
        'login_country': userLoginYearCountry,
    }
    return data


def writeOnDisk(data):
    filename = 'data-misp' + '.json'
    j = data
    with open(DIR+filename, 'w') as f:
        json.dump(j, f)
    return filename


def generate():
    rawData = fetch_data()
    data = compile_data(rawData)
    filename = writeOnDisk(data)
    return filename


if __name__ == '__main__':
    filename = generate()
    print(filename)
