from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback

import logging
import time
from copy import copy
import cPickle
import random
import requests

logger = logging.getLogger(__name__)

TAGSFILE = 'tagsfile.pkl'

class EchoLayer(YowInterfaceLayer):
    tagqueue = {}
    stagetag = {}
    initdone = False

    def init(self):
        try:
            tagsfile = open(TAGSFILE, "rb")
            self.tagqueue = cPickle.load(tagsfile)
            tagsfile.close()
        except IOError as e:
            pass

    def chitchatresponse(self, messageBody):

        chitchat_file = open('chitchat.pkl', 'rb')
        chitchat = cPickle.load(chitchat_file)
        chitchat_file.close()

        if messageBody.lower() in chitchat.keys():
            return chitchat[messageBody.lower()].strip()
        else:
            return ""

    def APIresponse(self, messageBody):

        urlToHit = "http://relequ07/JarvisTest/api/values/FetchResponse?query=" + messageBody.lower()
        req = requests.get(urlToHit)
        response = req.text[2:-2]
        return response.replace('\\','')
        #return " ".join(req.text.split('"')[1:-1])


    def getquote(self):

        lovequote_file = open('quotes.pkl', 'rb')
        lovequotes = cPickle.load(lovequote_file)
        lovequote_file.close()

        return random.choice(lovequotes)

    def gethelpstring(self):
        helpstring = "I do not understand that. You can try something like 'quote'"
        return helpstring


    def parsecapabilities(self, messageBody, phonenum):

        self.initdone or self.init()

        keyword = messageBody.split()[0]

        if keyword == "quote":
            return ('text', self.getquote())
        elif keyword == "name":
            return ('text', "Wait, I will soon have something cool")
        elif keyword == "new":
            return ('text', "I am so fresh on the block ... that's new i guess :)")
        elif keyword == "savetag":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid SAVETAG')
            tagname = '#' + keywords[1].strip('#')
            if tagname in self.tagqueue.keys():
                return ('text', 'Invalid SAVETAG: Given tag already exists')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        elif keyword in self.tagqueue.keys():
            return ('readymade', self.tagqueue[keyword])
        else:
            return ('text', self.gethelpstring())


    def genresponse(self, messageProtocolEntity):

        NOHANDLEMSG = 'I do not handle these messages'

        phonenum = messageProtocolEntity.getFrom(False)
        logging.info( phonenum)
        logging.info( self.stagetag)
        if phonenum in self.stagetag.keys():
            tagname = self.stagetag[phonenum]

            self.tagqueue[tagname] = copy(messageProtocolEntity)

            #backup the self.tagqueue pending
            output = open(TAGSFILE, 'wb')
            cPickle.dump(self.tagqueue, output)
            output.close()

            del self.stagetag[phonenum]

            return messageProtocolEntity

        if messageProtocolEntity.getType() == 'media':
            #for now, for all media messages, response is just echoed
            #messageProtocolEntity.setBody(NOHANDLEMSG)
            return messageProtocolEntity

        if messageProtocolEntity.getType() == 'text':
            messagebody = messageProtocolEntity.getBody()
            #if messagebody.startswith("#"):
	    if True:
                (restype, response) = self.parsecapabilities(messagebody, phonenum)
            #else:
                #(restype, response) = self.chitchatresponse(messagebody)
                #(restype, response) = self.APIresponse(messagebody)
                #messageProtocolEntity.setBody(NOHANDLEMSG)
                #return messageProtocolEntity

            if (restype == 'text'):
                if response != "" and response != "<no results>" and len(response) < 250:
                    safe_response = response.encode('ascii','ignore')
                    messageProtocolEntity.setBody(safe_response)
                elif len(messagebody.split(' ')) == 1:
                    messageProtocolEntity.setBody(":)")
                else:
                    messageProtocolEntity.setBody("Can I answer every question? Nobody likes a know-it-all!!!")

                return messageProtocolEntity

            if (restype == 'readymade'):
                return response

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):

        if messageProtocolEntity.getType() == 'text':
            #time.sleep(0.454)
            logging.info( messageProtocolEntity.getBody())

        response = self.genresponse(messageProtocolEntity)

        if response.getType() == 'text':
            self.onTextMessage(response)
        elif response.getType() == 'media':
            self.onMediaMessage(response)

        self.toLower(response.forward(messageProtocolEntity.getFrom()))
        self.toLower(messageProtocolEntity.ack())
        self.toLower(messageProtocolEntity.ack(True))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())

    def onTextMessage(self,messageProtocolEntity):
        logging.info(("Echoing %s to %s" % (messageProtocolEntity.getBody(), messageProtocolEntity.getFrom(False))))


    def onMediaMessage(self, messageProtocolEntity):
        if messageProtocolEntity.getMediaType() == "image":
            logging.info(("Echoing image %s to %s" % (messageProtocolEntity.url, messageProtocolEntity.getFrom(False))))

        elif messageProtocolEntity.getMediaType() == "location":
            logging.info(("Echoing location (%s, %s) to %s" % (messageProtocolEntity.getLatitude(), messageProtocolEntity.getLongitude(), messageProtocolEntity.getFrom(False))))

        elif messageProtocolEntity.getMediaType() == "vcard":
            logging.info(("Echoing vcard (%s, %s) to %s" % (messageProtocolEntity.getName(), messageProtocolEntity.getCardData(), messageProtocolEntity.getFrom(False))))




class SendLayer(YowInterfaceLayer):

    #This message is going to be replaced by the @param message in YowsupSendStack construction
    #i.e. list of (jid, message) tuples
    PROP_MESSAGES = "org.openwhatsapp.yowsup.prop.sendclient.queue"
    
    
    def __init__(self):
        super(SendLayer, self).__init__()
        self.ackQueue = []
        self.lock = threading.Condition()

    #call back function when there is a successful connection to whatsapp server
    @ProtocolEntityCallback("success")
    def onSuccess(self, successProtocolEntity):
        self.lock.acquire()
        for target in self.getProp(self.__class__.PROP_MESSAGES, []):
            #getProp() is trying to retreive the list of (jid, message) tuples, if none exist, use the default []
            phone, message = target
            if '@' in phone:
                messageEntity = TextMessageProtocolEntity(message, to = phone)
            elif '-' in phone:
                messageEntity = TextMessageProtocolEntity(message, to = "%s@g.us" % phone)
            else:
                messageEntity = TextMessageProtocolEntity(message, to = "%s@s.whatsapp.net" % phone)
            #append the id of message to ackQueue list
            #which the id of message will be deleted when ack is received.
            self.ackQueue.append(messageEntity.getId())
            self.toLower(messageEntity)
        self.lock.release()

    #after receiving the message from the target number, target number will send a ack to sender(us)
    @ProtocolEntityCallback("ack")
    def onAck(self, entity):
        self.lock.acquire()
        #if the id match the id in ackQueue, then pop the id of the message out
        if entity.getId() in self.ackQueue:
            self.ackQueue.pop(self.ackQueue.index(entity.getId()))
            
        if not len(self.ackQueue):
            self.lock.release()
            logger.info("Message sent")
            raise KeyboardInterrupt()

        self.lock.release()
