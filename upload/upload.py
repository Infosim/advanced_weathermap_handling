#!/usr/bin/env python
# coding: utf-8

# <center><img src='https://www.intel.com/content/dam/develop/external/us/en/images/infosim-logo-746616.png' style="width:300px"></center>

# <h1 align="center">StableNet® WeatherMap Restore from Filesystem (XML)</h1> 
# <h2>Import necessary python modules</h2>

# In[ ]:


import warnings
import requests
from requests.auth import HTTPBasicAuth
import getpass
from xml.etree import ElementTree
from pathlib import Path
import os, glob
import io
import re
import PIL.Image as Image
import shutil


# <h2>Enter server credentials and the source filesystem path to be used as base</h2>
# 
# It is possible to enter either the cleartext or the hashed password for the credentials. However, using the hash is more secure.

# In[ ]:


server_ip = '10.20.20.113'
server_port = '5443'
username = 'infosim'

pw=getpass.getpass('Enter password-hash for user ' + username + ' on the server:');

path = Path.cwd() # the current path (equal to "pwd" in bash)

print("You are currently in directory " + str(path))
new_directory = "backup_" + server_ip #input("Enter the destination directory (Relative or absolute path):")
path = Path(new_directory)
if not os.path.exists(path):
	raise SystemExit("The path " + str(path) + " does not exist yet. Please provide an existing folder to read in the Weathermaps from the filesystem")
else:
	print("The path " + str(path) + " could be found and will be used as base for Weathermap restore")


# <h2>Get List of Weather Maps from the Filesystem and print name and id</h2>

# In[ ]:


for filename in sorted(os.listdir(path)):
	if not filename.endswith('.xml'): continue
	fullname = os.path.join(path, filename)
	wmap = ElementTree.parse(fullname).getroot()
	if 'name' in wmap.attrib: 
		print('WeatherMap '+wmap.get('obid')+': '+wmap.get('name'))
	else:
		wmap.set('name',wmap.get('obid'))
		print('WeatherMap '+wmap.get('obid'))


# <h2>Restore selected Weather Map to the Server</h2>

# In[ ]:


for wmapid in [1041]:
	map = glob.glob(os.path.join(path,str(wmapid)+"*"+".xml"))    
	if len(map)>0:            
		print('Restoring map '+str(wmapid)+" from file "+ map[0])
		wmap = ElementTree.parse(map[0]).getroot()
		warnings.filterwarnings("ignore")
		resp = requests.post("https://{}:{}/rest/weathermaps/add/"		.format(server_ip, server_port), 
		verify=False,
		auth=HTTPBasicAuth(username, pw), 
		data=ElementTree.tostring(wmap),
		headers={'Content-Type': 'application/xml'}
		)

