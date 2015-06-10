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
import humanize
import json
import logging
import os

from collections import OrderedDict
from flask import Flask, render_template
from datetime import datetime


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Data dir
DATA_DIR = os.getenv("OPENSHIFT_DATA_DIR", "")
JSON_FILE = DATA_DIR + 'current.json'

def get_epoch():
    return (datetime.now() - datetime(1970, 1, 1)).total_seconds()

@app.route('/vmw')
def show_status_vmw():
    with open(JSON_FILE, 'r') as infile:
        data = json.load(infile, object_pairs_hook=OrderedDict)
    render_data = []
    update_time = 'unknown'
    for garage, stations in data.iteritems():
        if garage == 'last_updated_epoch':
            continue
        row = {'name': garage, 'stations': []}
        for station, port_data in stations.iteritems():
            col = {'name': station, 'ports': []}
            total = port_data[0]
            available = port_data[1]
            unknown = port_data[2]
            if total != unknown:
                for _ in range(available):
                    col['ports'].append(1)
                for _ in range(total - available):
                    col['ports'].append(0)
            else:
                for _ in range(total):
                    col['ports'].append(-1)
            row['stations'].append(col)
        render_data.append(row)

    if 'last_updated_epoch' in data:
        update_time = humanize.naturaltime(get_epoch() - data['last_updated_epoch'])
    return render_template('dashboard.html',
                           title='VMW Chargepoint Stations',
                           garages=render_data, last_update=update_time)

@app.route("/getCP")
def get_data():
    """DEBUG: Returns the current json data."""
    with open(JSON_FILE, "r") as curr:
        data = curr.readlines()
        return "\n".join(data) + "\n" + os.getenv("OPENSHIFT_APP_UUID", "BLANK")


if __name__ == "__main__":
    app.run(host='0.0.0.0')
