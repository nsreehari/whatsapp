from stack import YowsupEchoStack
import logging
import time

logging.basicConfig()
crphone="919502037758"
crpassword="29X+VHKeeSx+Q83sghUqyccjXY0="
credentials = (crphone, crpassword) # replace with your phone and password

while True:
    print "Sleeping now"
    time.sleep(1.6)
    stack = YowsupEchoStack(credentials, True)
    stack.start()
