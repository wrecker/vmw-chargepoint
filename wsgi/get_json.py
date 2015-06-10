#!/usr/bin/env python
#
# Copyright (c) 2015 Raju Subramanian <coder@mahesh.net>
#
# MIT LICENSE
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
import json
import logging
import os
import pytz
import requests
import sys
import types

from collections import OrderedDict
from datetime import datetime
from pytz import timezone

DATA_DIR = os.getenv("OPENSHIFT_DATA_DIR", '')
JSON_FILE = DATA_DIR + 'current.json'
PUSHBULLET_KEY_FILE = DATA_DIR + '.pb_key'
PASSWORD_FILE = DATA_DIR + '.cp_passwd'

# Garages & Pushbullet-channels
# NOTE: Only the owner/creator of a channel can push notifications
# to a channel. If you are setting up your own instance, you will
# need to create similar channels on pushbullet.com.
GARAGES = {'Central Garage': 'cp-vmw-cg',
           'Creekside Garage': 'cp-vmw-cr',
           'Hilltop Garage': 'cp-vmw-ht'}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Turn down requests module's logging
logging.getLogger("requests").setLevel(logging.WARNING)


def get_epoch():
    return (datetime.now() - datetime(1970, 1, 1)).total_seconds()


def get_status(query_data, station_prefix):
    with open(PASSWORD_FILE) as passwd_file:
        credentials = [x.strip().split(':') for x in passwd_file.readlines()]
    cp_username, cp_password = credentials[0]

    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:21.0) Gecko/20100101 Firefox/21.0',
        'Host': 'na.chargepoint.com',
        'Referer': 'https://na.chargepoint.com/',
        'X-Requested-With': 'XMLHttpRequest'}
    login_data = {
        'user_name': cp_username,
        'user_password': cp_password,
        'recaptcha_response_field': '',
        'timezone_offset': '480',
        'timezone': 'PST',
        'timezone_name': ''}
    url = 'https://na.chargepoint.com/users/validate'
    req = session.post(url, headers=headers, data=login_data, verify=False)
    url = 'https://na.chargepoint.com/dashboard/getFavoriteStationsList'
    req = session.post(url, headers=headers, data=query_data, verify=False)
    data = req.json()

    if not isinstance(data, types.ListType) or 'summaries' not in data[0]:
        return None

    summaries = data[0]['summaries']
    port_status = {}
    for summary in summaries:
        if 'station_name' not in summary:
            continue
        station_name = ' '.join(summary['station_name'])
        if not station_name.startswith(station_prefix):
            continue
        total_ports = summary['port_count']['total']
        available = summary['port_count']['available']
        device_id = summary['device_id']
        status = summary['station_status']
        port_status[device_id] = (station_name, available, total_ports, status)

    return port_status


def build_dict(station_list, port_status):
    ret = OrderedDict()
    for station_id in station_list:
        if station_id not in port_status:
            continue
        ret[port_status[station_id][0]] = []
        total = port_status[station_id][2]
        available = port_status[station_id][1]
        if port_status[station_id][3] != 'unknown':
            ret[port_status[station_id][0]] = [total, available, 0]
        else:
            ret[port_status[station_id][0]] = [total, 0, total]
    return ret


def post_pushbullet(channel, title, body):
    """Post message to pushbullet channel."""
    pb_key = None
    try:
        with open(PUSHBULLET_KEY_FILE) as key_file:
            data = key_file.readlines()
            if len(data):
                pb_key = data[0].strip()
    except IOError as ioe:
        logging.error("Could not open %s [%s]", PUSHBULLET_KEY_FILE, ioe)

    if not pb_key:
        logging.error("No PushBullet API Key found. "
                      "Push notifications are disabled.")

    url = "https://api.pushbullet.com/v2/pushes"
    header = {'Content-Type': 'application/json'}
    data = {'channel_tag': channel, 'type': 'note', 'title': title, 'body': body}
    res = requests.post(url, data=json.dumps(data), headers=header,
                        auth=(pb_key, ''))
    logging.info("Pushbullet Push: Status: %s, Message: %s",
                 res.status_code, res.text)

def get_json():
    query_data = {
        'placeId': 1391648779079,
        'sort_by': 'distance',
        'reference_lat': 0,
        'reference_lon': 0,
        'page_offset': '',
        'mapCords[lat]': 4.63046e+18,
        'mapCords[lng]': -4.58508e+18,
        'mapCords[f_estimationfee]': 'false',
        'mapCords[f_available]': 'true',
        'mapCords[f_inuse]': 'true',
        'mapCords[f_unknown]': 'true',
        'mapCords[f_cp]': 'true',
        'mapCords[f_other]': 'true',
        'mapCords[f_l3]': 'false',
        'mapCords[f_l2]': 'true',
        'mapCords[f_l1]': 'false',
        'mapCords[f_estimate]': 'false',
        'mapCords[f_fee]': 'true',
        'mapCords[f_free]': 'true',
        'mapCords[f_reservable]': 'false',
        'mapCords[f_shared]': 'true'}

    cg_stations = [
        79403,
        79363,
        79333,
        79383,
        79083,
        34743,
        71263]
    cr_stations = [
        98831,
        111415,
        92191,
        91785,
        92533,
        91141,
        91759,
        91091]
    ht_stations = [
        92219,
        91749,
        91783,
        92525,
        92197,
        91753,
        91777,
        91781]
    port_status = get_status(query_data, 'VMWARE')
    json_d = OrderedDict()
    json_d['Central Garage'] = build_dict(cg_stations, port_status)
    json_d['Hilltop Garage'] = build_dict(ht_stations, port_status)
    json_d['Creekside Garage'] = build_dict(cr_stations, port_status)

    process_data(json_d)


def process_data(data):
    new_data = data
    # Load the existing data
    curr_data = {}
    try:
        with open(JSON_FILE, "r") as currfile:
            curr_data = json.load(currfile)
    except IOError:
        logging.error("Could not load current.json")

    # Compare the two
    garage_new_openings = {}

    notify = 0
    if len(sys.argv) > 1 and sys.argv[1] == 'notify':
        notify = 1

    free_stations = OrderedDict()

    for garage, stations in new_data.iteritems():
        garage_new_openings[garage] = 0
        free_stations[garage] = []
        # Pass 1
        for station, data_tuple in stations.iteritems():
            # Add default marker to station
            data_tuple.append(0)
            if garage in curr_data and station in curr_data[garage]:
                # tuple[1]: no of free ports in the station
                # if free-ports in new is same as current, then check the 'trigger' marker
                # if '1': this station has not triggered an alert since it turned green.
                #         Conditionally trigger notification
                # if '0': this station has already triggered and is still green. Don't
                #         trigger notification for this garage.
                if curr_data[garage][station][1] and (
                        data_tuple[1] == curr_data[garage][station][1]):
                    # Check Marker (1=Not Triggered, 0=Triggered)
                    if len(curr_data[garage][station]) == 4:
                        if curr_data[garage][station][3]:
                            garage_new_openings[garage] += 1
                            free_stations[garage].append(station.replace("VMWARE ", ""))
                            # Update Marker
                            data_tuple[3] = 1
                        else:
                            garage_new_openings[garage] = -100
                # New free ports in this station. Set conditional trigger and update
                # marker for this station to not triggered.
                if data_tuple[1] > curr_data[garage][station][1]:
                    garage_new_openings[garage] += 1
                    free_stations[garage].append(station.replace("VMWARE ", ""))
                    data_tuple[3] = 1

        # Pass 2
        # Conditional Trigger.. Clear marker.
        if notify and garage_new_openings[garage] > 0:
            for station, data_tuple in stations.iteritems():
                data_tuple[3] = 0
        else:
            garage_new_openings[garage] = -1

    time_format = '%m/%d %I:%M %p'
    date = datetime.now(tz=pytz.utc)
    time_str = date.astimezone(timezone('US/Pacific')).strftime(time_format)

    for garage, pb_tag in GARAGES.iteritems():
        if garage_new_openings[garage] > 0:
            post_pushbullet(pb_tag, "%s: Ports Free" % garage,
                            ("[%s] One or more charging ports are free in this Garage."
                             "\nStations Free: %s"
                             "\nCheck Chargepoint or http://wreckr.net/vmw to "
                             "confirm availability.") % (
                                 time_str, ", ".join(free_stations[garage])))

    new_data['last_updated_epoch'] = get_epoch()
    with open(JSON_FILE, "w") as outfile:
        outfile.write(json.dumps(new_data, indent=2))


if __name__ == '__main__':
    get_json()
