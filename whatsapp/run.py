#!/opt/bitnami/python/bin/python
#-*- coding: utf-8 -*-

from stack import YowsupEchoStack
import logging
import time
from datetime import datetime

logging.basicConfig(filename='/tmp/whatsapp.log', level=logging.INFO)
crphone="919502037758"
crpassword="GzBOxFaczlGJF83KPjwSHxnowro="
credentials = (crphone, crpassword) # replace with your phone and password

while True:
    logging.info( '%s' % datetime.now() +  ": Sleeping now")
    time.sleep(1.6)
    stack = YowsupEchoStack(credentials, True)
    stack.start()
