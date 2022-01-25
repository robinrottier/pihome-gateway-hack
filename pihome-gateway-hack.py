#!/usr/bin/python3

import os
import re
import socket
import sys
import telnetlib, time, datetime
#from typing import Any
from datetime import datetime

import paho.mqtt.client as paho

# Debug log to screen configuration
dbgLevel = 1 	# 0-off, 1-info, 2-detailed, 3-all

desc = "PiHome Gateway Hack v1"

# Get the local ip address
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('google.com', 0))
ip = s.getsockname()[0]
base_ip = re.search('^[\d]{1,3}.[\d]{1,3}.[\d]{1,3}.', ip)

gatewaytype = "wifi"                            # serial/wifi
gatewaylocation = "192.168.86.31"                     # ip address or serial port of your MySensors gateway
gatewayport = 5003                        # UDP port or bound rate for MySensors gateway
gatewaytimeout = 60                    # Connection timeout in Seconds

maxLoopCount = 60*20					# after 20 mins no responses then exit (so can try again)

if base_ip.group(0) == "192.168.86.":
	mqtt_server = "has1"
else:
	mqtt_server = "mosquitto"
mqtt_port = 1883
mqtt_user = ""
mqtt_pass = ""

mqtt2_server = "192.168.86.38" #"emonpi"
mqtt2_port = 1883
mqtt2_user = "emonpi"
mqtt2_pass = "emonpimqtt2016"

def on_mqtt_publish(client,userdata,result):             #create function for callback
    #log("MQTT data published \n")
    pass

global mqtt_connected
mqtt_connected = 0

def nowstr():
	return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log(msg, end='\n'):
	print(nowstr()+" "+msg, flush=True, end=end)

def on_connect(client, userdata, flags, rc):
   global mqtt_connected
   mqtt_connected = 1
   if dbgLevel >= 1:
	   log("Mqtt connected")
   mqtt_client_publish("pihome/gateway-recv/connected", nowstr())

def on_disconnect(client, userdata, rc):
   global mqtt_connected
   mqtt_connected = 0
   if dbgLevel >= 1:
	   log("Mqtt disconnected")

def on_mqtt_publish2(client,userdata,result):             #create function for callback
    #log("MQTT data published \n")
    pass

global mqtt_connected2
mqtt_connected2 = 0

def on_connect2(client, userdata, flags, rc):
   global mqtt_connected2
   mqtt_connected2 = 1
   if dbgLevel >= 1:
	   log("Mqtt2 connected")

def on_disconnect2(client, userdata, rc):
   global mqtt_connected2
   mqtt_connected2 = 0
   if dbgLevel >= 1:
	   log("Mqtt2 disconnected")

def mqtt_client_publish(topic, msg):
	mqtt_op = "entry"
	try:
		global mqtt_connected
		if mqtt_connected == 0:
			mqtt_op = "pw-set"
			mqtt_client.username_pw_set(mqtt_user, mqtt_pass)
			mqtt_op = "connect"
			mqtt_client.connect(mqtt_server, mqtt_port)
		mqtt_op = "publish"
		mqtt_client.publish(topic, msg)
		mqtt_op = "exit"
	except Exception as e:
		log("MQTT exception on "+mqtt_op)
		log(format(e))

def mqtt_client_publish2(topic, msg):
	if mqtt2_server:
		mqtt_op = "entry2"
		try:
			global mqtt_connected2
			if mqtt_connected2 == 0:
				if mqtt2_user:
					mqtt_op = "pw-set"
					mqtt_client2.username_pw_set(mqtt2_user, mqtt2_pass)
					mqtt_op = "connect"
					mqtt_client2.connect(mqtt2_server, mqtt2_port)
			mqtt_op = "publish"
			mqtt_client2.publish(topic, msg)
			mqtt_op = "exit"
		except Exception as e:
			log("MQTT 2 exception on "+mqtt_op)
			log(format(e))

mqtt_client = paho.Client("pihome-gateway-to-mqtt")
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_publish = on_mqtt_publish
mqtt_client.username_pw_set(mqtt_user, mqtt_pass)
mqtt_client.connect(mqtt_server, mqtt_port)

mqtt_client_publish("pihome/gateway-recv/desc", desc)
mqtt_client_publish("pihome/gateway-recv/started", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

if mqtt2_server:
	mqtt_client2 = paho.Client("pihome-gateway-to-mqtt-2")
	mqtt_client2.on_connect = on_connect2
	mqtt_client2.on_disconnect = on_disconnect2
	mqtt_client2.on_publish = on_mqtt_publish2
	if mqtt2_user:
		mqtt_client2.username_pw_set(mqtt2_user, mqtt2_pass)
	mqtt_client2.connect(mqtt2_server, mqtt2_port)

	#mqtt_client_publish("pihome/gateway-recv/started", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

mqtt_client_summaryTopic = "emon/pihome"

if dbgLevel >= 1:
	log("Local ip:      "+ip)
	log("Base  ip:      "+base_ip.group(0))
	log("Gateway Type:  "+"Wifi/Ethernet")
	log("IP Address:    "+gatewaylocation)
	log("UDP Port:      "+str(gatewayport))

msgs = [ 
	"100;1;1;1;2;0",
	"101;1;1;1;2;0",
	"101;2;1;1;2;0",
	"101;3;1;1;2;0"
]

nodeidMap = {
	"0": "controller",
	"20": "downstairs",
	"21": "upstairs",
	"30": "hotwater",
	}

# map type,subtype to payload meaning
controllermsgmap = {
	"0314": "init",
	"0018": "version",
}

sensormsgmap = {
	"0017": "verion",
	"0018": "version",
	"0124": "min_value",
	"0311": "sensor_type",
	"0312": "sketch_version",
	"0300": "battery_level",
	"0306": "unknown",
}

sensorchildmsgmap = {
	"0003": "max_child_id",
	"0006": "max_child_id",
	"0100": "temperature",
	"0138": "battery_V",
	}

def readFromGatewayLoop():
	while True:
		try:
			if dbgLevel >= 1:
				log("")
				log("Openning gateway...")
			gw = telnetlib.Telnet(gatewaylocation, gatewayport, timeout=gatewaytimeout) # Connect mysensors gateway from MySQL Database
			readFromGateway(gw)
			if dbgLevel >= 1:
				log("Gateway unexpectedly ended")
		except Exception as e:
			if dbgLevel >= 1:
				log("Gateway aborted: "+e)
		finally:
			try:
				gw.close()
			except:
				# if that close fails just ignore it
				if (dbgLevel >= 2):
					log("Gateway close aborted (thats not too bad")
		time.sleep(10)

def readFromGateway(gw):

	mc = 0
	lastwasdot = False
	loopCount = 0

	while 1:
		if len(msgs) > 0:
			wm = msgs.pop(0)
			if dbgLevel >= 2:
				log("Write: "+wm)
			gw.write(wm.encode("utf-8"))

		mc = mc+1

		in_str = gw.read_until(b'\n', timeout=1) # Here is receiving part of the code for Wifi

		now = nowstr()

		in_str = in_str.decode('utf-8')
		in_str = in_str.replace("\n", "")
		in_str = in_str.replace("\r", "")
		if (in_str == ""):
			if dbgLevel >= 2:
				log(".", end="")
			lastwasdot = True
			loopCount = loopCount+1
			mqtt_client_publish("pihome/gateway-recv/loop", now)
			mqtt_client_publish("pihome/gateway-recv/loopCount", loopCount)

			# if 5000 loops without receiving then just exit and let retry happen
			# (maybe socket is blocked or OOM etc)
			if (loopCount >= maxLoopCount):
				log("Too many empty responses ...exiting")
				mqtt_client_publish("pihome/gateway-recv/last_exitDueNoResponse", now)
				sys.exit(1)

		else:
			if dbgLevel >= 2:
				if lastwasdot:
					log("")
				log("Received:"+str(mc)+": '"+in_str+"'")
			lastwasdot = False
			loopCount = 0

			mqtt_client_publish("pihome/gateway-recv/last_update", now)
			mqtt_client_publish("pihome/gateway-recv/last_read", in_str)

			if len(in_str) > 50:
				log("Line length exceeds 50 - ignoring")
				continue

			statement = in_str.split(";")
			if len(statement) != 6:
				log("Line parsing did not find 6 parts - ignoring")
				continue
			
			if not statement[0].isdigit(): #check if received message is right format
				log("Line parsing did not find part 0 numeric - ignoring")
				continue

			node_id = str(statement[0])
			child_sensor_id = int(statement[1])
			message_type = int(statement[2])
			ack = int(statement[3])
			sub_type = int(statement[4])
			payload = statement[5].rstrip() # remove \n from payload

			if dbgLevel >= 3: # Debug log to screen
				log("Node ID:                     "+node_id)
				log("Child Sensor ID:             "+str(child_sensor_id))
				log("Message Type:                "+str(message_type))
				log("Acknowledge:                 "+str(ack))
				log("Sub Type:                    "+str(sub_type))
				log("Pay Load:                    "+str(payload))
			elif dbgLevel >= 2:
				log("Node:"+node_id.rjust(2)+str(child_sensor_id).rjust(3)+" Type:"+message_type+" Ack:"+ack+" Sub_type:"+str(sub_type).rjust(2)+" Payload:"+payload)

			node = nodeidMap.get(node_id)
			if node == None:
				log("Node:",node_id.rjust(2),str(child_sensor_id).rjust(3),"Type:",message_type,"Ack:",ack,"Sub_type:",str(sub_type).rjust(2),"Payload:",payload," !! Unknwon node id")
			else:
				k = str(message_type).rjust(2,"0")+str(sub_type).rjust(2,"0")
				if node == "controller":
					m = controllermsgmap.get(k)
				else:
					if child_sensor_id == 255:
						m = sensormsgmap.get(k)
					else:
						m = sensorchildmsgmap.get(k)

				if m == None:
					log(node,str(child_sensor_id)+" Type:"+str(message_type)+" Ack:"+str(ack)+" Sub_type:"+str(sub_type).rjust(2)+" Payload:"+payload," !! Unknwon msg type")
				else:
					log(node.ljust(10)+" "+str(child_sensor_id).ljust(3)+" "+m.ljust(14)+" "+payload)

					mqtt_client_publish('pihome/sensors/%s/%s' % (node_id, m), payload)
					mqtt_client_publish('pihome/sensors/%s/last_update' % (node_id), now)

					mqtt_client_publish('%s/%s_%s' % (mqtt_client_summaryTopic, node_id, m), payload)

					if node_id != "0":
						if m == "temperature":
							mqtt_client_publish2('%s/%s' % (mqtt_client_summaryTopic, node_id), payload)
							mqtt_client_publish2('%s/%s_0' % (mqtt_client_summaryTopic, node_id), payload)
						else:
							mqtt_client_publish2('%s/%s_%s' % (mqtt_client_summaryTopic, node_id, m), payload)

try:
	readFromGatewayLoop()
except KeyboardInterrupt:
	print('Interrupted')
	try:
		sys.exit(1)
	except SystemExit:
		os._exit(0)