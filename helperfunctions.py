import pickle
import random
import requests

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

def parsecapabilities(messageBody):

    if messageBody.startswith("#lovequote"):
        return getlovequote()
    elif messageBody.startswith("#name"):
        return getnamestory()
    elif messageBody.startswith("#new"):
        return getnew()
    else:
        return gethelpstring()


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





