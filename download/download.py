#!/usr/bin/env python
# coding: utf-8

# <center><img src='https://www.intel.com/content/dam/develop/external/us/en/images/infosim-logo-746616.png' style="width:300px"></center>

# <h1 align="center">StableNet® WeatherMap Transfer - Copy to Filesystem</h1> 
# <h2>Import necessary python modules</h2>

# In[1]:


import warnings
import requests
from requests.auth import HTTPBasicAuth
import getpass
from xml.etree import ElementTree
from pathlib import Path
import os


# <h2>Enter server credentials and the destination path to be used as base</h2>
# 
# It is possible to enter either the cleartext or the hashed password for the credentials. However, using the hash is more secure.

# In[ ]:


server_ip = '10.20.20.46'
server_port = '5443'
username = 'infosim'

pw=getpass.getpass('Enter password-hash for user ' + username + ' on the server:');

path = Path.cwd() # the current path (equal to "pwd" in bash)

print("You are currently in directory " + str(path))
new_directory = input("Enter the destination directory (Relative or absolute path):")
path = Path(new_directory)
if not os.path.exists(path):
	val = input("The path " + str(path) + " does not exist yet. Do you want to create it? (y/n)")
	if val == "y":
		os.makedirs(path)
	else:
		raise SystemExit("Exiting...")


# <h2>Get List of Weather Maps from the Server and save XML to variable</h2>

# In[ ]:


warnings.filterwarnings("ignore")
resp = requests.get("https://"+server_ip+":"+server_port+"/rest/weathermaps/list", 
                    verify=False, auth=HTTPBasicAuth(username, pw))
tree = ElementTree.fromstring(resp.content)
for wmap in tree:
	print('WeatherMap '+wmap.get('obid')+': '+wmap.get('name'))


# <h2>Transfer selected Weather Maps from the Server to the Filesystem</h2>

# In[ ]:


for wmapid in [wmap.get('obid') for wmap in tree]:
	print('Transferring map '+wmapid)
	resp = requests.get("https://"+server_ip+":"+server_port+"/rest/weathermaps/get/" + wmapid, 
	                    verify=False, auth=HTTPBasicAuth(username, pw))
	wmap = ElementTree.fromstring(resp.content)  
	filename = str(wmapid) + '-' + wmap.get('name') + '.xml'
	destination = path / filename
	tree = ElementTree.ElementTree(wmap)
	tree.write(destination)

