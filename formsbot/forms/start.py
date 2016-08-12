#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import config
import dbhelper
import datetime
import copy

from telebot import types

# Initialize bot
bot = telebot.TeleBot(config.token)

USERS = 'user'
STAGING = 'staging'
EVENTS = 'events'
TELEGRAMUSERS = 'telegramuser'
ADMINS = 'admins'

fields = {}
fields_initialize = {
        USERS: {'mandatory': ['name', 'phone', 'email']},
        EVENTS: {'mandatory': ['name', 'date', 'start-time','finish-time']},
        TELEGRAMUSERS: {'mandatory':['ownerid']},
        ADMINS: {'mandatory': ['ownerid', 'alias']},
}

ignorefields = [ USERS, EVENTS, TELEGRAMUSERS, ADMINS ]

askmf_format_string = {}
askmf_format_string_initialize = {
        USERS: 'please enter your %s',
        EVENTS: 'Event %s', 
        TELEGRAMUSERS: '%s',
}

staging = lambda k: 'staging' + ''.join(map(lambda a: '%s' % a, k))
printrecord = lambda record: '\n'.join(map(lambda k: '_%s_ *%s*'%(k, record[k]), fields[record['table']]['mandatory']))

def ask_mf(table, message, recordkey):
    def get_a_missing_field(table, record):
        for field in fields[table]['mandatory']:
            if field not in record.keys():
                return field

    record = dbhelper.get_record(table, recordkey)
    if record:
        mf = get_a_missing_field(table, record)
        if mf:
            msg = askmf_format_string[table] % mf
            markup = types.ForceReply(selective=False)
    
            # add the needed message to the staging dict -- we are waiting for
            # a reply from the user
            skey = staging([message.chat.id, msg])
            dbhelper.update_record(STAGING, {'recordid':skey, 'recordkey':recordkey, 'table':table, 'field':mf})
            bot.send_message(message.chat.id, msg, reply_markup=markup)

            return



        #bot.send_message(message.chat.id, "%s stored :\n%s" % (table,  printrecord(record)), parse_mode="Markdown" )
        bot.send_message(message.chat.id, "%s stored :\n%s" % (table,  printrecord(record))  )

        if table == 'user':
            stdmenu(message)
            return
    
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('/add ' + table, '/count ' + table, '/list ' + table, '/done' )
        bot.send_message(message.chat.id, "What's next?", reply_markup=markup )

def stdmenu(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        #markup.row('/newevent', '/newuser')
        #markup.row('/events')
        #markup.row('/list events', '/list user')
        #markup.row('/count events', '/count user')
        markup.row('List All Forms', 'Create New Form')
        bot.send_message(message.chat.id, "What do you like to do next?", reply_markup=markup )

allusers = []

def refresh_allusers():
    global allusers
    allusers = dbhelper.get_allrecords(TELEGRAMUSERS, 'ownerid')
    print("Allusers = %s" % allusers)



def update_fields():
    global fields
    dbhelper.add_key('builtin_fields', fields)
    dbhelper.add_key('builtin_askmf_format_string', askmf_format_string)
    print(fields)
    print(askmf_format_string)

def refresh_fields():
    global fields
    global askmf_format_string
    fields = dbhelper.get_key('builtin_fields')
    askmf_format_string = dbhelper.get_key('builtin_askmf_format_string')
    if not fields:
        fields = fields_initialize
        askmf_format_string = askmf_format_string_initialize
        update_fields()
        fields = dbhelper.get_key('builtin_fields')
        askmf_format_string = dbhelper.get_key('builtin_askmf_format_string')

refresh_fields()
refresh_allusers()


#first message handle //no other message handler should be above this
@bot.message_handler(func=lambda message: message.chat.id not in allusers, content_types=["text"])
def newuser_arrived(message):
    refresh_allusers()
    if allusers == None or message.chat.id not in allusers:
        newrecord(TELEGRAMUSERS, message, askmf=False)
        refresh_allusers()
        bot.send_message(message.chat.id, "Hello! Welcome to Volunteer Help system!")
        newrecord(USERS, message, extra=[('primary', message.chat.id)])


# Handle always first "/start" message when new chat with your bot is created
@bot.message_handler(commands=["start", "help"])
def command_start(message):
    bot.send_message(message.chat.id, "Hello! Welcome to Mobile Forms system!")
    ask_mf(USERS, message, message.chat.id)
    stdmenu(message)

@bot.message_handler(commands=["done"])
def command_start(message):
    stdmenu(message)


@bot.message_handler(commands=["count"])
def command_count(message):
    kw = message.text.strip().split()
    if len(kw) <= 1:
        return
    #print(kw[1:])
    for j in kw[1:]:
        if j in fields.keys():
            #print(j)
            outp = '%s count is %s' %(j, dbhelper.count(j))
            #print(outp)
            bot.send_message(message.chat.id, outp)
        else:
            outp = "%s table doesn't exist" %(j)
            bot.send_message(message.chat.id, outp)

@bot.message_handler(commands=["list"])
def command_list(message):
    kw = message.text.strip().split()
    if len(kw) <= 1:
        return
    #print(kw[1:])
    for j in kw[1:]:
        if j in fields.keys():
            #print(j)

            keylist = fields[j]['mandatory']

            outp = 'List is: \n' 
            outp1 = ','.join(keylist) + '\n' + '\n'.join(map(lambda rec: ','.join('%s' % (i in rec.keys() and rec[i] or '') for i in keylist) , dbhelper.getlist(j)))

            fname = '/tmp/%s.csv' % datetime.datetime.now()
            f = open(fname, "w+")
            f.write(outp1)
            f.close()
            f = open(fname, 'rb')
            if outp1:
                bot.send_message(message.chat.id, outp)
                bot.send_document(message.chat.id, f)
            else:
                outp = "%s table contains zero records" %(j)
                bot.send_message(message.chat.id, outp)

        else:
            outp = "%s table doesn't exist" %(j)
            bot.send_message(message.chat.id, outp)

@bot.message_handler(commands=["add"])
def command_add(message):
    kw = message.text.strip().split()

    if len(kw) != 2:
        outp = "Usage: /add <formname> ; Wrong number of arguments given "
        bot.send_message(message.chat.id, outp)
        return

    formname = kw[1]
    if formname not in fields.keys():
        outp = "Unknown Form Name *%s*" % formname
        bot.send_message(message.chat.id, outp)
        return

    newrecord(formname, message)



@bot.message_handler(func=lambda message: message.text in ['List All Forms'], content_types=["text"])
def list_all_forms(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    count = 0

    add = lambda x : '/add %s' % x

    a = [ add(x) for x in 
             filter( lambda f: f not in ignorefields, fields.keys())
        ]   


    for (r1, r2, r3) in [( a[i], a[i+1], a[i+2] ) for i in range(0, len(a)-2, 3)]:
        markup.row(r1, r2, r3)

    rem = [ a[y] for y in range( int(len(a)/3) * 3, len(a)) ]
    if rem:
        if len(rem) == 2:
            markup.row( rem[0], rem[1], "")
        else:
            markup.row( "", rem[0], "")

    markup.row('/done')
    bot.send_message(message.chat.id, "Select an action ...", reply_markup=markup )



@bot.message_handler(func=lambda message: message.text in ['Create New Form'], content_types=["text"])
def create_new_form(message):
    command_newform(message)




evlist={}

@bot.message_handler(commands=["events"])
def command_events(message):
        for ev in dbhelper.getlist(EVENTS):
            evlist['%s %s %s-%s' % (ev['name'], ev['date'], ev['start-time'], ev['finish-time'])] = ev['recordid']

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for ev in evlist.keys():
            markup.add(ev)

        bot.send_message(message.chat.id, "Select an Event", reply_markup=markup)

last_message_sent = {}

REGISTER_FOR_EVENT = 'register for this event'
LIST_VOLUNTEERS = 'list volunteers'
COUNT_VOLUNTEERS = 'count volunteers'

@bot.message_handler(func=lambda msg: msg.text in evlist.keys(), content_types=["text"])
def selected_event(message):
    recordid = evlist[message.text]
    ev = dbhelper.get_record(EVENTS, recordid)

    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(REGISTER_FOR_EVENT)
    markup.row('list volunteers', 'count volunteers')
    last_message_sent[str(message.chat.id)] = {'record': ev}
    bot.send_message(message.chat.id, "What with this Event %s ? " % message.text, reply_markup=markup)


def get_user_description(chatid):
    userlist = dbhelper.getlist(USERS, efilter=('primary', chatid))
    return userlist[0]


@bot.message_handler(func=lambda message: message.text in [REGISTER_FOR_EVENT, COUNT_VOLUNTEERS, LIST_VOLUNTEERS], content_types=["text"])
def handle_rls(message):
    try:
        lms = last_message_sent[str(message.chat.id)] 
        del last_message_sent[str(message.chat.id)] 
        if lms['record']['table'] != EVENTS:
            raise KeyError

        recordid = lms['record']['recordid']

        evrec = dbhelper.get_record(EVENTS, recordid)
        if 'volunteers' not in evrec.keys():
            evrec['volunteers'] = []

        if message.text == REGISTER_FOR_EVENT and  message.chat.id not in evrec['volunteers']:
            evrec['volunteers'] += [message.chat.id]
            dbhelper.update_record(EVENTS, evrec)
            bot.send_message(message.chat.id, "Registered!")

        if message.text == COUNT_VOLUNTEERS:
            outp = 'Number of Registered Volunteers is: %s' % len(evrec['volunteers'])
            bot.send_message(message.chat.id, outp)

        if message.text == LIST_VOLUNTEERS:
            printuser = lambda record: '\t'.join(map(lambda k: '%s'%(record[k]), fields[record['table']]['mandatory']))
            outp = 'List is: \n' 
            outp1 = '\n'.join(('%s' % printuser(get_user_description(i))) for i in evrec['volunteers'])

            fname = '/tmp/%s.txt' % datetime.datetime.now()
            f = open(fname, "w+")
            f.write(outp1)
            f.close()
            f = open(fname, 'rb')
            bot.send_message(message.chat.id, outp)
            bot.send_document(message.chat.id, f)

        command_events(message)

    except:
        print('Exception! '  + message.text)
        return



@bot.message_handler(commands=["whoami"])
def command_whoami(message):
    userobj = get_user_description(message.chat.id)
    outp = 'Alien!!!'
    if userobj:
        outp = printrecord(userobj)
    bot.send_message(message.chat.id, outp)


@bot.message_handler(commands=["newuser"])
def command_newuser(message):
    newrecord(USERS, message)

@bot.message_handler(commands=["newevent"])
def command_newevent(message):
    newrecord(EVENTS, message)

def validate(bot, message, errorstr, condition):
    if condition:
        return False
    else:
        bot.send_message(message.chat.id, errorstr)
        return True


@bot.message_handler(commands=["newform"])
def command_newform(message):
    
    #validate for /newform formname fieldlist

    USAGE = "Usage: /newform <formname_upto_8_letters> <numfields> <field1> <field2> ... <fieldN>"

    args = message.text.split()
    if validate(bot, message, USAGE, args[0] == '/newform'):
        return
    if validate(bot, message, USAGE, len(args) >= 4):
        return
    
    name = args[1]
    if validate(bot, message, "Form Name *%s* cannot be more than 8 letters long; Use a different Name" % name, len(name) <= 8):
        return

    if validate(bot, message, "Form Name *%s* already in use; Use a different Name" % name, name not in fields.keys()):
        return

    try:
        numfields = int(args[2])
        if validate(bot, message, USAGE + "\n NumFields should be same as the number of fields following it;  Fields are space-separated", len(args) - 3 == numfields ) :
            return
        flds = copy.copy(args[3:])
    except:
        validate(bot, message, USAGE + "\nNumFields should be an integer", 0 ) 
        return

    fields[name] = { 'mandatory': flds }
    askmf_format_string[name] = name + ' record: Enter %s'

    update_fields()

    outp = "Form creation successful"
    bot.send_message(message.chat.id, outp)

            
    stdmenu(message)






def newrecord(table, message, extra=[], askmf=True):
    #rec = dbhelper.get_record(table, message.chat.id)
    rec = {}
    if 1:
        rec['table'] = table
        rec['recordid'] = '%s' % datetime.datetime.now()
        rec['ownerid'] = message.chat.id
        for (k,v) in extra:
            rec[k] = v
        dbhelper.update_record(table, rec)

        if askmf:
            ask_mf(table, message, rec['recordid'])

@bot.message_handler(func=lambda message: message.reply_to_message, content_types=["text"])
def namevalue_workflow_stage1(message):
    skey = staging([message.chat.id, message.reply_to_message.text])
    sval = dbhelper.get_record(STAGING, skey)
    if sval:
        #found the previous reply message in staging dict
        mf = sval['field']
        table = sval['table']
        recordkey = sval['recordkey']
        rec = dbhelper.get_record(table, recordkey)
        rec[mf] = message.text
        dbhelper.update_record(table, rec)

        dbhelper.delete_record(STAGING, skey)

        ask_mf(table, message, rec['recordid'])


@bot.message_handler(func=lambda message: message.chat.id == config.my_id, content_types=["text"])
def my_text(message):
    # If we're just sending messages to bot (not replying) -> 
    #do nothing and notify about it.
    # Else -> get ID whom to reply and send message FROM bot.
    print(message.reply_to_message)
    if message.reply_to_message:
        who_to_send_id = dbhelper.get_user_id(message.reply_to_message.message_id)
        if who_to_send_id:
            # You can add parse_mode="Markdown" 
            #or parse_mode="HTML", however, in this case you MUST make sure,
            # that your markup if well-formed as described 
            #here: https://core.telegram.org/bots/api#formatting-options
            # Otherwise, your message won't be sent.
            bot.send_message(who_to_send_id, message.text)
            # Temporarly disabled freeing message ids. 
            #They don't waste too much space
            # dbhelper.delete_message(message.reply_to_message.message_id)
    else:
        bot.send_message(message.chat.id, "Not something that I understand.  try /help")


@bot.message_handler(func=lambda message: message.chat.id == config.my_id, content_types=["sticker"])
def my_sticker(message):
    if message.reply_to_message:
        who_to_send_id = dbhelper.get_user_id(message.reply_to_message.message_id)
        if who_to_send_id:
            bot.send_sticker(who_to_send_id, message.sticker.file_id)
    else:
        bot.send_message(message.chat.id, "No one to reply!")


@bot.message_handler(func=lambda message: message.chat.id == config.my_id, content_types=["photo"])
def my_photo(message):
    if message.reply_to_message:
        who_to_send_id = dbhelper.get_user_id(message.reply_to_message.message_id)
        if who_to_send_id:
            # Send the largest available (last item in photos array)
            bot.send_photo(who_to_send_id, list(message.photo)[-1].file_id)
    else:
        bot.send_message(message.chat.id, "No one to reply!")


@bot.message_handler(func=lambda message: message.chat.id == config.my_id, content_types=["voice"])
def my_voice(message):
    if message.reply_to_message:
        who_to_send_id = dbhelper.get_user_id(message.reply_to_message.message_id)
        if who_to_send_id:
            # bot.send_chat_action(who_to_send_id, "record_audio")
            bot.send_voice(who_to_send_id, message.voice.file_id, duration=message.voice.duration)
    else:
        bot.send_message(message.chat.id, "No one to reply!")


@bot.message_handler(func=lambda message: message.chat.id == config.my_id, content_types=["document"])
def my_document(message):
    if message.reply_to_message:
        who_to_send_id = dbhelper.get_user_id(message.reply_to_message.message_id)
        if who_to_send_id:
            # bot.send_chat_action(who_to_send_id, "upload_document")
            bot.send_document(who_to_send_id, data=message.document.file_id)
    else:
        bot.send_message(message.chat.id, "No one to reply!")


@bot.message_handler(func=lambda message: message.chat.id == config.my_id, content_types=["audio"])
def my_audio(message):
    if message.reply_to_message:
        who_to_send_id = dbhelper.get_user_id(message.reply_to_message.message_id)
        if who_to_send_id:
            # bot.send_chat_action(who_to_send_id, "upload_audio")
            bot.send_audio(who_to_send_id, performer=message.audio.performer,
                           audio=message.audio.file_id, title=message.audio.title,
                           duration=message.audio.duration)
    else:
        bot.send_message(message.chat.id, "No one to reply!")


@bot.message_handler(func=lambda message: message.chat.id == config.my_id, content_types=["video"])
def my_video(message):
    if message.reply_to_message:
        who_to_send_id = dbhelper.get_user_id(message.reply_to_message.message_id)
        if who_to_send_id:
            # bot.send_chat_action(who_to_send_id, "upload_video")
            bot.send_video(who_to_send_id, data=message.video.file_id, duration=message.video.duration)
    else:
        bot.send_message(message.chat.id, "No one to reply!")


# No Google Maps on my phone, so this function is untested, should work fine though.
@bot.message_handler(func=lambda message: message.chat.id == config.my_id, content_types=["location"])
def my_location(message):
    if message.reply_to_message:
        who_to_send_id = dbhelper.get_user_id(message.reply_to_message.message_id)
        if who_to_send_id:
            # bot.send_chat_action(who_to_send_id, "find_location")
            bot.send_location(who_to_send_id, latitude=message.location.latitude, longitude=message.location.longitude)
    else:
        bot.send_message(message.chat.id, "No one to reply!")


# Handle all incoming messages except group ones
@bot.message_handler(func=lambda message: message.chat.id != config.my_id,
                     content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video',
                                    'voice', 'location', 'contact'])
def check(message):
    # Forward all messages from other people and save their message_id + 1 to shelve storage.
    # +1, because message_id = X for message FROM user TO bot and
    # message_id = X+1 for message FROM bot TO you

    #
    #bot.forward_message(config.my_id, message.chat.id, message.message_id)
    #dbhelper.add_message(message.message_id + 1, message.chat.id)
    #

    return


if __name__ == '__main__':
    bot.polling(none_stop=True)
