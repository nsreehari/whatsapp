#!/opt/bitnami/python/bin/python
#-*- coding: utf-8 -*-

from layer import YowsupEchoStack
import logging
import time
from datetime import datetime
import threading
from azure.servicebus import ServiceBusService, Message, Queue

from layer import SendQueue

logging.basicConfig(filename='/tmp/whatsapp.log', level=logging.INFO)
crphone="919502037758"
crpassword="GzBOxFaczlGJF83KPjwSHxnowro="
credentials = (crphone, crpassword) # replace with your phone and password

def watchAzureQueue():
        bus_service = ServiceBusService(
            service_namespace='msgtestsb',
            shared_access_key_name='RootManageSharedAccessKey',
            shared_access_key_value='Ar9fUCZQdTL7cVWgerdNOB7sbQp0cWEeQyTRYUjKwpk=')
        queue_options = Queue()
        queue_options.max_size_in_megabytes = '5120'
        queue_options.default_message_time_to_live = 'PT96H'

        bus_service.create_queue('process_incoming', queue_options)
        bus_service.create_queue('whatsapp_sender', queue_options)
 
        while True:
            msg = bus_service.receive_queue_message('whatsapp_sender', peek_lock=False)
            if msg != None and msg.body:
                logging.info( '%s ' % datetime.now() +  msg.body)
                SendQueue.put(msg.body)
            else:
                logging.info( '%s ' % datetime.now() +  "Empty Azure Queue")
    	        time.sleep(4.6)

        
def watchWhatsApp():
	while True:
    	    logging.info( '%s' % datetime.now() +  ": Sleeping now")
            if SendQueue.empty():
    	        time.sleep(1.6)
	    stack = YowsupEchoStack(credentials, True)
	    stack.start()

def main():
    tasks = [watchAzureQueue , watchWhatsApp ]
    #data = get_work_data()
    for task in tasks:
        t = threading.Thread(target=task, args=())
        t.start()

main()
