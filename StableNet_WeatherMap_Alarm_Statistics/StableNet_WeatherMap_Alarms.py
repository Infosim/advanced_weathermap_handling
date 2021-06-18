#!/usr/bin/env python
# coding: utf-8

# <center><img src='https://www.intel.com/content/dam/develop/external/us/en/images/infosim-logo-746616.png' style="width:300px"></center>

# <h1 align="center">StableNet® WeatherMap Handling </h1>
# <h2>Introduction</h2>
# This script gives a simple example on how to
# <ol>
#     <li>Load a WeatherMap from StableNet® using the REST API</li>
#     <li>Enhance the WeatherMap with advanced REST API calls to obtain alarms filtered for the selected element and add them as statistics</li>
#     <li>"Re-Add" the WeatherMap to the server as enhanced version using the REST API once more.</li>
# </ol>
# <h2>Import necessary python modules</h2>

# In[1]:


import warnings
import requests
from requests.auth import HTTPBasicAuth
import getpass
from xml.etree import ElementTree


# <h2>Enter Server Credentials & WeatherMapID to be used as base</h2>

# In[6]:


weathermapid = "1058"

#Credentials
server_ip = '10.20.20.113'
server_port = '5443'
username = 'infosim'


# <h2>Get Weather Map from Server and save XML to variable</h2>

# In[7]:


warnings.filterwarnings("ignore")
resp = requests.get("https://"+server_ip+":"+server_port+"/rest/weathermaps/get/" + weathermapid, 
                    verify=False, auth=HTTPBasicAuth(username, getpass.getpass('Enter password:')))
tree = ElementTree.fromstring(resp.content)


# <h2>Adding Alarms as Node Statistics to all Weather Map nodes</h2>

# In[8]:


pw=getpass.getpass('Enter password:');
for child in tree.findall('weathermapnodes/weathermapnode'):
    
	erefID=child.find('elementreference').get('obid')
	erefDOMAIN=child.find('elementreference').get('domain')
	stats=child.find('statistics')
	
	filter = ''
	if erefDOMAIN=="device": 
		filter='<valuetagfilter filtervalue="'+erefID+'"><tagcategory key="Device ID"/></valuetagfilter>'
	if erefDOMAIN=="measurement": 
		filter='<valuetagfilter filtervalue="'+erefID+'"><tagcategory key="Measurement ID"/></valuetagfilter>'
	if erefDOMAIN=="link": 
		filter='<valuetagfilter filtervalue="'+erefID+'"><tagcategory key="Link ID"/></valuetagfilter>'
	filter='<openalarmfilter>'+filter+'</openalarmfilter>'
	print('[Adding alarms for '+erefDOMAIN+' element with ID ' + erefID+']', end='')
	resp=requests.post("https://"+server_ip+":"+server_port+"/rest/events/liveopenalarms", 
                     verify=False, auth=HTTPBasicAuth(username, pw), 
                     data=filter, headers={'Content-Type': 'application/xml'})
	alarms = ElementTree.fromstring(resp.content)
    
	for openalarm in alarms:
		alarminfo = openalarm.find('rootcause').get('info')
		monitorid = openalarm.find('rootcause').get('monitorid')            
		print('R', end='')
		# Create statistic entry
		newentry=ElementTree.SubElement(stats,'statistic',{'showaslabel': 'false', 'type': 'monitorvalue', 'title': '[ROOT CAUSE] '+alarminfo})
		ElementTree.SubElement(newentry,'reference', {'obid': monitorid, 'domain': 'monitor'})
		ElementTree.SubElement(newentry,'time', {'multiplier': '1440', 'type': 'lastminutes', 'timezone': 'Europe/Berlin', 'average': '60000'})
		for symptom in openalarm.findall('symptoms/symptom'):
			alarminfo = symptom.get('info')
			monitorid = symptom.get('monitorid')            
			print('S', end='')
			# Create statistic entry
			newentry=ElementTree.SubElement(stats,'statistic',{'showaslabel': 'false', 'type': 'monitorvalue', 'title': '[SYMPTOM] '+alarminfo})
			ElementTree.SubElement(newentry,'reference', {'obid': monitorid, 'domain': 'monitor'})
			ElementTree.SubElement(newentry,'time', {'multiplier': '1440', 'type': 'lastminutes', 'timezone': 'Europe/Berlin', 'average': '60000'})
	print('')

tree.set('name',tree.get('name')+' (Alarm Statistics)')
        
finalMap = ElementTree.tostring(tree)


# <h2>Adding Extended Weather Map to server as new Weather Map </h2>

# In[9]:


warnings.filterwarnings("ignore")
resp=requests.post("https://"+server_ip+":"+server_port+"/rest/weathermaps/add/", 
                     verify=False, auth=HTTPBasicAuth(username, getpass.getpass('Enter password:')), 
                     data=finalMap, headers={'Content-Type': 'application/xml'})

