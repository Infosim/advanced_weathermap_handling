#!/usr/bin/env python
# coding: utf-8

# <center><img src='https://www.intel.com/content/dam/develop/external/us/en/images/infosim-logo-746616.png' style="width:300px"></center>

# # StableNet<sup>®</sup> Weather Map Statistics

# ## Introduction
# This script adds statistics to Weather Maps when given certain parameters as input over a CSV file.  We describe the form the input file has to be of and the script's workflow with an example.  It is important to note that the titles of columns in the input CSV file may not differ from those in the example file.  However, the order of the columns may vary.

# ## Example

# ## Program

# ### Imports and code definitions

# #### Import necessary python modules

# In[ ]:


import warnings
import requests
from requests.auth import HTTPBasicAuth
import getpass
from xml.etree import ElementTree
import xml.dom.minidom # for pretty printing XML
import re # for regular expressions
import json
import csv
import sys


# #### Function to normalize CSV entries

# In[ ]:


def normalized_entry(entry, i):
    if cols[i] == 'lastvalue or measurementstat':
        return 'lastvalue' if entry.lower().startswith('l') else 'measurementstat'
    if cols[i] == 'statistic default state':
        return entry if entry != '' else '0'
    if cols[i] == 'showaslabel':
        return 'true' if entry.lower().startswith('t') else 'false'
    if cols[i] == 'metricscale add':
        return entry if entry != '' else '0'
    if cols[i] == 'metricscale multiply':
        return entry if entry != '' else '1'
    if cols[i] == 'time multiplier':
        return entry if entry != '' else '1'
    if cols[i] == 'time type':
        return entry if entry != '' else 'lastmonths'
    if cols[i] == 'offset multiplier':
        return entry if entry != '' else '0'
    if cols[i] == 'offset type':
        return entry if entry != '' else 'lastmonths'
    if cols[i] == 'node or link':
        return 'node' if entry.lower().startswith('n') else 'link'
    if cols[i] == 'source or destination':
        if entry == '':
            return ''
        return 'source' if entry.lower().startswith('s') else 'destination'
    if cols[i] == 'domain':
        if entry.lower().startswith('d'):
            return 'device'
        if entry.lower().startswith('i'):
            return 'interface'
        if entry.lower().startswith('me'):
            return 'measurement'
        if entry.lower().startswith('mon'):
            return 'monitor'
        if entry.lower().startswith('mod'):
            return 'module'
        return 'service'
    return entry


# #### Function to create and append statistic tag to Weather Map object (using \<statistics\>)

# In[ ]:


def append_stat_tag():
    stat_attrs = {'metrickey': metric_key, 'type': stat_props['lastvalue or measurementstat'], 
                 'title': title, 'ranges': stat_props['statistic ranges'], 
                 'defaultstate': stat_props['statistic default state'],
                 'showaslabel':stat_props['showaslabel']}
    statistic = ElementTree.SubElement(
        el.find('statistics'), 'statistic', stat_attrs
    )
    ElementTree.SubElement(
        statistic, 'reference', {'obid': meas_id, 'domain': 'measurement'}
    )
    ElementTree.SubElement(
        statistic, 'metricscale', 
        {
            'add': stat_props['metricscale add'], 
            'multiply': stat_props['metricscale multiply']
        }
    )
    if stat_props['lastvalue or measurementstat'] == 'measurementstat':
        ElementTree.SubElement(
            statistic, 'time', 
            {
                'multiplier': stat_props['time multiplier'], 
                'type': stat_props['time type'], 
                'average': stat_props['time average'],
                'offsetmultiplier': stat_props['offset multiplier'], 
                'offsettype': stat_props['offset type']
            }
        )


# #### Functions to obtain measurement for given Weather Map object (using /rest/tag/query)

# In[ ]:


def get_andtagfilter_with_two_valuetagfilters(cat1, val1, cat2, val2):
    return '<andtagfilter>                <valuetagfilter filtervalue="{}">                    <tagcategory key = "{}"/>                </valuetagfilter>                <valuetagfilter filtervalue="{}">                    <tagcategory key = "{}"/>                </valuetagfilter>            </andtagfilter>'.format(val1, cat1, val2, cat2)

def get_andtagfilter_with_valuetagfilter_and_patterntagfilter(cat1, val, cat2, pat):
    return '<andtagfilter>                <valuetagfilter filtervalue="{}">                    <tagcategory key = "{}"/>                </valuetagfilter>                <patterntagfilter filterpattern="{}">                    <tagcategory key = "{}"/>                </patterntagfilter>            </andtagfilter>'.format(val, cat1, pat, cat2)

def compute_measurement():
    url = 'https://{}:{}/rest/tag/query'.format(server_ip, server_port)
    filter = ''
    if obj_domain == 'device': 
        #Here we consider Ping measurements separately because
        #the name of the measurement typically is the device name
        if stat_props['measurement pattern'] == 'Ping measurement':
            filter +=  get_andtagfilter_with_two_valuetagfilters(
                'Device ID', obj_id, 'Measurement Type', 'Ping')
        else:
            filter += get_andtagfilter_with_valuetagfilter_and_patterntagfilter(
                'Device ID', obj_id, 'Measurement Name', stat_props['measurement pattern'])
    if obj_domain == 'interface':
        #Here we consider SNMP Interface measurements separately because
        #the name of the measurement typically is the device name
        if stat_props['measurement pattern'] == 'Interface measurement':
            filter += get_andtagfilter_with_two_valuetagfilters(
                'Interface ID', obj_id, 'Measurement Type', 'SNMP Interface')
        else:
            filter += get_andtagfilter_with_valuetagfilter_and_patterntagfilter(
                'Interface ID', obj_id, 'Measurement Name', stat_props['measurement pattern'])
    if obj_domain == 'measurement':
        filter += get_andtagfilter_with_valuetagfilter_and_patterntagfilter(
            'Measurement ID', obj_id, 'Measurement Name', stat_props['measurement pattern'])
    if obj_domain == 'monitor':
        filter += get_andtagfilter_with_valuetagfilter_and_patterntagfilter(
            'Monitor ID', obj_id, 'Measurement Name', stat_props['measurement pattern'])
    if obj_domain == 'module':
        filter += get_andtagfilter_with_valuetagfilter_and_patterntagfilter(
            'Device Module ID', obj_id, 'Measurement Name', stat_props['measurement pattern'])
    if obj_domain == 'service':
        filter += get_andtagfilter_with_valuetagfilter_and_patterntagfilter(
            'Service ID', obj_id, 'Measurement Name', stat_props['measurement pattern'])
    query = '<taggablelistqueryinput domain="Measurement">                <tagcategories>                    <tagcategory key="Measurement ID"/>                    <tagcategory key="Measurement Name"/>                    </tagcategories>' +                filter +            '</taggablelistqueryinput>'
    resp = requests.post(
        url, 
        data = query,
        verify = False, 
        auth = HTTPBasicAuth(username, pw),
        headers = {'Content-Type': 'application/xml'}
    )
    meas = ElementTree.fromstring(resp.content)
    meas_id = ''
    meas_name = ''
    for element in meas.iter():
        if element.tag == 'tag':
            if element.get('key') == 'Measurement ID':
                meas_id = element.get('value')
            elif element.get('key') == 'Measurement Name':
                meas_name = element.get('value')
        if meas_id != '' and meas_name != '':
            break
    return (meas_id, meas_name)


# #### Function to obtain metric key and metric name (making use of /rest/measurements/metric/{id})

# In[ ]:


def compute_metric_key_and_name():
    resp = requests.get(
            "https://" + server_ip + ":" + server_port + 
            "/rest/measurements/metric/" + meas_id, 
            verify=False, 
            auth=HTTPBasicAuth(username, pw)
        )
    print("https://" + server_ip + ":" + server_port + 
            "/rest/measurements/metric/" + meas_id)
    metrics = ElementTree.fromstring(resp.content)
    metric_key = ''
    pat1 = re.compile(stat_props['metricname'])
    pat2 = re.compile(stat_props['metricunit'])
    for metric in metrics.iter():
        if pat1.search(str(metric.get('name'))):
            if pat2.search(str(metric.get('unit'))):
                if stat_props['lastvalue or measurementstat'] == 'measurementstat':
                    metric_key = stat_props['aggregate'] + '_'
                return (metric_key + metric.get('key'), metric.get('name'))
    return ('','')


# #### Function to generate a standard statistic title (unless it is provided in the CSV file)

# In[ ]:


def compute_statistic_title(input_title, meas_name, metric_name):
    title = ''
    if input_title != '':
        return input_title
    else:
        if stat_props['node or link'] == 'link':
            title = 'Src ' if stat_props['source or destination'] == 'source' else 'Dest '
        title += meas_name
        return title + metric_name


# #### Function to request the Weather Map object as XML (using /rest/weathermaps/get/{id})

# In[ ]:


def request_weathermap():
    url = "https://{}:{}/rest/weathermaps/get/{}".format(server_ip, server_port, wmap_id)
    resp = requests.get(
        url,
        verify=False, 
        auth=HTTPBasicAuth(username, pw)
    )
    #print (xml.dom.minidom.parseString(resp.content.decode('utf-8')).toprettyxml())
    wmap = ElementTree.fromstring(resp.content)
    if wmap.tag == 'error':
        print('weathermap with id {} does not exist on server {}:{}'            .format(wmap_id, server_ip, server_port))
        sys.exit()
    # if flag is set, delete all existing statistics
    if delete_existing_stats:
        for el in wmap.iter():
            if el.tag == 'statistics':
                el.clear()
    return wmap


# #### Function to check whether current object is relevant for the current line of the CSV file

# In[ ]:


def relevance_check():
    if obj_domain != stat_props['domain']:
        return False
    #test whether the name of the weathermapnode matches stat_props['pattern for node name']
    if stat_props['pattern for node name'] == '' or el.tag != 'weathermapnode':
        return True
    pattern = re.compile(stat_props['pattern for node name'])
    if pattern.search(str(el.get('name'))) is None:
        return False
    return True


# ### Actual program code to handle Weather Maps

# <span style="color:red">Select this cell and run in menu: "Run > Run All Above Selected Cell"</span>

# #### Provide server credentials

# In[ ]:


#Credentials of server
server_ip = '10.20.20.113'
server_port = '5443'
username = 'infosim'
pw=getpass.getpass('Enter password for user ' + username + ' on server A:')


# #### Check server credentials and get List of Weather Maps from Server

# In[ ]:


warnings.filterwarnings("ignore")
resp = requests.get(
    "https://"+server_ip+":"+server_port+"/rest/weathermaps/list", 
    verify=False, 
    auth=HTTPBasicAuth(username, pw)
)
tree = ElementTree.fromstring(resp.content)
if tree.tag == 'html':
    print('wrong credentials inserted')
    sys.exit()
for wmap in tree:
    wmap_name = wmap.get('name') if wmap.get('name') is not None else ''
    print('WeatherMap ' + wmap.get('obid') + ': ' + wmap_name)


# #### Define input parameters for script

# In[ ]:


delete_existing_stats = True#if True, all existing statistics are deleted from the weathermap
wmap_suffix = '_TREND';
wmap_id = '1058'
csv_file_name = 'input_node_trend.csv'


# #### Read in statistic configuration from CSV file

# In[ ]:


inputs = []
cols = []
with open(csv_file_name, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=';', quotechar='\'')
    first_line = True
    for row in reader:
        if not first_line:
            inputs += [{}]
            for i in range(0, len(row)):
                inputs[-1][cols[i]] = normalized_entry(row[i], i)
        else:
            for entry in row:
                cols += [entry]
            first_line = False
        if len(row) != len(cols):
            print('Malformed csv file: '
                  'not all lines of same length')
            break
for j in range(0, len(inputs)):
    print('Line: ' + str(j+1))
    for i in range(0, len(cols)):
        print('\t\t' + cols[i] + ': ' + inputs[j][cols[i]])


# #### Add statistics to Weather Map XML and post it to server

# In[ ]:


wmap = request_weathermap() # Request Weather Map with wmap_id from server previously defined
i = 0
for stat_props in inputs:
    i += 1
    print('Processing line {} of input file'.format(str(i)))
    for el in wmap.findall('weathermapnodes/weathermapnode')        + wmap.findall('weathermaplinks/weathermaplink'):
        reference_tag = 'elementreference'
        if stat_props['node or link'] == 'link':
            reference_tag = 'sourcereference' if stat_props['source or destination'] == 'source'                else 'destinationreference'
        obj_ref = el.find(reference_tag)
        if not hasattr(obj_ref, 'get'):
            continue
        obj_id = obj_ref.get('obid')
        obj_domain = obj_ref.get('domain')
        if not relevance_check():
            continue
        (meas_id, meas_name) = compute_measurement()
        if meas_id == '' or meas_name == '':
            print('{:15}'.format(obj_domain + ' ' + obj_id) + 'Requested measurement not found')
            continue
        (metric_key, metric_name) = compute_metric_key_and_name()           
        if metric_key == '':
            print('{:15}'.format(obj_domain + ' ' + obj_id) + ': Requested metric not found')
            continue
        title = compute_statistic_title(stat_props['statistic title'],meas_name, metric_name)
        append_stat_tag()
        print('{:15}'.format(obj_domain + ' ' + obj_id) + ' Statistic added')
wmap.set('name', wmap.get('name') + wmap_suffix)
#print(xml.dom.minidom.parseString(ElementTree.tostring(wmap)).toprettyxml())
resp = requests.post(
    "https://" + server_ip + ":" + server_port + "/rest/weathermaps/add/", 
    verify = False, 
    auth = HTTPBasicAuth(username, pw), 
    data = ElementTree.tostring(wmap), 
    headers = {'Content-Type': 'application/xml'}
)
#print (xml.dom.minidom.parseString(resp.content.decode('utf-8')).toprettyxml())

