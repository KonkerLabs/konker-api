# konker-api
this repository contains API libraries that can be used to accelerate the usage of Konker Platform, written in several languages to help use the platform API

## sample

contains some simple usage samples of wrappers to call / manage Konker API calls using different languages.
each file basically provide:

a) login on the platform  -- using a commmon login for sample usage 
b) get a list of devices that this user can access on the platform 
c) get last samples of data received by this device, in all channels it has

## src

this folder contains the implementation for Konker API using several languages. 
its main purpose is to facilitate and accelerate the use of the Konker API providing common access methods that encapsulates raw HTTPS calls to othe API 

fell free to implement more accessor methods or to create new languages wrappers in this folder. 
you can submit a new pull request that will be evaluated and tested by the team to be released on the wild.

