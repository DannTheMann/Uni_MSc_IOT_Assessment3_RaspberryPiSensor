
import time
# MQTT Library, speficially client
import paho.mqtt.client as mqtt
# Pi GPIO Control
import RPi.GPIO as GPIO

# Equiv of constants
__SERVER__ = "broker.hivemq.com"
__PORT__ = 1883
__MQTT_TOPIC_CONTROL__ = "/testing/dja33/public/control"
__MQTT_TOPIC_MESSAGE__ = "/testing/dja33/public/message"
__GPIO_PIN__ = 16

# Global vars
client = mqtt.Client()
connected = 0


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	print("Connected with result code "+str(rc))

    	# Subscribing in on_connect() means that if we lose the connection and
    	# reconnect then subscriptions will be renewed.
	client.subscribe(__MQTT_TOPIC_CONTROL__)
	# After subscribing and connecting, we setup GPIO pins
	connected = 11

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
	publishMessage("Noise Alarm!")

def publishMessage(msg):
	(result, mid) = client.publish(__MQTT_TOPIC_MESSAGE__, msg, 1, True)
	print ("Mid: {} | Result: {} | Contents: {}".format(mid, result, msg))

try:

	print ("Started Program...")
	client = mqtt.Client()
	print ("Setting callbacks...")
	client.on_connect = on_connect
	client.on_message = on_message
	print ("Connecting to {}:{} ...".format(__SERVER__, __PORT__))
	client.connect(__SERVER__, __PORT__, 60)
	print (" % ...")
	#client.loop_forever()
#	while connected <= 10:
#		if connected == 10:
#			print ("Failed to connect to MQTT '{}', quitting.".format(__SERVER__))
#			quit()
#		connected = connected + 1
#		time.sleep(1)
	print ("Setting up GPIO pins...")

	GPIO.setmode(GPIO.BOARD)

	# GPIO 16 set up as an input, pulled down, connected to 3V3 on button press  
	GPIO.setup(__GPIO_PIN__, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 

	# when a falling edge is detected on port 17, regardless of whatever   
	# else is happening in the program, the function my_callback will be run  
	GPIO.add_event_detect(16, GPIO.FALLING, callback=on_noise_break, bouncetime=300)

	print ("Ready!")

	# Blocking call that processes network traffic, dispatches callbacks and
	# handles reconnecting.
	# Other loop*() functions are available that give a threaded interface and a
	# manual interface.
	client.loop_forever()

# CRTL + C
except KeyboardInterrupt:
	GPIO.remove_event_detect(__GPIO_PIN__)
	GPIO.cleanup()       # clean up GPIO on CTRL+C exit
	print(" Keyboard interrupt, exiting...")
	quit()
