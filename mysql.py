#!/usr/bin/env python

"""
MySQL external inventory script
=================================

External inventory using a MySQL backend.

Requires a MySQL database using a few predefined tables.
See the mysql.sql file for the tables to import,
modify mysql.ini to match your login credentials.

Extended upon the Cobbler Inventory script.

"""

# Copyright (c) 2015 Productsup GmbH, Yorick Terweijden yt@products-up.de
#
# As it is mostly based on the original Cobbler Dynamic Inventory
# https://github.com/ansible/ansible/blob/devel/contrib/inventory/cobbler.py
# the same license, the GPL-3 applies.
#
######################################################################

import argparse
import configparser
import os
import re
from time import time
import pymysql.cursors

try:
    import json
except ImportError:
    import simplejson as json

from six import iteritems

class MySQLInventory(object):

    def __init__(self):

        """ Main execution path """
        self.conn = None

        self.inventory = dict()  # A list of groups and the hosts in that group
        self.cache = dict()  # Details about hosts in the inventory

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Cache
        if self.args.refresh_cache:
            self.update_cache()
        elif not self.is_cache_valid():
            self.update_cache()
        else:
            self.load_inventory_from_cache()
            self.load_cache_from_cache()

        data_to_print = ""

        # Data to print
        if self.args.host:
            data_to_print += self.get_host_info()
        else:
            self.inventory['_meta'] = { 'hostvars': {} }
            for hostname in self.cache:
                self.inventory['_meta']['hostvars'][hostname] = self.cache[hostname]
            data_to_print += self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def _connect(self):
        if not self.conn:
            self.conn = pymysql.connect(**self.myconfig)

    def is_cache_valid(self):
        """ Determines if the cache files have expired, or if it is still valid """

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_inventory):
                    return True

        return False

    def read_settings(self):
        """ Reads the settings from the mysql.ini file """

        config = configparser.ConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/mysql.ini')

        self.myconfig = dict(config.items('server'))
        if 'port' in self.myconfig:
            self.myconfig['port'] = config.getint('server', 'port')

        # Cache related
        cache_path = config.get('config', 'cache_path')
        self.cache_path_cache = cache_path + "/ansible-mysql.cache"
        self.cache_path_inventory = cache_path + "/ansible-mysql.index"
        self.cache_max_age = config.getint('config', 'cache_max_age')

        # Other config
        try:
		    self.inventory_hostname = config.get('config', 'inventory_hostname') 
        except:
            self.inventory_hostname = 'host'
        try:
		    self.inventory_groups = config.get('config', 'inventory_groups') 
        except:
            self.inventory_groups = 'immediate'

    def parse_cli_args(self):
        """ Command line argument processing """

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on MySQL')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to MySQL (default: False - use cache files)')
        self.args = parser.parse_args()

    def process_group(self, groupname):
        # Fetch the Group info
        if groupname not in self.inventory:
            cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            sql = "SELECT variables FROM `group` WHERE name = %s"
            cursor.execute(sql, groupname)
            groupinfo = cursor.fetchone()
            self.inventory[groupname] = dict()
            if groupinfo['variables'] and groupinfo['variables'].strip():
                try:
                   self.inventory[groupname]['vars'] = json.loads(groupinfo['variables'])
                   self.inventory[groupname]['hosts'] = list()
                except:
                   raise Exception('Group does not have valid JSON', groupname, groupinfo['variables'])

            if 'vars' not in self.inventory[groupname]:
               self.inventory[groupname] = list()

    def update_cache(self):
        """ Make calls to MySQL and save the output in a cache """

        self._connect()
        self.hosts = dict()

        # Fetch the systems
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT * FROM inventory;"
        cursor.execute(sql)
        data = cursor.fetchall()

        for host in data:
            self.process_group(host['group'])

            inventory_hostname = host[self.inventory_hostname]
            if 'hosts' in self.inventory[host['group']]:
                self.inventory[host['group']]['hosts'].append(inventory_hostname)
            else:
                self.inventory[host['group']].append(inventory_hostname)

            dns_name = host['host']
            if host['host_vars'] and host['host_vars'].strip():
                try:
                   cleanhost = json.loads(host['host_vars'])
                except:
                   raise Exception('Host does not have valid JSON', host['host'], host['host_vars'])
            else:
                cleanhost = dict()
            cleanhost['ansible_host'] = dns_name

            self.cache[inventory_hostname] = cleanhost
            self.inventory = self.inventory

        # first fetch all the groups to check for possible childs
        if self.inventory_groups == 'all':
            gsql = """SELECT * FROM children_all;"""
        else:
            gsql = """SELECT * FROM children;"""

        cursor.execute(gsql)
        groupdata = cursor.fetchall()

        for group in groupdata:
            self.process_group(group['parent'])
            if 'hosts' not in self.inventory[group['parent']]:
                self.inventory[group['parent']] = {'hosts': self.inventory[group['parent']]}

            if 'children' not in self.inventory[group['parent']]:
                self.inventory[group['parent']]['children'] = list()

            self.inventory[group['parent']]['children'].append(group['child'])

        # cleanup output
        for group in self.inventory:
            if 'hosts' in self.inventory[group] and self.inventory[group]['hosts'] == list():
                del self.inventory[group]['hosts']

        self.write_to_cache(self.cache, self.cache_path_cache)
        self.write_to_cache(self.inventory, self.cache_path_inventory)

    def get_host_info(self):
        """ Get variables about a specific host """

        if not self.cache or len(self.cache) == 0:
            # Need to load index from cache
            self.load_cache_from_cache()

        if not self.args.host in self.cache:
            # try updating the cache
            self.update_cache()

            if not self.args.host in self.cache:
                # host might not exist anymore
                return self.json_format_dict({}, True)

        return self.json_format_dict(self.cache[self.args.host], True)

    def push(self, my_dict, key, element):
        """ Pushed an element onto an array that may not have been defined in the dict """

        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]

    def load_inventory_from_cache(self):
        """ Reads the index from the cache file sets self.index """

        cache = open(self.cache_path_inventory, 'r')
        json_inventory = cache.read()
        self.inventory = json.loads(json_inventory)

    def load_cache_from_cache(self):
        """ Reads the cache from the cache file sets self.cache """

        cache = open(self.cache_path_cache, 'r')
        json_cache = cache.read()
        self.cache = json.loads(json_cache)

    def write_to_cache(self, data, filename):
        """ Writes data in JSON format to a file """
        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        """ Converts 'bad' characters in a string to underscores so they can be used as Ansible groups """

        return re.sub("[^A-Za-z0-9\-]", "_", word)

    def json_format_dict(self, data, pretty=False):
        """ Converts a dict to a JSON object and dumps it as a formatted string """

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

MySQLInventory()
