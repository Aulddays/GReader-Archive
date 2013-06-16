#!/bin/env python

CR = '''
Google Reader archive downloader
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

# global options
datadir = 'data'
waittime = 30	# wait 30 seconds after each http request. Otherwise will probably be antispidered

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s')
logging.getLogger().setLevel(logging.INFO)
#logging.getLogger().setLevel(logging.DEBUG)

class GRRequester:
	servers = ["www.google.com"]
	conn = None
	# Enabling gzip saves as much as 60% of downloading time.
	# user-agent is (strangely) required otherwise gzip will not be enabled
	commonheader = {"Host": "www.google.com", 'Accept-Encoding': 'gzip',
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:20.0) Gecko/20100101 Firefox/20.0'}
	user = None
	pwd = None
	auth = None

	def setServers(self, serverlist):
		if not isinstance(serverlist, (list, tuple)):
			logging.error("GRRequester.setServers(): Invalid parameter")
			return 1
		self.servers = serverlist

	# perfoem a request to Google server
	def request(self, path, postdata, tries, useauth = True):
		status = 0
		data = ""
		params = None
		headers = self.commonheader
		if postdata is not None:
			params = urllib.urlencode(postdata)
			headers['Content-type'] = 'application/x-www-form-urlencoded'
		if useauth:
			headers['Authorization'] = 'GoogleLogin auth=' + self.auth
		for i in range(tries):	# retry on network errors
			try:
				if self.conn is None:
					self.reconnect()
				if postdata is not None:
					self.conn.request("POST", path, params, headers)
				else:
					self.conn.request("GET", path, headers = headers)
				response = self.conn.getresponse()
				status = response.status
				data = response.read()
				if response.getheader('Content-Encoding') == 'gzip':
					data = gzip.GzipFile(fileobj=StringIO(data)).read()
			except socket.error, e:
				logging.error("Network error: %s" % (e))
				if self.conn is not None:
					self.conn.close()
					self.conn = None
				time.sleep(waittime)
				continue
			except httplib.BadStatusLine, e:
				logging.error("Network error (BadStatusLine): %s" % (e))
				if self.conn is not None:
					self.conn.close()
					self.conn = None
				time.sleep(waittime)
				continue
			if status == 503:	# antispidered!
				logging.info('Client IP antispidered. wait 1 hour and continue...')
				logging.debug(data)
				time.sleep(3600)
				self.reconnect()
				self.setUser(self.user, self.pwd)	# try relogin
				continue
			break	# should be no exception if arrived here
		return status, data

#	def get(self, path, tries, auth = None):
#		status = 0
#		data = ""
#		headers = self.commonheader
#		if auth is not None:
#			headers['Authorization'] = 'GoogleLogin auth=' + auth
#		for i in range(tries):	# retry 3 times on network errors
#			try:
#				if self.conn is None:
#					self.reconnect()
#				logging.debug("Begin download")
#				self.conn.request("GET", path, headers = headers)
#				response = self.conn.getresponse()
#				status = response.status
#				data = response.read()
#				if response.getheader('Content-Encoding') == 'gzip':
#					data = gzip.GzipFile(fileobj=StringIO(data)).read()
#				logging.debug("End download")
#			except socket.error, e:
#				logging.error("Network error: %s" % (e))
#				if self.conn is not None:
#					self.conn.close()
#					self.conn = None
#				time.sleep(waittime)
#				continue
#			break	# should be no exception if arrived here
#		return status, data

	def reconnect(self):
		if self.conn is not None:
			self.conn.close()
			self.conn = None
		self.conn = httplib.HTTPSConnection(self.servers[random.randint(0, len(self.servers) - 1)], timeout = 30)

	def setUser(self, user, pwd):
		self.auth = None
		status, data = self.request('/accounts/ClientLogin',
			{'Email': user, 'Passwd': pwd, 'service': 'reader', 'accountType': 'HOSTED_OR_GOOGLE'}, 99, False)
		if status != 200 and status != 503:
			logging.error("Login failed. please check network and verify email and/or password")
			self.user = self.pwd = None
			return -1
		for param in data.splitlines():
			if param.startswith('Auth='):
				self.auth = param[5:]	# skip 'Auth='
				logging.debug('Auth: %s' % (self.auth))
		if self.auth is None:	# auth not found, treat as a failure
			logging.error("Auth not found. please verify email and/or password")
			self.user = self.pwd = None
			return -1
		self.user = user
		self.pwd = pwd
		return 0
	
	def relogin(self):
		if self.user is not None and self.pwd is not None:
			self.setUser(self.user, self.pwd)

	def __del__(self):
		if self.conn is not None:
			self.conn.close()

#end of class GRRequester

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

def mkdir(dirname):
	if not os.path.exists(dirname):
		os.makedirs(dirname)

def processWrite(filename, fin, idx, name):
	with open(filename, 'w') as f:
		f.write("%d\n%d\n%s\n" % (fin, idx, name))

def processRead(filename):
	try:
		with open(filename) as f:
			fin = int(f.readline())
			idx = int(f.readline())
			name = f.readline().rstrip()
	except IOError:
		return None, None, None
	return fin, idx, name

def main():
	logging.info("Start")
	
	mkdir(datadir)
	
	requester = GRRequester()
	
	# Try to load custom IPs
	servers = []
	for ip in fileRead('conf/customip.list').splitlines():
		ip = ip.strip()
		if ip != '' and not ip.startswith('#'):
			servers.append(ip)
	if len(servers) > 0:
		logging.warning("Loaded %d custom Google IPs from conf/customip.list. Remove that file if you experience download failure"
			% (len(servers)))
		requester.setServers(servers)
	
	# Ask for username and password
	print "\nIf your Google account uses 2-step verification, please refer to http://live.aulddays.com/tech/13/google-reader-archive-download.htm#advanced"
	user = raw_input("Google Reader Username: ")
	logging.debug(user)
	#os.system("stty -echo")
	#pwd = raw_input("Password (will not display while typing): ")
	#os.system("stty echo")
	pwd = getpass.getpass("Password (will not display while typing): ")
	logging.debug(pwd)
	
	if requester.setUser(user, pwd) != 0:
		logging.error("")
		exit(1)
	
	userdir = datadir + '/' + user
	mkdir(userdir)
	gfin, gNone, gid = processRead(userdir + '/process.dat')
	if gfin is not None:	# have process record
		if gfin != 0: # already finished
			overwrite = raw_input("%s's data has already finished downloading. Start over again? (y/n): " % (user))
			if not (overwrite.startswith('y') or overwrite.startswith('Y') or
				overwrite.startswith('t') or overwrite.startswith('T') or overwrite.startswith('1')):
					logging.info("Finish")
					exit(0)
			gfin = gid = None
		elif len(gid) > 0: 	# partial download found
			while 1:
				overwrite = raw_input("Unfinished download found. Continue (press c) or Start over again (press s)?: ")
				if overwrite.lower().startswith('s'):
					gfin = gid = None
					break
				elif overwrite.lower().startswith('c'):	# continue
					try:
						subs = json.loads(fileRead(userdir + '/subscriptions.json'))
						if not subs.has_key('subscriptions'):
							raise ValueError
						break
					except ValueError:
						logging.error("Invalid unfinished download data. Please delete all downloaded data and try again.")
						exit(1)
		else: # gfin != 0 and len(gid) == 0, invalid data load
			gfin = gid = None
			
	
	if gfin is None:
		logging.info('Retrieving subscribtion list...')
		for i in range(3):
			status, data = requester.request('https://www.google.com/reader/api/0/subscription/list?output=json',
					None, 3)
			if status == 200:
				subs = json.loads(data)
				#print subs
				if subs.has_key('subscriptions'):
					break
			logging.info('%d: %s' % (status, data))
			time.sleep(waittime)
		if status != 200:
			logging.error("Error retrieving subscription list")
			sys.exit(1)
		logging.info('Retrieved %d items of user %s' % (len(subs['subscriptions']), user))
		fileWrite(userdir + '/subscriptions.json', data)
	
	# download each subscription
	for sub in subs['subscriptions']:
		logging.info("Processing %s (%s)..." % (sub['title'], sub['id']))
		if gid != None and sub['id'] != gid:
			print gid, sub['id']
			logging.info('Already downloaded, skip')
			continue
		elif gid is None:
			processWrite(userdir + '/process.dat', 0, 0, sub['id'])
		
		# determin the dir(s) to put this subscription
		subdirs = []
		for cat in sub['categories']:
			catdir = userdir + '/dir_' + dirnameClean(cat['label'])
			mkdir(catdir)
			subdir = catdir + '/' + dirnameClean(sub['title'])
			mkdir(subdir)
			subdirs.append(subdir)
		if len(subdirs) == 0:
			subdir = userdir + '/' + dirnameClean(sub['title'])
			mkdir(subdir)
			subdirs.append(subdir)
		# check meta info in case of subscriptions having the same name
		for i, subdir in enumerate(subdirs):
			idx = 0
			testdir = subdir
			while 1:
				mkdir(testdir)
				try:
					meta = json.loads(fileRead(testdir + '/meta.json'))
				except ValueError:
					meta = None
				if meta is not None and meta.has_key('id'):
					if meta['id'] == sub['id']:	# right one
						break
					else:	# not the right one, try next dir
						idx += 1
						testdir = subdir + "_%d" % (idx)
						subdirs[i] = testdir
						continue
				else:	# meta not found, write current
					fileWrite(testdir + '/meta.json', json.dumps(sub))
					break
		#end of determin the dir(s) to put this subscription
		
		# download contents
		c = ''	# c param in url
		idx = 0
		if gid != None and sub['id'] == gid:	# subscription partially downloaded
			gid = None
			sfin, idx, c = processRead(subdirs[0] + '/process.dat')
			if sfin is not None and sfin != 0:	# finished
				logging.info('Already downloaded, skip')
				continue
			elif sfin is None or c == '':	# none downloaded or invalid data, start over again
				c = ''
				idx = 0
		
		while 1: # download each file of this subscription
			url = 'https://www.google.com/reader/atom/' + urlReplace(sub['id']) + '?n=2000'
			if c != '':
				url += '&c=' + c
			logging.info("downloading %s to %03d.xml" % (url, idx))
			status, data = requester.request(url, None, 99999)
			if status != 200:
				logging.error("Error downloading")
				logging.debug("%d: %s" % (status, data))
				logging.error("Give up this subscription")
				time.sleep(waittime)
				break
			for subdir in subdirs:
				fileWrite(subdir + "/%03d.xml" % (idx), data)
			idx += 1
			sfin = 0
			# extract c
			for i in range(1):
				cb = data.find('<gr:continuation>')
				if cb < 0:	# '<gr:continuation>' not found, finish
					logging.info("Finished %s (%s). %d files downloaded" % (sub['title'], sub['id'], idx))
					sfin = 1
					break
				ce = data.find('</gr:continuation>', cb + 1)
				if ce < 0:	# '</gr:continuation>' not found, error
					logging.error("Parsing content fail. Give up %s (%s)." % (sub['title'], sub['id'], idx))
					sfin = 1
					break
				c = data[cb + len('<gr:continuation>') : ce]
				if c == '':
					logging.info("Finished %s (%s). %d files downloaded" % (sub['title'], sub['id'], idx))
					sfin = 1
				break
			for subdir in subdirs:
				processWrite(subdir + '/process.dat', sfin, idx, c)
			logging.info("Fin and sleep")
			time.sleep(waittime)
			if sfin:
				break
		# end of while 1: # download each file of this subscription
	# end of download each subscription
	processWrite(userdir + '/process.dat', 1, 0, '')
	logging.info("%s finished downloading", user)

	

if __name__ == '__main__':
	print CR
	try:
		main()
	except KeyboardInterrupt:
		print
		logging.info("Exit. You may choose to continue unfinished download next time.")
