from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

import json
import pprint
from pprint import pprint
import os
import sys
import urllib.parse

# send data thru MQTT
import paho.mqtt.client as mqtt
import json

# send data HTTP
import base64
import requests

# data handling libraries 
import arrow 
import numpy as np
from pandas.io.json import json_normalize
import pandas as pd

class Konker(object):
    base_api = 'https://api.demo.konkerlabs.net'
    application = 'default'
    token = None
    client = None
    oauth = None
    deviceClientCache = {}

    def load_credential(self, cid):
        ''' use this function to load the credentials of the user from a configuration file 
            named 'credentials.json' on the current path 
        '''
        # lookup for credential file
        if os.path.isfile('credentials.json'):
            with open('credentials.json') as f:
                credentials = json.load(f)
        else:
            print('"credentials.json" not found. You must define the username and password by yourself')
            credentials = {}
            
        try:
            username = credentials[cid]['username']
            password = credentials[cid]['password']

            return {'username':username, 'password':password}

        except Exception as e:
            raise Exception('"{}" not found on credentials file'.format(cid))

        return {}

    def login(self, cid='', username='', password=''):
        ''' use this function to connect to the platform using predefined credentials 
            on "credentials.json" file or given explicity username and password
            '''
        
        if (cid != ''):
            # lookup for credential file
            if os.path.isfile('credentials.json'):
                with open('credentials.json') as f:
                    credentials = json.load(f)
            else:
                print('"credentials.json" found. You must define the username and password by yourself')
                credentials = {}
                
            try:
                username = credentials[cid]['username']
                password = credentials[cid]['password']
            except Exception as e:
                raise Exception('"{}" not found on credentials file'.format(cid))
        else:
            # must have informed username and password ....
            if (len(username) == 0 or len(password) == 0):
                print('invalid username or password')
                return None, None
            
            
        # try to login on the platform ... 
            
        self.client = BackendApplicationClient(client_id=username)
        self.oauth = OAuth2Session(client=self.client)
        self.token = self.oauth.fetch_token(token_url='{}/v1/oauth/token'.format(self.base_api),
                                               client_id=username,
                                               client_secret=password)
        
        # log the username 
        self.username = username 
        
        return self.oauth, self.token 
    
    def setApplication(self, _name):
        '''
        define the application to be used this point forward
        '''
        self.application = _name
        
    def checkConnection(self):
        if (not self.oauth):
            raise Exception('not connected. login first')
        
    def getAllLocations(self):
        '''
        retrieve a list of all devices connected to this application, visible to your user
        '''
        self.checkConnection()
        locations = self.oauth.get("{}/v1/{}/locations/".format(self.base_api, self.application)).json()['result']
        return locations

    def getAllDevices(self):
        '''
        retrieve a list of all devices connected to this application, visible to your user
        '''
        self.checkConnection()
        devices = self.oauth.get("{}/v1/{}/devices/".format(self.base_api, self.application)).json()['result']
        return devices

    def getDeviceCredentials(self, guid):
        '''
        get credentials for a device 
        '''
        self.checkConnection()
        info = self.oauth.get("{}/v1/{}/deviceCredentials/{}".format(self.base_api, self.application, guid)).json()
        return info
    
    
    def getAllDevicesForLocation(self, location):
        '''
        retrieve a list of all devices for a given STORE.
        give just the store # as a parameter, for instance:
        app.getAllDevicesForStore(1234)
        '''
        self.checkConnection()
        devices = self.oauth.get("{}/v1/{}/devices/?locationName={}".format(self.base_api, self.application, location)).json()['result']
        return devices

    def onConnect(self, client, userdata, flags, rc):
        print('connected to client={} | ud={} | flags={} | rc={}'.format(client, userdata, flags, rc))


    def connectMQTT(self, device, usr, pwd):
        if device in self.deviceClientCache:
            return self.deviceClientCache[device]
        client = mqtt.Client(device)
        client.username_pw_set(usr, pwd)
        client.on_connect = self.onConnect
        client.connect("mqtt.demo.konkerlabs.net", 1883, keepalive=60)
        self.deviceClientCache[device] = {'mqtt':client, 'id':usr}
        return client


    def sendDataMQTT(self, device, channel, data, usr=None, pwd=None):
        client = self.connectMQTT(device,usr,pwd)
        url="data/{}/pub/{}".format(client['id'], channel)
        print('sending to {} = {}'.format(url, json.dumps(data)))
        return client['mqtt'].publish(url, json.dumps(data))

    def sendDataHTTP(self, device, channel, data, usr=None, pwd=None):
        ans = 0
        while (ans!=200):
            try:
                token = base64.b64encode('{}:{}'.format(usr,pwd))
                req = requests.post( 
                    "https://data.demo.konkerlabs.net/pub/{}/{}".format(usr,channel),  
                    headers={'Authorization': 'Basic ' + token}, data='['+json.dumps(data)+']')
                ans = req.status_code
                #print('['+k_data.decode()+']')
            except requests.exceptions.RequestException as e:
                ans = 0


        
    def readData(self, guid, channel=None, delta=-10, start_date=None):
        '''
        read data from a given device for a specific period of time (default 10 days)
        and a starting date (if not informed return last X days)
        
        the final returning is a Pandas Dataframe that can be used for further processing
        '''
        self.checkConnection()
        stats_dfa = []
        interval = 2 if abs(delta) > 1 else 1

        if (start_date):
            dt_start = start_date
        else:
            dt_start = arrow.utcnow().to('America/Sao_Paulo').floor('day')

        dt_start = dt_start.shift(days=delta)

        for batch in range(0,int((delta*-1) / interval)+1):
            dt_end = dt_start.shift(days=interval)

            q = 'device:{}{}timestamp:>{} timestamp:<{}'.format(
                guid, 
                ' channel:{} '.format(channel) if channel else ' ',
                dt_start.isoformat(), 
                dt_end.isoformat()
            )
            q = urllib.parse.quote(q)
                        
            statsx = self.oauth.get(
                "{}/v1/{}/incomingEvents?q={}&sort=newest&limit=10000".format(
                    self.base_api,    
                    self.application,
                    q
                )
            )
                    
            stats = statsx.json()['result']
            if (stats and len(stats) > 0):
                stats_dfx = json_normalize(stats).set_index('timestamp')
                stats_dfx = stats_dfx[3:]
                stats_dfa.append(stats_dfx)
            dt_start = dt_end
        return pd.concat(stats_dfa) if len(stats_dfa) > 0 else pd.DataFrame()       
    
            