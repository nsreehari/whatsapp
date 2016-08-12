# -*- coding: utf-8 -*-
# A simple wrapper on Python 3 Shelve module
# https://docs.python.org/3.5/library/shelve.html

import shelve
import config


def add_message(message_id, user_id):
    """
    Add key `message_id` with value `user_id`
    Integers can't be keys in Shelve, so we convert them to strings
    :param message_id: :param message_id: Telegram Message unique ID (within bot)
    :param user_id: User's unique ID
    """
    with shelve.open(config.storage_name) as db:
        db[str(message_id)] = user_id


# Temporally not using this to allow you to answer the same user multiple times
# and/or use ANY message from certain user to write to him
def delete_message(message_id):
    """
    Remove unnecessary key-value pair from Shelve to keep storage as small as possible
    :param message_id: Telegram Message unique ID (within bot)
    """
    with shelve.open(config.storage_name) as db:
        del db[str(message_id)]


def get_user_id(message_id):
    """
    Get user_id for given message_id
    On error, None is returned
    :param message_id:
    :exception KeyError: No key found with name "message_id"
    :return: User's unique ID on success / None if error occurs
    """
    try:
        with shelve.open(config.storage_name) as db:
            return db[str(message_id)]
    except KeyError:
        return None

reckey = lambda table, rkey : '%s%s'%(table, rkey)

def delete_record(table, rkey):
    """
    Remove unnecessary key-value pair from Shelve to keep storage as small as possible
    :param message_id: Telegram Message unique ID (within bot)
    """
    recordkey = reckey(table, rkey)

    with shelve.open(config.storage_name) as db:
        if recordkey in db:
            del db[recordkey]

def get_allrecords(table, field):
    try:
        with shelve.open(config.storage_name) as db:
            recs = filter ( lambda k: db[k]['table'] == table, db)
            return list(map(lambda k: db[k][field], recs))
    except:
        # This should not REACH HERE
        print("get_allrecords ERROR!!!")
        return None

def get_record(table, rkey):
    """
    Get user_obj for given user_id
    On error, None is returned
    :param user_id:
    :exception KeyError: No key found with name "user_id"
    :return: User object on success / None if error occurs
    """
    recordkey = reckey(table, rkey)
    try:
        with shelve.open(config.storage_name) as db:
            return db[recordkey]
    except KeyError:
        return None


def update_record(table, record):
    """
    Update user_obj for given user_id
    On error, None is returned
    :param user_id, user_obj:
    :exception KeyError: No key found with name "user_id"
    :return: User object on success / None if error occurs
    """
    recordkey = reckey(table, record['recordid'])
    try:
        with shelve.open(config.storage_name) as db:
            db[recordkey] = record
    except KeyError:
        # This should not REACH HERE
        print("update_record ERROR!!!")
        return None


def add_key(key, value):
    """
    Add key `key` with value `value`
    Integers can't be keys in Shelve, so we convert them to strings
    :param key: :param key: Telegram Message unique ID (within bot)
    :param value: User's unique ID
    """
    with shelve.open(config.storage_namekv) as db:
        db[str(key)] = value


# Temporally not using this to allow you to answer the same user multiple times
# and/or use ANY message from certain user to write to him
def delete_key(key):
    """
    Remove unnecessary key-value pair from Shelve to keep storage as small as possible
    :param key: Telegram Message unique ID (within bot)
    """
    with shelve.open(config.storage_namekv) as db:
        del db[str(key)]


def get_key(key):
    """
    Get value for given key
    On error, None is returned
    :param key:
    :exception KeyError: No key found with name "key"
    :return: User's unique ID on success / None if error occurs
    """
    try:
        with shelve.open(config.storage_namekv) as db:
            return db[str(key)]
    except KeyError:
        return None


def count(table, filters=[]):
    try:
        #for (fk,fv) in filters:
        #    db[k][fk] == db[k][fv]

        with shelve.open(config.storage_name) as db:
            return len(list(filter ( lambda k: db[k]['table'] == table,db)))
    except:
        # This should not REACH HERE
        print("count ERROR!!!")
        return None

def getlist(table, efilter=None, fields=[]):
    try:
        #for (fk,fv) in filters:
        #    db[k][fk] == db[k][fv]

        with shelve.open(config.storage_name) as db:
            if efilter:
                (efk, efv) = efilter
                m = map(lambda rec: db[rec], filter ( lambda k: db[k]['table'] == table and db[k][efk] == efv, db))
                return list(m)
            else:
                m = map(lambda rec: db[rec], filter ( lambda k: db[k]['table'] == table,db))
                return list(m)
    except:
        # This should not REACH HERE
        print("count ERROR!!!")
        return None
