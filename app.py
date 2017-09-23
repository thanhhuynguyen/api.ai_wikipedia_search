# -*- coding:utf8 -*-
# !/usr/bin/env python
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

import requests
# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = distanceRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def distanceRequest(req):
    api_key = ' AIzaSyDggNGowyQTuQ9l6sUk1yN_Vf7tj9MtNlE '

    if req.get("result").get("action") != "googleDistanceMatrix":
        return {}
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
    origin, destination = makeDistanceQuery(req)
    if origin is None or destination is None:
        return {}
    
    payload = {
        'origins' : '|'.join(origin),
        'destinations' : '|'.join(destination), 
        'mode' : 'driving',
        'api_key' : api_key
    }

    result = requests.get(base_url, params = payload)
    ###
    # result = urlopen(yql_url).read()
    data = json.loads(result.text)
    res = makeDistanceResult(data)
    return res


def makeDistanceQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    origin = parameters.get("geo-city")
    destination = parameters.get("geo-city1")

    if origin is None or destination is None:
        return None

    return origin, destination


def makeDistanceResult(data):
    for isrc, src in enumerate(data['origin_addresses']):
        for idst, dst in enumerate(data['destination_addresses']):
            row = data['rows'][isrc]
            cell = row['elements'][idst]
            if cell['status'] == 'OK':
                speech = 'i got distance between {} and {} is {}, if you driving , you will loss {}.'.format(src, dst, cell['distance']['text'], cell['duration']['text'])
            else:
                speech = "i am sorry, i can not got it, maybe you can use your google map"
    # print(json.dumps(item, indent=4))

    # speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
    #          ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-distance-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')


