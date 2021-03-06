#!/opt/bitnami/python/bin/python
#-*- coding: utf-8 -*-

from layer import YowsupEchoStack
import logging
import time
from datetime import datetime
import threading
from azure.servicebus import ServiceBusService, Message, Queue
from os.path import isfile
from os import unlink

from layer import SendQueue, AZURE_RECEIVING

logging.basicConfig(filename='/tmp/whatsapp.log', level=logging.INFO)
crphone="917331134925"
crpassword="dgG1bPd+XXgTgEdYR7exLTTiC5k="
credentials = (crphone, crpassword) # replace with your phone and password

Counter = 100

def watchAzureQueue():
        global Counter
        if AZURE_RECEIVING == False:
            return 

        bus_service = ServiceBusService(
            service_namespace='msgtestsb',
            shared_access_key_name='RootManageSharedAccessKey',
            shared_access_key_value='Ar9fUCZQdTL7cVWgerdNOB7sbQp0cWEeQyTRYUjKwpk=')
        queue_options = Queue()
        queue_options.max_size_in_megabytes = '5120'
        queue_options.default_message_time_to_live = 'PT96H'

        bus_service.create_queue('process_incoming', queue_options)
        bus_service.create_queue('whatsapp_sender', queue_options)
 
        while not isfile('/home/bitnami1/whatsapp/.stopwhatsapp') and Counter > 1:
            msg = bus_service.receive_queue_message('whatsapp_sender', peek_lock=False)
            if msg != None and msg.body:
                logging.info( '%s ' % datetime.now() +  msg.body)
                SendQueue.put(msg.body)
            else:
                logging.info( '%s ' % datetime.now() +  "Empty Azure Queue")
    	        time.sleep(4.6)

        
def watchWhatsApp():
        global Counter
        while not isfile('/home/bitnami1/whatsapp/.stopwhatsapp') and Counter > 0:
    	    logging.info( '%s counter:%s' % (datetime.now(), Counter) +  ": Sleeping now")
            if SendQueue.empty():
    	        time.sleep(1.6)
	    stack = YowsupEchoStack(credentials, True)
	    stack.start()

            Counter -= 1



def main():
    if True and False:
       t = threading.Thread(target=watchAzureQueue, args=())
       t.start()

    watchWhatsApp()

    #for i in range(0, 1000) :
    #   watchAzureQueue()
    #   watchWhatsApp()


while True:
  global Counter
  Counter = 1000
  try:
    main()
    unlink('/home/bitnami1/whatsapp/.stopwhatsapp') 
  except:
    pass
