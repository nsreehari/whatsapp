from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback

import time
import pickle
import random
import requests

tagqueue = {}

def chitchatresponse(messageBody):

    chitchat_file = open('chitchat.pkl', 'rb')
    chitchat = pickle.load(chitchat_file)
    chitchat_file.close()

    if messageBody.lower() in chitchat.keys():
        return chitchat[messageBody.lower()].strip()
    else:
        return ""

def APIresponse(messageBody):

    urlToHit = "http://relequ07/JarvisTest/api/values/FetchResponse?query=" + messageBody.lower()
    req = requests.get(urlToHit)
    response = req.text[2:-2]
    return response.replace('\\','')
    #return " ".join(req.text.split('"')[1:-1])


def getlovequote():

    lovequote_file = open('lovequotes.pkl', 'rb')
    lovequotes = pickle.load(lovequote_file)
    lovequote_file.close()

    return random.choice(lovequotes)


def getnamestory():
    return "Wait, I will soon have something cool"


def getnew():

    return "I am so fresh on the block ... that's new i guess :)"


def gethelpstring():

    helpstring = "I did not understand that but I have a set of amazing things you can try\n"
    helpstring = helpstring + "#lovequote : For those soulful quotes :)\n"
    helpstring = helpstring + "#name <Friend's name> : Just tell your friend's name and check what happens!\n"
    helpstring = helpstring + "#new : Keep yourself updated with what's new with me\n"
    return helpstring


def parsecapabilities(messageBody):

    keyword = messageBody.split()[0]

    if keyword == "#lovequote":
        return ('text', getlovequote())
    elif keyword == "#name":
        return ('text', getnamestory())
    elif keyword == "#new":
        return ('text', getnew())
    elif keyword in tagqueue.keys():
        return ('readymade', tagqueue(keyword))
    else:
        return ('text', gethelpstring())


def genresponse(messageProtocolEntity):

    messagebody = messageProtocolEntity.getBody()
    if messagebody.startswith("#"):
        (restype, response) = parsecapabilities(messagebody)
    else:
        (restype, response) = APIresponse(messagebody)
        #response = chitchatresponse(messagebody)
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






class EchoLayer(YowInterfaceLayer):

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):

        if messageProtocolEntity.getType() == 'text':
            #time.sleep(0.454)
            print messageProtocolEntity.getBody()
            response = genresponse(messageProtocolEntity)

        elif messageProtocolEntity.getType() == 'media':
            #for now, for all media messages, response is just echoed
            self.onMediaMessage(messageProtocolEntity)

        if response.getType() == 'text':
            self.onTextMessage(messageProtocolEntity)
        elif response.getType() == 'media':
            self.onMediaMessage(response)

        self.toLower(messageProtocolEntity.forward(messageProtocolEntity.getFrom()))
        self.toLower(messageProtocolEntity.ack())
        self.toLower(messageProtocolEntity.ack(True))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())

    def onTextMessage(self,messageProtocolEntity):
        print("Echoing %s to %s" % (messageProtocolEntity.getBody(), messageProtocolEntity.getFrom(False)))


    def onMediaMessage(self, messageProtocolEntity):
        if messageProtocolEntity.getMediaType() == "image":
            print("Echoing image %s to %s" % (messageProtocolEntity.url, messageProtocolEntity.getFrom(False)))

        elif messageProtocolEntity.getMediaType() == "location":
            print("Echoing location (%s, %s) to %s" % (messageProtocolEntity.getLatitude(), messageProtocolEntity.getLongitude(), messageProtocolEntity.getFrom(False)))

        elif messageProtocolEntity.getMediaType() == "vcard":
            print("Echoing vcard (%s, %s) to %s" % (messageProtocolEntity.getName(), messageProtocolEntity.getCardData(), messageProtocolEntity.getFrom(False)))


