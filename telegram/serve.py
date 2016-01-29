
import logging
import time
from copy import copy, deepcopy
import cPickle
import random
import json
#import requests
from urllib import urlretrieve
from sys import version_info
from datetime import datetime
from os.path import isfile, basename
from subprocess import call

logger = logging.getLogger(__name__)

TESTSCRIPT = ''

def stitchmessage(j, phonenum, tagname):
     logger.info("Attaching content for " + tagname)
     logger.info(j)
     if j['msgtype'] == 'text':
         stt = ['text', j['msgbody']]
         return stt
     elif j['msgtype'] == 'media':
       if j['mediatype'] in ['image', 'audio', 'video'] :
         url = j['mediaurl']
         savepath = '/tmp/serve/repo_' + basename(url)
         if j['medium'] == 'whatsapp':
             urlretrieve(url, savepath)
         if isfile(savepath):
             stt = [j['mediatype'], {'localfile':savepath, 'caption': j['caption']}]
             return stt
         else:
             if 'cacheinfo' in j.keys():
                  jk = j['cacheinfo']
             else:
                  jk = ''
             stt = [j['mediatype'], {'cacheinfo':jk, 'mediaurl':j['mediaurl'], 'caption': j['caption']}]
             return stt
       elif j['mediatype'] in ['location']:
         stt = [j['mediatype'], {'lat':j['lat'], 'long':j['long'], 'encoding':j['encoding'], 'name':j['name'], 'url':j['url']}]
         return stt
       elif j['mediatype'] in ['vcard']:
         stt = [j['mediatype'], {'name':j['name'], 'carddata':j['carddata']}]
         return stt


class Sites():
    def sitestructure(self, phonenum, isevent, isteam):
        base = { 'tags': {}, 'phones':[phonenum] }
        if isevent:
            base['eventdata'] = {'registerlist': set()}
        if isteam:
            base['teamdata'] = {'memberlist': set()}
        return  base

    def __init__(self, cbfn=None):
        global TESTSCRIPT
        self.TAGSFILE = '/tmp/serve/' + TESTSCRIPT + 'tags_sites.pkl'
        self.stagetag = {}
        self.topickle = {'sites': {}, 'employees':{}}

        self.sitehandle = lambda n : '@%s' % n

        try:
            tagsfile = open(self.TAGSFILE, "rb")
            self.topickle = cPickle.load(tagsfile)
            tagsfile.close()
            self.employees = self.topickle['employees']
        except:
            self.topickle['employees'] = {}
            self.employees = self.topickle['employees']
            pass

        self.sites = self.topickle['sites']

    def flushpickle(self):
        output = open(self.TAGSFILE, 'wb')
        cPickle.dump(self.topickle, output)
        output.close()

    def preparse(self, j, phonenum):
      
        if phonenum in self.stagetag.keys():
            (cmd, site, tagname) = self.stagetag[phonenum]

            stt = stitchmessage(j, phonenum, tagname)
            if site:
                siteStruct = self.sites[site]
                siteTags = siteStruct['tags']
                siteAllow = siteStruct['phones']

                if cmd == "append":
                    if tagname in siteTags.keys():
                        siteTags[tagname].append(stt)
                        rettext = 'Successfully appended to tag:' + tagname
                    else:
                        siteTags[tagname] = [ stt ]
                        rettext = 'Successfully attached to tag:' + tagname
                else: 
                    siteTags[tagname] = [ stt ]
                    rettext = 'Successfully attached to tag:' + tagname
            else:
                allEmployees = self.employees
                if tagname == 'next' and cmd == 'broadcast':
                    (rst, rsp) = stt
                    X = {}
                    X['employees'] = allEmployees.keys()
                    X['restype'] = rst
                    X['response'] = rsp
                    return ('broadcast', X)
                else:
                    allEmployees[phonenum][tagname] =  stt 
                rettext = 'Successfully updated ' + tagname

            #flush the siteTags to disk
            self.flushpickle()

            del self.stagetag[phonenum]

            return ('text', rettext)
        else:
            return None

    def parse(self, messageBody, phonenum):
        Okeywords = messageBody.split()
        keywords = map(lambda i: i.lower(), Okeywords)
        allSites = self.sites
        allEmployees = self.employees
        if phonenum not in allEmployees.keys():
            allEmployees[phonenum] = {}
        kw0 = keywords[0]
        if kw0 in [ 'get', 'set', 'reset', 'list', 'count', 'broadcastmsg']:
            xdict = {
                'myalias': ('MYALIAS', ' alias', False, False),
                'myname': ('MYNAME', ' name', False, True),
                'myphoto': ('MYPHOTO', '', True, False),
            }
            if kw0 == 'broadcastmsg' :
                if len(keywords) < 2:
                        return ('text', 'Invalid Command.  Usage: BROADCASTMG msessage' )
                elif keywords[1] == 'next':
                        self.stagetag[phonenum] = ('broadcast', '', keywords[1])
                        return ('text', 'Please send message to be boradcasted %s ' % (keywords[1]))
                else:
                    return ('broadcast', {'employees':allEmployees.keys(), 'response': ' '.join(Okeywords[1:]), 'restype':'text'} )

            if kw0 == 'count' :
                    if len(keywords) != 1: 
                        return ('text', 'Invalid Command.  Usage: list' )

                    return ('text', len(allEmployees))
            if kw0 == 'list' :
                    if len(keywords) != 1: 
                        return ('text', 'Invalid Command.  Usage: list' )

                    def stitch(phonenum): 
                        try:
                            (r1, r2) = allEmployees[phonenum]['myalias']
                        except:
                            r2 = ''
                            pass
                        try:
                            (r1, r3) = allEmployees[phonenum]['myname']
                        except:
                            r3 = ''
                            pass
                        try:
                            (r1, r4) = allEmployees[phonenum]['myphoto']
                            r5 = r4['mediaurl']
                        except:
                            r5 = ''
                            pass
                        #return "%s,%s,%s,%s" % (r2, r3, phonenum, r5)
                        return "%s,%s" % (r2, phonenum)
                    return ('text', '\n'.join(map(stitch, allEmployees.keys())))
            kw1 = keywords[1]
            if kw1 in xdict.keys():
                (pstr, ppstr, asknext, unlimited) = xdict[kw1]


                if kw0 == 'get':
                    if len(keywords) != 2: 
                        return ('text', 'Invalid Command.  Usage: GET %s' % (ppstr))
                    if kw1 in allEmployees[phonenum].keys():
                        return  allEmployees[phonenum][kw1]
                    else:
                   
                        return ('text', 'Not yet set. Set using: SET %s' % (pstr))

                elif kw0 in [ 'set', 'reset']:

                    if (not unlimited) and (not asknext and len(keywords) != 3) or asknext and (len(keywords) != 2): 
                        return ('text', 'Invalid Command.  Usage: SET %s' % (pstr+ppstr))
                    if kw1 in allEmployees[phonenum].keys() and kw0 == 'set'  :
                        return ('text', 'Unsuccessful. %s for %s already set . To update, send RESET %s' % (pstr, phonenum, pstr + ppstr))

                    if unlimited:
                        allEmployees[phonenum][kw1] = ('text', ' '.join( Okeywords[2:]))
                        self.flushpickle()
                        return ('text', 'Successfully updated %s ' % (kw1))
                    if asknext:
                        self.stagetag[phonenum] = ('attach', '', kw1)
                        return ('text', 'Please send content for  %s ' % (kw1))
                    else:
                        allEmployees[phonenum][kw1] = ('text', keywords[2])
                        self.flushpickle()
                        return ('text', 'Successfully updated %s ' % (kw1))


        if keywords[0] in ['newsite', 'newevent', 'newteam']:
            pstr = 'SITEHANDLE'
            isevent = False
            isteam = False
            if keywords[0] == 'newteam':
                pstr = 'TEAMHANDLE'
                isteam = True
            if keywords[0] == 'newevent':
                pstr = 'EVENTHANDLE'
                isevent = True

            if len(keywords) != 2: 
                return ('text', 'Invalid Command.  Usage: %s %s' % (keywords[0], pstr))
            sitename = keywords[1]
            if sitename in allSites.keys():
                return ('text', 'Invalid %s : Given handle already exists -- Choose a different handle' % pstr)

            allSites[sitename] = self.sitestructure( phonenum, isevent, isteam )
            self.flushpickle()
            if isevent:
                return ('text', 'Event %s created. Send %s register to register' % (sitename, self.sitehandle(sitename)))
            if isteam:
                return ('text', 'Team %s created. Send %s addmember <alias> to add members' % (sitename, self.sitehandle(sitename)))

            return ('text', 'Site %s created. Send %s SET TAGNAME to start a tag for this site' % (sitename, self.sitehandle(sitename)))

        elif "getsites" == keywords[0]:
            sitestr = ' '.join(map(lambda s: self.sitehandle(s), allSites.keys()))
            if sitestr:
                return ('text', "Try 'SITE help' -- Existing Sites: " + sitestr)
            else:
                return ('text', 'No Sites exist: Create one using "newsite SITENAME"')

        for s in allSites.keys():
            #check within each site now
            sitekey = self.sitehandle(s) 
            if sitekey in keywords:
                # found @site in the given message i.e. keywords[]
                kw = copy(keywords)
                kw.remove(sitekey)
                siteStruct = allSites[s]
                siteTags = siteStruct['tags']
                siteAllow = siteStruct['phones']
                siteEvent = 'eventdata' in siteStruct.keys()
                siteTeam = 'teamdata' in siteStruct.keys()

                def defretstr(msg='', sk=sitekey, st=siteTags, se=siteEvent, sm=siteTeam):
                    retstr = ''
                    retstr1 = ''

                    if sm:
                        retstr1 = '%s addmember <alias>\n' % sk + '%s membercount\n' % sk + '%s memberlist\n' % sk
                    if se:
                        retstr = '%s register \n' % sk + '%s registercount\n' % sk + '%s registerlist\n' % sk
                        #return ('text', retstr)
                    if st:
                        #retstr = '%s Use %s TAG -- where TAG is one of [%s]' % (msg, sk, ', '.join( st.keys() ))
                        X = st.keys()
                        X.remove("main")
                        retstr = 'Usage:\n' + retstr + retstr1 + '\n'.join(map(lambda a: "%s %s" % (sk, a), X))
                    else:
                        retstr = 'Usage:\n' + retstr + retstr1
                        #retstr = 'No Tags exist for %s - Setup something using %s set TAGNAME' % (sk, sk)
                    return ('text', retstr)

                if 'allow' in kw:
                    if phonenum not in siteAllow:
                        logger.info( siteAllow)
                        logger.info( phonenum)
                        return ('text', 'This Phone is not allowed for setting tags for %s. To allow this phone, Send %s ALLOW %s from the original phone number ' % (sitekey, sitekey, phonenum))
                    try:
                      if len(kw) == 2:
                        tagname = '%s' % int(kw[1])
                        if tagname[0] == '-' and tagname.replace('-', '') in siteAllow:
                            siteAllow.remove(tagname.replace('-', ''))
                        elif tagname[0] != '-' and tagname not in siteAllow:
                            siteAllow.append(tagname)
                        logger.info( siteAllow)
                        self.flushpickle()
                        return ('text', 'Successfully allowed %s for site %s' %(tagname, sitekey))
                      elif len(kw) == 1:
                        return ('text', 'Allowed phone numbers for site %s are %s' %(sitekey, siteAllow))
                      else:
                        return ('text', 'Invalid command/phone. To allow a phone, Send %s ALLOW PHONE from the original phone number' % (sitekey))
                    except:
                        return ('text', 'Invalid command. To allow a phone, Send %s ALLOW PHONE from the original phone number' % (sitekey))

                if 'set' in kw or 'reset' in kw or 'append' in kw or 'delete' in kw :
                    if phonenum not in siteAllow:
                        return ('text', 'This Phone is not allowed for setting tags for %s. To allow this phone, Send %s ALLOW %s from the original phone number' % (sitekey, sitekey, phonenum))
                    if len(kw) != 2: 
                        return ('text', 'Invalid TAGNAME')
                    tagname = kw[1]

                    if 'set' in kw and tagname in siteTags.keys(): 
                        return ('text', 'Invalid TAGNAME: Given tag already exists for the site %s -- Use %s APPEND TAGNAME to attach the content to and existing tag or  %s RESET TAGNAME to reset existing tag' % (sitekey, sitekey, sitekey) )
                    if ('reset' in kw or 'append' in kw or 'delete' in kw) and tagname not in siteTags.keys(): 
                        return ('text', 'Invalid TAGNAME: Given tag doesn not exist for the site %s -- Use %s SET TAGNAME set existing tag' % (sitekey, sitekey) )

                    if 'append' in kw:
                        self.stagetag[phonenum] = ('append', s, tagname)
                    elif 'delete' in kw:
                        del siteTags[tagname]
                        self.flushpickle()
                        return ('text', 'Deleted %s tag: %s' % (sitekey, tagname))
                    elif 'set' in kw or 'reset' in kw:
                        self.stagetag[phonenum] = ('update', s, tagname)
                        logger.info( self.stagetag[phonenum])

                    return ('text', 'Please send the content for %s tag: %s' % (sitekey, tagname))
                elif len(kw) < 1:
                    if 'main' in siteTags.keys():
                        ret1 = deepcopy(siteTags['main'])
                        if sitekey not in ['@hack']:
                            ret1.append(defretstr())
                        logger.info(ret1)
                        return ('list', ret1)
                    else:
                        return defretstr()
                elif 'help' == kw[0]:
                    return defretstr()
                elif 'adminhelp' == kw[0]:
                    return ('list', [('text', '%s set/reset/append TAG -- for updating a tag ' % (sitekey)), ('text', '%s allow PHONENUMBER -- for allowing another phone for updates') 
                        ] )
                else:
                    if siteTeam:
                        siteTeamData = siteStruct['teamdata']
                        if 'membercount' in kw :  
                            rl = siteTeamData['memberlist']
                            if len(kw) != 1:
                                return ('text', 'Invalid message: Please send %s membercount or %s memberlist' % (sitekey, sitekey))
                            return ('text', 'Number of Members: %s' % len(rl) )
                        if 'memberlist' in kw :  
                            rl = siteEventData['memberlist']
                            if len(kw) != 1:
                                return ('text', 'Invalid message: Please send %s membercount or %s memberlist' % (sitekey, sitekey))
                            return ('text', '\n'.join(map(lambda a: '%s'% a, rl) ) or 'No members added yet')


                        if 'addmember' or 'removemember' in kw:
                            if len(kw) != 2:
                                return ('text', 'Invalid message: Please send %s addmember/removemember <alias>' % (sitekey))
                            rl = siteEventData['memberlist']
                            alias = kw[1]
                            if 'addmember' == kw[0]:
                                if (len(rl)>=6) :
                                    return ('text', 'Max members per team is 6. %s could not be added to %s' % (alias, sitekey))

                                rl.add(alias)
                                return ('text', 'Added %s to %s ' % (alias, sitekey))
                            else:
                                rl.discard(alias)
                                return ('text', 'Removed %s from %s ' % (alias, sitekey))


                    if siteEvent:
                        siteEventData = siteStruct['eventdata']
                        if 'registercount' in kw :  
                            rl = siteEventData['registerlist']
                            if len(kw) != 1:
                                return ('text', 'Invalid message: Please send %s registercount or %s registerlist' % (sitekey, sitekey))
                            return ('text', 'Total Registrations: %s' % len(rl) )

                        if 'registerlist' in kw :  
                            rl = siteEventData['registerlist']
                            if len(kw) != 1:
                                return ('text', 'Invalid message: Please send %s registercount or %s registerlist' % (sitekey, sitekey))
                            return ('text', '\n'.join(map(lambda a: '%s'% a, rl) ) or 'No one registered yet')


                        if 'register' or 'unregister' in kw:
                            if len(kw) != 1:
                                return ('text', 'Invalid message: Please send %s register ' % (sitekey))
                            rl = siteEventData['registerlist']
                            try:
                               (r1, r2) = allEmployees[phonenum]['myalias']
                            except:
                                return ('text', 'Invalid registration: Your alias is not registered. Please send "set myalias ALIAS" first ' )

                            alias = r2
                            if 'register' == kw[0]:
                                rl.add(alias)
                                return ('text', 'Registered %s for %s ' % (alias, sitekey))
                            else:
                                rl.discard(alias)
                                return ('text', 'Unregistered %s from %s ' % (alias, sitekey))



                    # Here is the real search for a given TAG
                    tagname = kw[0]
                    if tagname in siteTags.keys():
                        return ('list', siteTags[tagname])
                    else:
                        return defretstr(msg="Invalid tag! ")

                return defretstr()

        return None


class GetSet():
    def __init__(self, cbfn=None):
        global TESTSCRIPT
        self.TAGSFILE = '/tmp/serve/' + TESTSCRIPT + 'tags_getset.pkl'
        self.stagetag = {}
        self.topickle = { 'tags': {} }

        try:
            tagsfile = open(self.TAGSFILE, "rb")
            self.topickle = cPickle.load(tagsfile)
            tagsfile.close()
        except IOError:
            pass

        self.tagqueue = self.topickle['tags']

    def flushpickle(self):
        output = open(self.TAGSFILE, 'wb')
        cPickle.dump(self.topickle, output)
        output.close()

    def preparse(self, j, phonenum):
      
        if phonenum in self.stagetag.keys():
            tagname = self.stagetag[phonenum].lower()

            stt = stitchmessage(j, phonenum, tagname)
            logger.info(stt)
            if tagname.startswith("append__"):
                tagname = tagname[8:]
                if tagname in self.tagqueue.keys():
                    self.tagqueue[tagname].append(stt)
                else:
                    self.tagqueue[tagname] = [ stt ]
            else: 
                self.tagqueue[tagname] = [ stt ]

            #flush the self.tagqueue to disk
            self.flushpickle()

            logger.info( self.stagetag)
            del self.stagetag[phonenum]

            return ('text', 'Successfully attached to tag:' + tagname)
        else:
            return None

    def parse(self, messageBody, phonenum):
        keyword = messageBody.split()[0].lower()
        if keyword == "get":
            keywords = messageBody.split()
            tagname = keywords[1].lower()
            if tagname in self.tagqueue.keys():
                return ('list', self.tagqueue[tagname])

        elif keyword == "set":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid TAGNAME')
            tagname = keywords[1]
            if tagname in self.tagqueue.keys():
                return ('text', 'Invalid TAGNAME: Given tag already exists -- Use APPEND TAGNAME to attach the content to and existing tag or RESET TAGNAME to reset existing tag')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        elif keyword == "append":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid TAGNAME')
            tagname = keywords[1]
            if tagname not in self.tagqueue.keys():
                return ('text', 'Invalid TAGNAME: Given tag doesn"t exist')

            self.stagetag[phonenum] = "append__" + tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        elif keyword == "reset":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid tag')
            tagname = keywords[1]
            if tagname not in self.tagqueue.keys():
                return ('text', 'Invalid TAG: Given tag does not exist')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        return None



class Default():

    def getquote(self):

        quote_file = open('quotes.pkl', 'rb')
        quotes = cPickle.load(quote_file)
        quote_file.close()

        return random.choice(quotes)

    def gethelpstring(self):
        helpstring = "Please try @faq"
        return helpstring

    def preparse(self, jsondict, phonenum):

        if jsondict['msgtype']  == 'mediaaa':

            if jsondict['mediatype']  in ("image"):
                media_url = jsondict['mediaurl'] 
                TEMPDOWNLOADFILE = '/tmp/X.jpg'
                savepath = TEMPDOWNLOADFILE
                urlretrieve( media_url, savepath)
                call(["/home/bitnami1/bhandara/gitpush.script"])
                return ret('text', 'saved %s' % 8)
            return ret('text', 'no media messages are handled')
        return None

    def parse(self, messageBody, phonenum):
        keyword = messageBody.split()[0].lower()

        if keyword.lower() in[ "inspire", "inspiration"]:
            return ('text', self.getquote())
        elif keyword == "name":
            return ('text', "Wait, I will soon have something cool")
        elif keyword == "img#$SDF#R$W":
            try:
                image_number = messageBody.split()[1]
                if image_number not in ['1', '2', '3', '4', '5', '6', '7']:
                    image_number = '1'
            except:
                image_number = '1'
            return ('image', '/home/bitnami1/bhandara/website/img/t%s.jpg' % image_number )
        else:
            return ('text', self.gethelpstring())

class Serve():

    def __init__(self, cbfn=None):

                
        call("mkdir -p /tmp/serve".split())

        self.subparsers = [  Sites(), GetSet(), Default() ]


    def getResponse(self, jsondict):

        ret = lambda a,b: {'phonenum':jsondict['phonenum'], 'medium':jsondict['medium'] ,'restype': a, 'response': b}

        phonenum = '%s' % jsondict['phonenum']
        #logger.info( self.stagetag)

        for sp in self.subparsers:
            ret1 = sp.preparse(jsondict, phonenum)
            if ret1:
                (a, b) = ret1
                return ret(a, b)

        if jsondict['msgtype'] != 'text':
            return None

        for sp in self.subparsers:
            ret1 = sp.parse(jsondict['msgbody'], phonenum)
            if ret1:
                (restype, response) = ret1
                return ret(restype, response)

        return None

    def getResponseWrapper(self, jsondict, recdMsg):
        inputjson = json.loads(jsondict)
        resp = self.getResponse(inputjson)
        if resp:
            return json.dumps(resp)
        else:
            return None
        
        


