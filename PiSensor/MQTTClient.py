
import time, threading, traceback
# MQTT Library, speficially client
import paho.mqtt.client as mqtt
# Pi GPIO Control
import RPi.GPIO as GPIO

# Equiv of constants
# MQTT Settings
__SERVER__ = "broker.hivemq.com"
__PORT__ = 1883
__MQTT_TOPIC_CONTROL__ = "/testing/dja33/public/control"
__MQTT_TOPIC_MESSAGE__ = "/testing/dja33/public/message"
# MQTT Control messages
__CONTROL_START_MSG__ = "START"
__CONTROL_END_MSG__   = "END"
__CONTROL_ALARM_MSG__ = "ALARM"

# GPIO settings
__GPIO_PIN__ = 16

# Global vars
client = mqtt.Client()
connected = 0 # Connection state, 0 = nothing, 1 = connected

# GPIO (General purpose input/output) settings
GPIOenabled = True # GPIO interrupt enabled, yes or no
GPIObouncetime = 300 # How long to wait before accepting new interrupts (Milliseconds)
GPIOthreshold = 3 # How many consecutive signals we must receive to trigger our state
GPIOdelaycounter = 0.5 # Seconds between each decrement of a 'count'
GPIOtimer = None # Object wrapper for Thread manipulation of counting

class GPIOTimer:

	# defines that these are the ONLY self referencing fields
	# for this class/object
	__slots__ = ("_stage", "_delay", "_thread", "_count")

	def __init__(self):
		self._delay = GPIOdelaycounter
		self._stage = 0
		self._thread = None
		self._count = 5	

	def _count():
		if self._stage > 0:
			time.sleep(GPIObouncetime + self._delay)
			if self._count > 0:
				self._count = self._count - 1
			if self._count == 0:
				self._count = 5
				self._stage = self._stage - 1

	def start(self):
		self.stop()
		self._thread = threading.Thread(target=self._count) 

	def stop(self):
		if not self._thread == None and self._thread.is_alive():
			self._thread.stop()
		self._count = 5
		self._stage = 0

	def increase_sensitivity(self):
		self._delay = self._delay + 0.1
		self._count = self._count + 1

	def decrease_sensitivity(self):
		self._delay = self._delay - 1
		self._count = self._count - 1

	def increment(self):
		print ("Increment Received: {}".format(self._stage))
		self._stage = self._stage + 1
		if self._stage >= GPIOthreshold:
			publish_message(__CONTROL_ALARM_MSG__)
			self._stage = 0
		self._count = 5

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	print("Connected with result code: {}".format(str(rc)))
    	# Subscribing in on_connect() means that if we lose the connection and
    	# reconnect then subscriptions will be renewed.
	client.subscribe(__MQTT_TOPIC_CONTROL__)
	publish_message(__CONTROL_START_MSG__)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	print(msg.topic+" -> "+str(msg.payload))
	# Acknowledge request
	# Mid = message ID
	# Result = Successful or not
	(result, mid) = client.publish(__MQTT_TOPIC_MESSAGE__, "Ackn", 1, True)
	print ("Mid: {}".format(mid))
	print ("Result: {}".format(result))

def on_noise_break(channel):  
	GPIOtimer.increment()

def publish_message(msg):
	(result, mid) = client.publish(__MQTT_TOPIC_MESSAGE__, msg, 1, True)
	print ("Mid: {} | Result: {} | Contents: {}".format(mid, result, msg))

def disable_interrupts():
	print ("Disabling interrupts.")
	GPIO.remove_event_detect(__GPIO_PIN__) 
	GPIOtimer.stop()
	# ...

def enable_interrupts(bounce):
	print ("Enabling interrupts.")
	GPIO.add_event_detect(__GPIO_PIN__, GPIO.FALLING, callback=on_noise_break, bouncetime=bounce)
	GPIOtimer.start()
	# ...

def update_interrupt_settings(bounce):
	disable_interrupts()
	# Let GPIO catch up
	time.sleep(3)
	enable_interrupts(bounce)

# Start 
try:

	print ("Started Program...")
	print ("ControlTopic: {}".format(__MQTT_TOPIC_CONTROL__))
	print ("MessageTopic: {}".format(__MQTT_TOPIC_MESSAGE__))
	client = mqtt.Client()
	print ("Setting callbacks for receiving and connection...")
	client.on_connect = on_connect
	client.on_message = on_message
	print ("Connecting to '{}:{}' ...".format(__SERVER__, __PORT__))
	client.connect(__SERVER__, __PORT__, 60)
	print (" % ...")
	print ("Setting up GPIO pins...")
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(__GPIO_PIN__, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
	GPIOtimer = GPIOTimer()
	enable_interrupts(GPIObouncetime)	

	print ("Ready to receive/transmit. CRTL+C to terminate.")

	# Blocking call that processes network traffic, dispatches callbacks and
	# handles reconnecting.
	client.loop_forever()

# CRTL + C
except KeyboardInterrupt:
	print(" Keyboard interrupt, exiting...") 
except BaseException as e:
	print(" An error occurred. Exiting...") 
	print (e)
	traceback.print_exc()

publish_message(__CONTROL_END_MSG__)
disable_interrupts()
GPIO.cleanup()       # clean up GPIO on CTRL+C exit
quit()
