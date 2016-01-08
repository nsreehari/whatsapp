from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_media.protocolentities import RequestUploadIqProtocolEntity, ImageDownloadableMediaMessageProtocolEntity, AudioDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.mediauploader import MediaUploader 
from yowsup.layers.protocol_media.mediadownloader import MediaDownloader 
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity 


from serve import Serve
import logging
import time
from copy import copy
import cPickle
import random
import requests
from urllib import urlretrieve
from sys import version_info
import json

logger = logging.getLogger(__name__)

from azure.servicebus import ServiceBusService, Message, Queue

class EchoLayer(YowInterfaceLayer):

    def __init__(self):
        super(EchoLayer, self).__init__()
        YowInterfaceLayer.__init__(self)
        self.connected = False
        #self.serve = Serve(self.sendMessage)

        self.bus_service = ServiceBusService(
            service_namespace='msgtestsb',
            shared_access_key_name='RootManageSharedAccessKey',
            shared_access_key_value='Ar9fUCZQdTL7cVWgerdNOB7sbQp0cWEeQyTRYUjKwpk=')
        queue_options = Queue()
        queue_options.max_size_in_megabytes = '5120'
        queue_options.default_message_time_to_live = 'PT1M'

        self.bus_service.create_queue('process_incoming', queue_options)
        self.bus_service.create_queue('whatsapp_sender', queue_options)

    @ProtocolEntityCallback("message")
    def onMessage(self, recdMsg):

        jsondict = {'medium': 'whatsapp'}
        jsondict['phonenum'] = recdMsg.getFrom(False)
        jsondict['msgtype'] = recdMsg.getType()
        if jsondict['msgtype'] == 'text':
            jsondict['msgbody'] = recdMsg.getBody()
        
        if jsondict['msgtype'] == 'media':
            jsondict['mediatype'] = recdMsg.getMediaType()
            if jsondict['mediatype'] in ["image", "audio", "video"]:
                jsondict['mediaurl'] = recdMsg.getMediaUrl()

        #jsondict['msg'] = recdMsg # pass whole message for backup just in case:)
        
        if jsondict['msgtype'] == 'text':
            logging.info( recdMsg.getBody())

#        self.serve.getResponse(jsondict)
        msg = Message(json.dumps(jsondict))
        self.bus_service.send_queue_message('process_incoming', msg)

        self.toLower(recdMsg.ack())
        self.toLower(recdMsg.ack(True))

    def sendMessage(self, phonenum, restype, response):
        if restype == 'image':
            self.image_send(phonenum, response)

        elif restype == 'text':
            self.message_send(phonenum, response)

        elif restype == 'readymade':
            self.logResponse(response)
            self.toLower(response.forward(phonenum))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())



    def logResponse(self, msg):
        if msg.getType() == 'text':
                logging.info(("Echoing %s to %s" % (msg.getBody(), msg.getFrom(False))))
        elif msg.getType() == 'media':
            if msg.getMediaType() == "image":
                logging.info(("Echoing image %s to %s" % (msg.url, msg.getFrom(False))))
            
            elif msg.getMediaType() == "location":
                logging.info(("Echoing location (%s, %s) to %s" % (msg.getLatitude(), msg.getLongitude(), msg.getFrom(False))))
            
            elif msg.getMediaType() == "vcard":
                logging.info(("Echoing vcard (%s, %s) to %s" % (msg.getName(), msg.getCardData(), msg.getFrom(False))))


    @ProtocolEntityCallback("success")
    def onSuccess(self, entity):
        self.connected = True
        logger.info("Logged in! Auth")

    @ProtocolEntityCallback("failure")
    def onFailure(self, entity):
        self.connected = False
        logger.info("Login Failed, reason: %s" % entity.getReason())


    def message_send(self, number, content):
            outgoingMessage = TextMessageProtocolEntity(content.encode("utf-8") if version_info >= (3,0) else content, to = self.normalizeJid(number))
            self.toLower(outgoingMessage)

    def image_send(self, number, path, caption = None):
            jid = self.normalizeJid(number)
            entity = RequestUploadIqProtocolEntity(RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE, filePath=path)
            successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, path, successEntity, originalEntity, caption)
            errorFn = lambda errorEntity, originalEntity: self.onRequestUploadError(jid, path, errorEntity, originalEntity)

            self._sendIq(entity, successFn, errorFn)



    def normalizeJid(self, number):
        if '@' in number:
            return number
        elif "-" in number:
            return "%s@g.us" % number

        return "%s@s.whatsapp.net" % number

    ########### callbacks ############

    def onRequestUploadResult(self, jid, filePath, resultRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity, caption = None):

        if requestUploadIqProtocolEntity.mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO:
            doSendFn = self.doSendAudio
        else:
            doSendFn = self.doSendImage

        if resultRequestUploadIqProtocolEntity.isDuplicate():
            doSendFn(filePath, resultRequestUploadIqProtocolEntity.getUrl(), jid,
                             resultRequestUploadIqProtocolEntity.getIp(), caption)
        else:
            successFn = lambda filePath, jid, url: doSendFn(filePath, url, jid, resultRequestUploadIqProtocolEntity.getIp(), caption)
            mediaUploader = MediaUploader(jid, self.getOwnJid(), filePath,
                             resultRequestUploadIqProtocolEntity.getUrl(),
                             resultRequestUploadIqProtocolEntity.getResumeOffset(),
                             successFn, self.onUploadError, self.onUploadProgress, async=False)
            mediaUploader.start()

    def onRequestUploadError(self, jid, path, errorRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity):
        logger.error("Request upload for file %s for %s failed" % (path, jid))

    def onUploadError(self, filePath, jid, url):
        logger.error("Upload file %s to %s for %s failed!" % (filePath, url, jid))

    def onUploadProgress(self, filePath, jid, url, progress):
        return
        #sys.stdout.write("%s => %s, %d%% \r" % (os.path.basename(filePath), jid, progress))
        #sys.stdout.flush()


    def doSendImage(self, filePath, url, to, ip = None, caption = None):
        entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
        self.toLower(entity)

    def doSendAudio(self, filePath, url, to, ip = None, caption = None):
        entity = AudioDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to)
        self.toLower(entity)

    def getMediaMessageBody(self, message):
        if message.getMediaType() in ("image", "audio", "video"):
            return self.getDownloadableMediaMessageBody(message)
        else:
            return "[Media Type: %s]" % message.getMediaType()


    def getDownloadableMediaMessageBody(self, message):
         return "[Media Type:{media_type}, Size:{media_size}, URL:{media_url}]".format(
            media_type = message.getMediaType(),
            media_size = message.getMediaSize(),
            media_url = message.getMediaUrl()
            )


