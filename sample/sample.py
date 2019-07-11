'''
 KONKER SAMPLE APPLICATION TO LIST ALL DEVICES ASSOCIATED WITH AN ACCOUNT 
 2019

 MIT License
'''

import sys
sys.path.insert(0, '../src/python')

import konker as api

konker = api.Konker()

username = 'jobs@konkerlabs.com'
password = 'gokonkergokonker!'

(_, token) = konker.login(username=username, password=password)

if token:

  print('LIST OF AVAILABLE DEVICES ------ ')
  for device in konker.getAllDevices(): 
    print(device)

    print('. GETTING DATA FOR DEVICE {} ---- '.format(device['name']))
    data = konker.readData(device['guid'], delta=-1)
    print(data)
    print('...')

  print ('Done.')
