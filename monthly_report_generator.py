#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Sekiwere Samuel"

import requests
import json
import base64
# from settings import config
import getopt
import sys
import datetime
import time
import mysql.connector

dbconfig = {
    'user': 'root',
    'password': 'root',
    'unix_socket': '/opt/local/var/run/mysql8/mysqld.sock',
    'database': 'disis_amr',
}

config = {
    # dispatcher2 confs
    #'dispatcher2_queue_url':'http://localhost:9191/queue',
    'dispatcher2_queue_url':'http://iol.gcinnovate.com/queue',
    'dispatcher2_username': 'admin',
    'dispatcher2_password': 'admin',
    'dispatcher2_source': 'disis',
    'dispatcher2_destination': 'dhis2',

    # DHIS 2
    'dhis2_username': '',
    'dhis2_password': '',
    'dhis2_url': '',
}

cmd = sys.argv[1:]
opts, args = getopt.getopt(
    cmd, 'dy:m:',
    [])

# use current month as default
now = datetime.datetime.now()
year = now.year
month = now.month
DIRECT_SENDING = False

for option, parameter in opts:
    if option == '-d':
        DIRECT_SENDING = True
    if option == '-y':
        year = parameter
        try:
            year = int(year)
        except:
            pass
    if option == '-m':
        month = parameter
        try:
            month = int(month)
        except:
            pass
    # if option == '-f':
    #    ADD_FIELDS = True


def get_start_and_end_date(year, month):
    start_month = datetime.datetime(year, month, 1)
    date_in_next_month = start_month + datetime.timedelta(35)
    start_next_month = datetime.datetime(date_in_next_month.year, date_in_next_month.month, 1)
    return start_month.strftime('%Y-%m-%d'), start_next_month.strftime('%Y-%m-%d')


def post_data_to_dhis2(url, data, params={}, method="POST"):
    user_pass = '{0}:{1}'.format(config['dhis2_username'], config['dhis2_password'])
    coded = base64.b64encode(user_pass.encode())
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + coded.decode()
    }

    response = requests.post(
	url, data=data, headers=headers,
	verify=False, params=params
    )
    return response


def queue_in_dispatcher2(data, url=config['dispatcher2_queue_url'], ctype="json", params={}):
    user_pass = '{0}:{1}'.format(config['dispatcher2_username'], config['dispatcher2_password'])
    coded = base64.b64encode(user_pass.encode())
    if 'xml' in ctype:
        ct = 'text/xml'
    elif 'json' in ctype:
        ct = 'application/json'
    else:
        ct = 'text/plain'
    response = requests.post(
        url, data=data, headers={
            'Content-Type': ct,
            'Authorization': 'Basic ' + coded.decode()},
        verify=False, params=params  # , cert=config['dispatcher2_certkey_file']
    )
    return response

cnx = mysql.connector.connect(**dbconfig)

cursor = cnx.cursor(dictionary=True)
# cursor.execute("SELECT * FROM hh_rawdata LIMIT 2;")

# Let's get the mapping of facilities/Labs to corresponding DHIS 2 UIDs
cursor.execute("SELECT name, dhis2_name, dhis2id FROM facilities")
res = cursor.fetchall()
facilities_mapping = {}
facilitiesList = []
for f in res:
    facilities_mapping[f['name']] = f['dhis2id']
    facilitiesList.append(f['name'])

# let's get the indicator mappings
cursor.execute("SELECT form, slug, cmd, dataset, dataelement, category_option_combo FROM indicator_mapping")
res = cursor.fetchall()
indicator_mappings = {}
for mapping in res:
    indicator_mappings[mapping['slug']] = {
        'cmd': mapping['cmd'],
        'dataset': mapping['dataset'],
        'dataelement': mapping['dataelement'],
        'category_option_combo': mapping['category_option_combo'],
    }


# print(facilities_mapping)

# now get the antibiotics list and mapping
cursor.execute("SELECT name, code, disis_code FROM antibiotics WHERE in_dhis2 = TRUE")
res = cursor.fetchall()
antibioticsDictionary = {}
antibioticsList = []

for antibiotic in res:
    antibioticsDictionary[antibiotic['code']] = antibiotic['disis_code']
    antibioticsList.append(antibiotic['code'])

print(antibioticsDictionary)

# Now get the organisms in DHIS 2
cursor.execute("SELECT name, code FROM organisms WHERE in_dhis2 = TRUE")
organisms = cursor.fetchall()
organismsDictionary = {}
organismsList = []
for organism in organisms:
    organismsList.append(organism['code'])
    organismsDictionary[organism['code']] = organism['name']
print(organismsList)

# Get the isolates for each organism for a given month
start_date, end_date = get_start_and_end_date(year, month)
print (start_date, "==>", end_date)

for facility_name in facilitiesList[9:11]:
    print("### Going to generate data for: {0}:{1}".format(facility_name, facilities_mapping[facility_name]))
    # dispatcher2 queuing params
    extra_params = {
        'year': year,
        'month': month,
        'source': 'disis',
        'destination': 'dhis2',
        'facility': facility_name,
        'is_qparams': "f",
    }

    isolatesDataValues = []
    for organism in organismsList:
        cursor.execute(
            "SELECT count(*) as isolates FROM hh_rawdata WHERE "
            " str_to_date(specimen_collection_date, '%m/%d/%Y') >= %s  AND "
            " str_to_date(specimen_collection_date, '%m/%d/%Y') < %s AND organism = %s "
            " AND laboratory = %s ", (start_date, end_date, organism, facility_name))
        res = cursor.fetchone()
        total_isolates = res['isolates']

        # XXX decide what to do if we have no isolates at all
        if not total_isolates:
            continue
        print("The number of Isolates for {0} in {1}-{2} is {3}".format(
            organismsDictionary[organism], year, month, res['isolates']))
        # build the DHIS 2 payload and insert it into data exchange middleware. dispatcher2
        isolatesDataValues.append(
            {
                'dataElement': indicator_mappings["iso_{0}".format(organism)]['dataelement'],
                'categoryOptionCombo': indicator_mappings["iso_{0}".format(organism)]['category_option_combo'],
                'value': total_isolates})
        # payload = {
        #     'completeDate': datetime.datetime.now().strftime("%Y-%m-%d"),
        #     'period': "{0}{1:02d}".format(year, month),
        #     'orgUnit': facilities_mapping[facility_name],
        #     'dataValues': dataValues
        # }

        # print(">>>>>ISOLATES<<<<< FOR {0} => {1}".format(organism, total_isolates), json.dumps(payload))

        # Get the resistance for the organisms wrt antibiotics

        dataValues2 = []
        for antibiotic in antibioticsList:
            total_resistance = 0
            temporar_dataValues = []
            for resistance in ('R', 'I', 'S'):
                query = (
                    "SELECT count(*) as resistance FROM hh_rawdata WHERE laboratory = %s AND "
                    " str_to_date(specimen_collection_date, '%m/%d/%Y') >= %s  AND "
                    " str_to_date(specimen_collection_date, '%m/%d/%Y') < %s AND organism = %s AND "
                    " {0} = %s")
                query = query.format(antibioticsDictionary[antibiotic])

                cursor.execute(query, (facility_name, start_date, end_date, organism, resistance))
                res = cursor.fetchone()
                total_resistance += res['resistance']
                temporar_dataValues.append(
                    {
                        'dataElement': indicator_mappings["{0}_{1}_{2}".format(
                            antibiotic, organism, resistance.lower())]['dataelement'],
                        'categoryOptionCombo': indicator_mappings["{0}_{1}_{2}".format(
                            antibiotic, organism, resistance.lower())]['category_option_combo'],
                        'value': res['resistance']})
                # print("{0}_{1}_{2} => {3}".format(antibiotic, organism, resistance.lower(), res['resistance']))

            if total_resistance > 0:  # only add if antibitic was tested XXX
                for v in temporar_dataValues:
                    dataValues2.append(v)
        if dataValues2:
            payload2 = {
                'completeDate': datetime.datetime.now().strftime("%Y-%m-%d"),
                'period': "{0}{1:02d}".format(year, month),
                'orgUnit': facilities_mapping[facility_name],
                'dataValues': dataValues2
            }
            print(">>>>><<<<<<", json.dumps(payload2))
            extra_params['report_type'] = organism
            if DIRECT_SENDING:
                pass
            else:
                queue_in_dispatcher2(json.dumps(payload2), ctype="json", params=extra_params)

    # Compose Isolates Payload after going through all isolates
    if isolatesDataValues:
        payload = {
            'completeDate': datetime.datetime.now().strftime("%Y-%m-%d"),
            'period': "{0}{1:02d}".format(year, month),
            'orgUnit': facilities_mapping[facility_name],
            'dataValues': isolatesDataValues
        }
        print(">>>>>ISOLATES<<<<< FOR {0} => {1}".format(facility_name, json.dumps(payload)))
        extra_params['report_type'] = 'iso'
        if DIRECT_SENDING:
            pass
        else:
            queue_in_dispatcher2(json.dumps(payload), ctype="json", params=extra_params)

cnx.close()
