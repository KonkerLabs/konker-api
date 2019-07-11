//
// KONKER SAMPLE APPLICATION TO LIST ALL DEVICES ASSOCIATED WITH AN ACCOUNT 
// 2019
//
// MIT License
// 

const konker = require('../src/nodejs/KonkerApi');

const username = 'jobs@konkerlabs.com';
const password = 'gokonkergokonker!';
const appname = 'default';


konker.authenticate(username, password).then((res) => {
  konker.getAllDevices(appname).then((res) => {
    // console.log(res.data);
    if (res.data.code === 200) { 
      // console.log(res.data);
      res.data.result.forEach(device => {

        console.log('device = '+ JSON.stringify(device));

        konker.getIncomingEvents(appname, device.guid).then(res => {
          console.log('DEVICE DATA --> ');
          console.log(res.data);
        })

      });

    }
  }).catch(err => {console.log(err)})
}).catch(err => {console.log(err)})

