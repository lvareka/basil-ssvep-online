import threading
import json
import requests
import base64
import sys


class Netio (threading.Thread):

	def __init__(self): #, name, counter):
		threading.Thread.__init__(self)
		# self.threadID = threadID
		self.ip = '192.168.2.78'
		self.plugToToggle = 1
		#self.name = name
		#self.counter = counter
		self.menu = {
			"name": "Netio",
			"image": "./menu/images/appliances/netios.gif",
			"sub1": {
				"name": "Toggle plug 1",
				"image": "./menu/images/appliances/netio-1.gif",
				"execute": ["Netio",1]
			},
			"sub2": {
				"name": "Toggle plug 2",
				"image": "./menu/images/appliances/netio-2.gif",
				"execute":  ["Netio",2]
			},
			"sub3": {
				"name": "plug 3 and 4",
				"image": "./menu/images/appliances/netio-3+4.gif",
				"sub1": {
					"name": "Toggle plug 3",
					"image": "./menu/images/appliances/netio-3.gif",
					"execute":  ["Netio",3]
				},
				"sub2": {
					"name": "Toggle plug 4",
					"image": "./menu/images/appliances/netio-4.gif",
					"execute":  ["Netio",4]
				},
				"sub3": {
					"name": "",
					"execute": "root"
				},
				"sub4": {
					"name": "",
					"image": "./menu/images/root.gif",
					"execute": "root"
				}
			},
			"sub4": {
				"name": "",
				"image": "./menu/images/root.gif",
				"execute": "root"
			}
		}

	def run(self):
		print("RUN"+str(self.plugToToggle))

	def setIp(self, ip):
		'''
		to correct the ip. If the plug hasnt the 192.168.20.109 address.
		'''
		self.ip = ip

	def execute(self, plugToToggle):
		'''
		To toggle the sockets. Usage: Netio.execute(["Netio", x]) with the socket x in [1,..,4].
		The Netio String is just stuff needed for the menu. Not relevant for the communication with the plug.
		'''
		#plugToToggle = 1
		# plugToToggle = exc[1]
		print("NetioExecute Toggle: " + str(plugToToggle))
		toggleOrder = { "Outputs": [{ "ID":plugToToggle, "Action": 4  }] } #Action: 0 – off, 1 – on, 2 – short off, 3 – short on, 4 – toggle, 5 – no change, (6 – ignore)
		toggleOrderJson = json.dumps(toggleOrder)
		username = "write"
		password = "basil-2020"
		string = username + ":" + password
		writeAutorization = "Basic " + str(base64.b64encode(string.encode("utf-8")), "utf-8")
		headers = {'Authorization' : writeAutorization}
		requests.post('http://'+self.ip+'/netio.json', data=toggleOrderJson, headers= headers)
		return 0

	def getStates (self):
		'''
		Get the state of the netio Plugs. Returns a Json with the states of the sockets.
		'''
		#print("GETSTATES")
		try:
			r = requests.get('http://'+self.ip+'/netio.json')
		except requests.exceptions.RequestException as e:
			print(e)
			sys.exit(2)
		if r.status_code == 200:
			plugs = json.loads(r.content)["Outputs"]
			for i in range(4):
				if plugs[i]["State"]==0:
					pass
		else:
			sys.exit('Netio sockets not reachable!')
		return

	def getMenu(self):
		return self.menu

	def getName(self):
		return self.menu["name"]