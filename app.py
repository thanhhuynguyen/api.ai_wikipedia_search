#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
import requests
from xml.dom import minidom


import json
import os
import re

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    if req.get("result").get("action") == "googleDistanceMatrix":
        res = distanceRequest(req)

        res = json.dumps(res, indent=4)
        # print(res)
        r = make_response(res)
        r.headers['Content-Type'] = 'application/json'
        return r


    if req.get("result").get("action") == "WikipediaSearch":
        title = search(req)
        res = get_answer(title)

        res = json.dumps(res, indent=4)
        r = make_response(res)
        r.headers['Content-Type'] = 'application/json'
        return r

    if req.get("result").get("action") == "yahooWeatherForecast":
        res = processRequest(req)

        res = json.dumps(res, indent=4)
        # print(res)
        r = make_response(res)
        r.headers['Content-Type'] = 'application/json'
        return r

############################################################################################
# Google Distance Matrix
###########################################################################################
def distanceRequest(req):
    api_key = ' AIzaSyDggNGowyQTuQ9l6sUk1yN_Vf7tj9MtNlE '

    if req.get("result").get("action") != "googleDistanceMatrix":
        return {}
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
    origin, destination = [],[]

    origin_query, destination_query = makeDistanceQuery(req)
    if origin is None or destination is None:
        return {}
        
    origin.append(origin_query)
    destination.append(destination_query)


    # origin = ["ho chi minh"]
    # destination = ["da nang"]

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


###############################################################################33
# wikipedia search
#################################################################################
def search(req):
    if req.get("result").get("action") != "WikipediaSearch":
        return {}
    baseurl = "https://en.wikipedia.org/w/api.php?"
    yql_query = makeSearchQuery(req)
    print (yql_query)
    if yql_query is None:
        return {}
    query = urlencode({'search': yql_query})
    wiki_query = {'action':'opensearch', 'format': 'xml',
                  'namespace': '0', 'limit': '1', 'redirects':'resolve', 'warningsaserror':'1', 'utf8': '1'}
    yql_url = baseurl + urlencode(wiki_query) + "&" + query
    result = urlopen(yql_url).read().decode("utf8")
    search_term = get_title(result)
    return search_term

def get_answer(title):
    baseurl = "https://en.wikipedia.org/w/api.php?"

    query = title.strip().replace(" ", "+")
    wiki_query = {'action':'query', 'format': 'xml', 'prop': 'extracts',
                  'list': '', 'redirects': '1', 'exintro': '', 'explaintext': ''}
    yql_url = baseurl + urlencode(wiki_query) + "&titles=" + query
    print ("ANSWER URL = " + yql_url)
    result = requests.get(yql_url).text
    print ("RESULT:\n" + result)
    res = makeSearchResult(result)
    return res

def get_title(data):
    xmldoc = minidom.parseString(data)
    url = xmldoc.getElementsByTagName('Text')[0].childNodes[0].data
    title = url
    return title

def makeSearchQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    query = parameters.get("phrase")
    if query is None:
        return None
    print ('QUERY' + query)
    return query


def makeSearchResult(data):
    xmldoc = minidom.parseString(data)
    extract = xmldoc.getElementsByTagName('extract')[0].childNodes[0].data

    # speech = extract
    if extract.split(".")[0][-1] != ":":
        if len(extract.split(".")[0].split(" ")) > 3:
            speech = extract.split(".")[0]
        else:
            speech = extract.split(".")[0] + extract.split(".")[1]
    else:
        speech = "i am sorry, i can not find it." 
    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-wikipedia-webhook"
    }


#######################################################################################
# Weather API
#######################################################################################
def processRequest(req):
    if req.get("result").get("action") != "yahooWeatherForecast":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data)
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
