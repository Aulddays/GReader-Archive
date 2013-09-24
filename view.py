#!/bin/env python

CR = '''
GReader Archive viewer index generator
Copyright (C) 2013 Aulddays

For documentation (Chinese), visit:
http://live.aulddays.com/tech/13/google-reader-archive-download.htm
For comment, suggestions, etc, @HiZml on Twitter

'''
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
import sys
import os
import httplib, urllib
import random
import socket
import time
from StringIO import StringIO
import gzip
import getpass
try:
	import json
except ImportError:
	import simplejson as json
import xml.etree.ElementTree as ET

# global options
datadir = 'data'

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s')
logging.getLogger().setLevel(logging.INFO)
#logging.getLogger().setLevel(logging.DEBUG)

def fileWrite(filename, content):
	with open(filename, 'w') as f:
		f.write(content)

def fileRead(filename):
	try:
		with open(filename) as f:
			return f.read()
	except IOError:
		return ''

# encode certain chars in  RSS url so that it can be properly interpreted
def urlReplace(url):	# '%' must be replaced at first place
	return url.replace('%', '%25').replace('?', '%3F').replace('&', '%26').replace('=', '%3d')

# clean certain chars in string so that it conforms to valid file/dir naming rules
def dirnameClean(dirname):
	spechars = '/\\?*"<>|:.'
	for char in spechars:
		dirname = dirname.replace(char, '_')
	return dirname

def main():
	
	# Ask for username and password
	raw_input("Press Enter to begin...")
	
	logging.info("Start")
	
	users = []
	for user in os.listdir(datadir):
		if user == 'users.json':
			continue
		logging.info("Processing user %s", user)
		users.append(urllib.quote(user))
		userdir = datadir + '/' + user
		try:
			subs = json.loads(fileRead(userdir + '/subscriptions.json'))
		except:
			logging.error("Failed to read %s. Skip this user.", userdir + '/subscriptions.json')
			continue
		if not subs.has_key('subscriptions'):
			logging.error("%s is invalid, skip this user", userdir + '/subscriptions.json')
			continue

		for sub in subs['subscriptions']:
			logging.info("Processing feed %s (%s)..." % (sub['title'], sub['id']))
			# determine the dir where this subscription was kept (only need first dir if multiple)
			subdircand = []
			feeddir = ''
			for cat in sub['categories']:
				catdir = userdir + '/dir_' + dirnameClean(cat['label'])
				subdir = catdir + '/' + dirnameClean(sub['title'])
				subdircand.append(subdir)
			if len(subdircand) == 0:
				subdir = userdir + '/' + dirnameClean(sub['title'])
				subdircand.append(subdir)
			# check meta info in case of subscriptions having the same name
			for i, subdir in enumerate(subdircand):
				idx = 0
				testdir = subdir
				while os.path.exists(testdir):
					try:
						meta = json.loads(fileRead(testdir + '/meta.json'))
					except ValueError:
						meta = None
					if meta is not None and meta.has_key('id') and meta['id'] == sub['id']:	# right one
						feeddir = testdir
						break
					else:	# not the right one, try next dir
						idx += 1
						testdir = subdir + "_%d" % (idx)
						subdircand[i] = testdir
						continue
				if feeddir != '':	# check result after testing one subdir
					break
			if feeddir == '':	# no proper dir found
				logging.error("No downloaded data for feed %s found. Skip." % (sub['title']))
				continue
			# Seems that
			# sub['GR_dir'] = urllib.quote(feeddir.encode(sys.getdefaultencoding()))
			# is safer, but sadly not working...
			sub['GR_dir'] = urllib.quote(feeddir.encode('utf-8'))
			# process xml files	
			idx = 0
			totalitems = 0
			sub['GR_counts'] = []
			while 1:	# for each xml downloaded
				#content = fileRead(feeddir + "/%03d.xml" % (idx))
				#if content == '':
				#	break
				try:
					tree = ET.parse(feeddir + "/%03d.xml" % (idx))
				except:
					break
				item = len(tree.getroot().findall('{http://www.w3.org/2005/Atom}entry'))
				totalitems += item
				sub['GR_counts'].append(item)
				idx += 1
			sub['GR_total'] = totalitems
			if (idx > 0):
				logging.info("%d items in %d data files found for feed %s" % (totalitems, idx, sub['title']))
			else:
				logging.warning("No valid data file found for feed %s" % (sub['title']))

		fileWrite(userdir + '/subscriptions_viewer.json', json.dumps(subs))
	# for user in os.listdir(datadir):
	fileWrite(datadir + '/users.json', json.dumps(users))
	
	logging.info("Finish")
	return 0


if __name__ == '__main__':
	print CR
	res = 0
	try:
		res = main()
	except KeyboardInterrupt:
		print
		logging.info("Aborted by user")
	raw_input("Press ENTER to exit...")
	exit(res)

