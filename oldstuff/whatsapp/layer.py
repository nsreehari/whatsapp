from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_media.protocolentities import RequestUploadIqProtocolEntity, ImageDownloadableMediaMessageProtocolEntity, AudioDownloadableMediaMessageProtocolEntity, LocationMediaMessageProtocolEntity, VCardMediaMessageProtocolEntity, VideoDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.mediauploader import MediaUploader 
from yowsup.layers.protocol_media.mediadownloader import MediaDownloader 
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity 

AZURE_SERVICING = False
AZURE_RECEIVING = True

from serve import Serve
import logging
import time
from copy import copy, deepcopy
import cPickle
import random
import requests
from urllib import urlretrieve
from sys import version_info
import json
from datetime import datetime
from os import unlink
from os.path import isfile, basename
logger = logging.getLogger(__name__)

from azure.servicebus import ServiceBusService, Message
from Queue import Queue

SendQueue = Queue()
CompletedSendQueue = []


class EchoLayer(YowInterfaceLayer):

    def __init__(self):
        super(EchoLayer, self).__init__()
        YowInterfaceLayer.__init__(self)
        self.connected = False
        self.serve = Serve()

        self.bus_service = ServiceBusService(
            service_namespace='msgtestsb',
            shared_access_key_name='RootManageSharedAccessKey',
            shared_access_key_value='Ar9fUCZQdTL7cVWgerdNOB7sbQp0cWEeQyTRYUjKwpk=')

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
                if jsondict['mediatype'] in ["image", "video"]:
                  jsondict['caption'] = recdMsg.getCaption()
                else:
                  jsondict['caption'] = None
            elif jsondict['mediatype'] == 'vcard':
                jsondict['name'] = recdMsg.getName()
                jsondict['carddata'] = recdMsg.getCardData()
            elif jsondict['mediatype'] == "location":
                jsondict['lat'] = recdMsg.getLatitude() 
                jsondict['long'] = recdMsg.getLongitude()
                jsondict['name'] = recdMsg.getLocationName()
                jsondict['url'] = recdMsg.getLocationURL()
                jsondict['encoding'] = "raw"

        
        if jsondict['msgtype'] == 'text':
            logging.info( recdMsg.getBody())

        pushjson = json.dumps(jsondict)
        if AZURE_SERVICING:
            msg = Message(pushjson)
            self.bus_service.send_queue_message('process_incoming', msg)
        else:
            retjson = self.serve.getResponseWrapper(pushjson, recdMsg)
            if retjson:
                SendQueue.put(retjson)

        self.toLower(recdMsg.ack())
        self.toLower(recdMsg.ack(True))

        self.sendMessages()

    def sendMessages(self):
            try:
                sendmsg = SendQueue.get_nowait()
            except:
                return
            
            jsondict = json.loads(sendmsg)
            phonenum = jsondict['phonenum']
            if jsondict['restype'] == 'list':
                ret = jsondict['response']
            else:
                ret = [(jsondict['restype'], jsondict['response'])]
 

            for (restype,response) in ret: 
         
              logging.info(  '%s: Send to %s %s ' % (datetime.now(), phonenum, restype))
              if restype in [ 'image' , 'audio', 'video' ]:
                if 'localfile' in response.keys():
                     path = response['localfile']
                else:
                     mediaurl = response['mediaurl']
                     path = '/tmp/' + basename(mediaurl)
                     if isfile(path):
                         unlink(path)
                     urlretrieve(mediaurl, path)

                if isfile(path):
                  if restype == 'image':
                    self.image_send(phonenum, path, response['caption'])
                  if restype == 'video':
                    #  self.video_send(phonenum, path, response['caption'])
                    # video not supported yet
                    self.message_send(phonenum, "Video Message not supported yet")
                    
                  if restype == 'audio':
                    # self.audio_send(phonenum, path)
                    # video not supported yet
                    self.message_send(phonenum, "Audio Message not supported yet")

              elif restype == 'text':
                self.message_send(phonenum, response)
              elif restype == 'vcard':
                self.vcard_send(phonenum, response['name'],response['carddata'])
              elif restype == 'location':
                self.location_send(phonenum, response['lat'],response['long'],
                       response['name'], response['url'], response['encoding'])

              # handling completed queue in azure service not yet implemented
              #CompletedSendQueue.append(key[1])

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())

        self.sendMessages()


    def logResponse(self, msg):
        if msg.getType() == 'text':
                logging.info(("Echoing %s to %s" % (msg.getBody(), msg.getFrom(False))))
        elif msg.getType() == 'media':
            if msg.getMediaType() in [ "image", "audio", "video"]:
                logging.info(("Echoing %s %s to %s" % (msg.getMediaType(),  msg.url, msg.getFrom(False))))
            
            elif msg.getMediaType() == "location":
                logging.info(("Echoing location (%s, %s) to %s" % (msg.getLatitude(), msg.getLongitude(), msg.getFrom(False))))
            
            elif msg.getMediaType() == "vcard":
                logging.info(("Echoing vcard (%s, %s) to %s" % (msg.getName(), msg.getCardData(), msg.getFrom(False))))


    @ProtocolEntityCallback("success")
    def onSuccess(self, entity):
        self.connected = True
        logger.info("Logged in! Auth")
        self.sendMessages()

    @ProtocolEntityCallback("failure")
    def onFailure(self, entity):
        self.connected = False
        logger.info("Login Failed, reason: %s" % entity.getReason())


    def message_send(self, number, content):
            outgoingMessage = TextMessageProtocolEntity(content.encode("utf-8") if version_info >= (3,0) else content, to = self.normalizeJid(number))
            self.toLower(outgoingMessage)

    def vcard_send(self, number, name, carddata):
            outgoingMessage = VCardMediaMessageProtocolEntity(
                                name, carddata, to = self.normalizeJid(number))
            self.toLower(outgoingMessage)

    def location_send(self, number, lat, lon, name, url, encoding):
            outgoingMessage = LocationMediaMessageProtocolEntity(
                 lat, lon, name, url, encoding, to = self.normalizeJid(number))
            self.toLower(outgoingMessage)

    def image_send(self, number, path, caption = None):
            jid = self.normalizeJid(number)

            entity = RequestUploadIqProtocolEntity(RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE, filePath=path)
            successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, path, successEntity, originalEntity, caption)
            errorFn = lambda errorEntity, originalEntity: self.onRequestUploadError(jid, path, errorEntity, originalEntity)

            self._sendIq(entity, successFn, errorFn)

    def video_send(self, number, path, caption = None):
            jid = self.normalizeJid(number)

            entity = RequestUploadIqProtocolEntity(RequestUploadIqProtocolEntity.MEDIA_TYPE_VIDEO, filePath=path)
            successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, path, successEntity, originalEntity, caption)
            errorFn = lambda errorEntity, originalEntity: self.onRequestUploadError(jid, path, errorEntity, originalEntity)

            self._sendIq(entity, successFn, errorFn)


    def audio_send(self, number, path):
            jid = self.normalizeJid(number)

            entity = RequestUploadIqProtocolEntity(RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO, filePath=path)
            successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, path, successEntity, originalEntity)
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
        elif requestUploadIqProtocolEntity.mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE:
            doSendFn = self.doSendImage
        else:
            doSendFn = self.doSendVideo

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

    def doSendVideo(self, filePath, url, to, ip = None, caption = None):
        entity = VideoDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
        self.toLower(entity)

    def doSendImage(self, filePath, url, to, ip = "127.0.0.1", caption = None):
        logger.info('filepath:%s url:%s to:%s ip:%s caption:%s ' % (filePath, url, to, ip, caption))
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


from yowsup.stacks import YowStack
from yowsup.layers import YowLayerEvent
from yowsup.layers.auth                        import YowCryptLayer, YowAuthenticationProtocolLayer, AuthError
from yowsup.layers.coder                       import YowCoderLayer
from yowsup.layers.network                     import YowNetworkLayer
from yowsup.layers.protocol_messages           import YowMessagesProtocolLayer
from yowsup.layers.protocol_media              import YowMediaProtocolLayer
from yowsup.layers.stanzaregulator             import YowStanzaRegulator
from yowsup.layers.protocol_receipts           import YowReceiptProtocolLayer
from yowsup.layers.protocol_acks               import YowAckProtocolLayer
from yowsup.layers.logger                      import YowLoggerLayer
from yowsup.layers.protocol_iq                 import YowIqProtocolLayer
from yowsup.layers.protocol_calls              import YowCallsProtocolLayer
from yowsup.layers                             import YowParallelLayer
from yowsup.common import YowConstants
from yowsup import env


class YowsupEchoStack(object):
    def __init__(self, credentials, encryptionEnabled = False):
        if encryptionEnabled:
            from yowsup.layers.axolotl                     import YowAxolotlLayer
            layers = (
                EchoLayer,
                YowParallelLayer([YowAuthenticationProtocolLayer, YowMessagesProtocolLayer, YowReceiptProtocolLayer, YowAckProtocolLayer, YowMediaProtocolLayer, YowIqProtocolLayer, YowCallsProtocolLayer]),
                YowAxolotlLayer,
                YowLoggerLayer,
                YowCoderLayer,
                YowCryptLayer,
                YowStanzaRegulator,
                YowNetworkLayer
            )
        else:
            layers = (
                EchoLayer,
                YowParallelLayer([YowAuthenticationProtocolLayer, YowMessagesProtocolLayer, YowReceiptProtocolLayer, YowAckProtocolLayer, YowMediaProtocolLayer, YowIqProtocolLayer, YowCallsProtocolLayer]),
                YowLoggerLayer,
                YowCoderLayer,
                YowCryptLayer,
                YowStanzaRegulator,
                YowNetworkLayer
            )

        self.stack = YowStack(layers)
        self.stack.setCredentials(credentials)

    def start(self):
        self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
        try:
            logging.info("Whatsapp IS STARTING : ReceiveStack");
            self.stack.loop(timeout=1, count=100)
            logging.info("Stopping ... ");
        except AuthError as e:
            logging.info("Authentication Error: %s" % e.message)



