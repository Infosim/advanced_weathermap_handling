#!/usr/bin/env python
# coding: utf-8

# <center><img src='https://www.intel.com/content/dam/develop/external/us/en/images/infosim-logo-746616.png' style="width:300px"></center>

# # StableNet<sup>®</sup> Weather Map Transfer 
# 
# ## Introduction
# The only non-trivial part for transferring a Weather Map from one StableNet server to another one via REST API (and thus, the only reason for the existence of this script) is handling the references to objects in StableNet.  For each "relevant" tag domain this script allows to define a non-empty and finite list of python regular expressions characterizing tag domains.  If there are two objects from the respective domain (one on each server) whose tag values are equal on all these tag categories, then this script assumes these objects as equal and replaces the references to the first objects with references to the second object.
# 
# The following inputs need to be specified:
# * IP-address, port, username, and password for the two StableNet servers (in "Provide server credentials")
# * Id of the Weather Map that shall be transferred (in "Define input parameters for script")
# * Regular Expressions for relevant tag categories per domain (already preselected, in "Define input parameters for script")

# ## Program

# ### Imports and code definitions
# #### Import necessary python modules

# In[41]:


import warnings
import requests
from requests.auth import HTTPBasicAuth
import getpass
from xml.etree import ElementTree
import xml.dom.minidom # for pretty printing XML
import re # for regular expressions
import json
import sys


# #### Function to request Weather Map from server

# In[42]:


def request_weather_map():
    resp = requests.get(
        "https://{}:{}/rest/weathermaps/get/{}"
        .format(a_server_ip, a_server_port, wmap_id), 
        verify=False, 
        auth=HTTPBasicAuth(a_username, a_pw)
    )
    wmap = ElementTree.fromstring(resp.content)
    if wmap.tag == 'error':
        print('Weather Map with id {} does not exist on server {}:{}'              .format(wmap_id, a_server_ip, a_server_port))
        sys.exit()
    #print (xml.dom.minidom.parseString(resp.content.decode('utf-8')).toprettyxml())
    return wmap


# #### Function to request the tags of a StableNet object (using the REST endpoint /rest/tag/list)

# In[43]:


def request_tags_in_source_system():
    url = "https://{}:{}/rest/tag/list?includeAttributeTags=true"        "&includeDirectTags=false&includeInheritedTags=true"        .format(a_server_ip, a_server_port)
    return requests.post(
        url, 
        verify=False, 
        auth=HTTPBasicAuth(a_username, a_pw), 
        data='<taggablereference domain="{}" obid="{}" />'.format(ref_domain, ref_id), 
        headers = {'Content-Type': 'application/xml'}
    )


# #### Functions to obtain the obid of a StableNet object on the target server (using tag categories that can be specified below and the REST endpoint /rest/tag/query)

# In[51]:


def get_valuetagfilter(cat, val):
    return '<valuetagfilter filtervalue="{}">                <tagcategory key = "{}"/>            </valuetagfilter>'.format(val, cat)
    
def compute_id_in_target_system():
    lookups = []
    for tag_key in tag_keys[ref_domain]:
        pattern = re.compile(
            '<tag id="[^"]*" key="([^"]*{}[^"]*)"'\
            ' value="(?P<tagvalue>[^"]*)"[^>]*>'\
            .format(tag_key.replace('.', '[^"]'))
        )
        lookups.append(pattern.search(a_tags.content.decode('utf-8')))
    flag = True
    for lookup in lookups:
        flag = True if (hasattr(lookup, 'group') and flag) else False
    if not flag:
        return []
    url = 'https://{}:{}/rest/tag/query'.format(b_server_ip, b_server_port)
    filter = ''
    for lookup in lookups:
        tag_key = lookup.group(1)
        tag_value = lookup.group('tagvalue')
        filter += get_valuetagfilter(tag_key, tag_value)
    filter = '<andtagfilter>' + filter + '</andtagfilter>'
    domain_to_be_queried = ref_domain[0].upper() + ref_domain[1:]
    tag_category_to_be_queried = domain_to_be_queried + ' ID' if ref_domain != 'module' else 'Device ' + domain_to_be_queried + ' ID'
    query = '<taggablelistqueryinput domain="{}">                <tagcategories>                    <tagcategory key="{}"/>                </tagcategories>'.format(domain_to_be_queried, tag_category_to_be_queried) +                filter +            '</taggablelistqueryinput>'
    resp = requests.post(
        url, 
        data = query,
        verify = False, 
        auth = HTTPBasicAuth(b_username, b_pw),
        headers = {'Content-Type': 'application/xml'}
    )
    obj = ElementTree.fromstring(resp.content)
    obid = ''
    for element in obj.iter():
        if element.tag == 'tag':
            if element.get('key') == tag_category_to_be_queried:
                obid = element.get('value')
        if obid != '':
            break
    return obid


# ### Enter server credentials & Weather Map ID to be used as base

# ### Actual program code to handle Weather Maps

# <span style="color:red">Select this cell and run in menu: "Run > Run All Above Selected Cell"</span>

# #### Provide server credentials

# In[50]:


#Credentials of server a (source system)
a_server_ip = '10.20.20.21'
a_server_port = '5443'
a_username = 'infosim'
a_pw = getpass.getpass(
    'Enter password for user ' + a_username + ' on server A:'
)

#Credentials of server b (destination system)
b_server_ip = '10.20.20.162'
b_server_port = '5443'
b_username = 'infosim'
b_pw=getpass.getpass(
    'Enter password for user ' + b_username + ' on server B:'
)


# #### Check server credentials and get List of Weather Maps from Server

# In[52]:


warnings.filterwarnings("ignore")
resp = requests.get(
    "https://"+a_server_ip+":"+a_server_port+"/rest/weathermaps/list", 
    verify = False, 
    auth = HTTPBasicAuth(a_username, a_pw))
#print(xml.dom.minidom.parseString(resp.content.decode('utf-8')).toprettyxml())
tree = ElementTree.fromstring(resp.content)
if tree.tag == 'html':
    print('wrong credentials on source server inserted')
    sys.exit()
for wmap in tree:
    wmapname = wmap.get('name') if wmap.get('name') is not None else ''
    print('Weather Map ' + wmap.get('obid') + ': ' + wmapname)
#print (xml.dom.minidom.parseString(resp.content.decode('utf-8')).toprettyxml())


# #### Define input parameters for script
# For each tag domain specify regular expressions for the tag categories which shall be used to identify objects on the two servers.

# In[53]:


wmap_id = '1791'
#tag_keys[dom] must be a list of Python regex
#that specify the tag categories over which the objects
#of the domain dom are identified on both servers.  The
#regex should not contain the symbol '"'.
#Objects are identified iff they agree on all specified
#tag categories.
tag_keys = {}
tag_keys['device'] = ['Device Name']
tag_keys['measurement'] = ['[m,M]easure.* [n,N]ame']
tag_keys['interface'] = ['Device Name', 'Inter.* Name']
tag_keys['monitor'] = ["Moni.* Name"]
tag_keys['link'] = ['[L,l]ink Source Device Name', '[L,l]ink Dest.* Device Name','[L,l]ink Source Inter.* Name', '[L,l]ink Dest.*Inter.* Name']
tag_keys['service'] = ['Service Name']
tag_keys['module'] = ['Device Module Name', 'Device Name']


# #### Transfer the Weather Map

# In[54]:


print('Transferring map '+ wmap_id)
wmap = request_weather_map()
for element in wmap.iter():
    if not element.tag.endswith('reference'):
        continue
    ref_id = element.get('obid')
    ref_domain = element.get('domain')
    a_tags = request_tags_in_source_system()
    target_id = compute_id_in_target_system()
    if target_id != '':
        print('{:22}'.format('Domain: ' + ref_domain) +
                'OBID on Server A: {}, OBID on Server B: {}'
                .format(element.get('obid'), target_id))
        element.set('obid',target_id)
    else: #object not found on target system
        print('{:22}'.format('Domain: ' + ref_domain) +
                'OBID on Server A: {}, not found on Server B'
                .format(element.get('obid')))
        element.set('obid','')
print(wmap.get('name') + ' transferred from ' + a_server_ip + ' to ' + b_server_ip)    
wmap.set('name',wmap.get('name') +' (CLONED FROM ' + a_server_ip + ')')
final_map = ElementTree.tostring(wmap)    
resp = requests.post(
    "https://{}:{}/rest/weathermaps/add/"\
        .format(b_server_ip, b_server_port), 
    verify=False,
    auth=HTTPBasicAuth(b_username, b_pw), 
    data=final_map,
    headers={'Content-Type': 'application/xml'}
)

