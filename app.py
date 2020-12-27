# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 12:41:20 2020

@author: James Brennan
"""
import os
import sys
import requests

import psycopg2
from flask import Flask, request

from constants import DB_QUERIES, BASE_URL

BOT_ID = os.getenv('GROUPME_BOT_ID')
GM_BOT_ID = '850624'
TOKEN = os.getenv('TOKEN')
MAIN_GROUP = os.getenv('MAIN_GROUP')
ADMIN_ID = os.getenv('ADMIN_ID')

DATABASE_URL = os.getenv('DATABASE_URL')


app = Flask(__name__)

# Enter here
@app.route('/', methods=['POST'])
def webhook():
  data = request.get_json()
  if "@bot" in data['text']:
      find_call(data)
      log('===============FINDING CALL===============')
  else:
      if data['sender_id'] != GM_BOT_ID:
          msg = check_triggers(data['text'])
          if len(msg) > 0:
              basic_message(msg)
  return "ok", 200

def send_message(data):
  url  = BASE_URL+'/bots/post'
  log(f'message sent: {data}')
  request = requests.post(url, json=data)
  return request
  
def make_request(resource, payload):
    url = f'{BASE_URL}/{resource}?token={TOKEN}'
    response = requests.get(url=url, params=payload)
    log('Request to GroupMe: \n\t'+
        f'url: {url}\n\t'+
        f'payload: {payload}\n\t'+
        f'status: {str(response.status_code)}')
    return response
  
def find_call(data):
    text = data["text"]
    # commands
    if   "!all" in text:
        mention_all()
    elif "!remember" in text:
        remember(data)
    elif "!forget" in text:
        pass#forget(data)
    else:
        command_not_found()
        
def basic_message(msg):
    data = {
        "bot_id" : BOT_ID,
        "text": msg
    }
    send_message(data)
        
def mention_all():
    members = _get_members()
    if members:
        # Initialize
        data = {"bot_id" : BOT_ID}
        text = ""
        attachments, loci = [], []
        walker = 1
        attach_dict = {"type":"mentions", "user_ids":[]}
        # Work 
        for mem in members:
            text += " @"
            nickname = members[mem]["nickname"]
            l = [walker, len(nickname)+1]
            text += nickname
            walker += len(nickname) + 2
            attach_dict["user_ids"].append(mem)
            loci.append(l)
        attach_dict["loci"] = loci
        attachments.append(attach_dict)
        data["text"] = text
        data["attachments"] = attachments
        send_message(data)
        
def remember(data):
    text = data['text']
    command = text[15:].split('::')
    if len(command) != 2:
        msg = "Invalid format -.-"
    else : 
        trig  = command[0]
        response = command[1]
        if not _pr_table_exists():
            _execute_query(DB_QUERIES["CREATE_PR_TABLE"])
        qry = DB_QUERIES["PR_INSERT"].format(trig, response)
        _execute_query(qry)
        msg = f'"{trig}" will now trigger "{response}"'
    basic_message(msg)
        
# def forget(data):
#     text = data['text']
#     trig = msg[13:]
#     if df:
#         df.drop(trig)
#         _update_table(df)
#         msg = f'Just forgot all about "{trig}"'
#     else:
#         msg = 'Sorry boss, no saved data to forget.'
#     basic_message(msg)

def check_triggers(text):
    trig_list = _execute_query(DB_QUERIES["GET_TRIGS"])
    msg = ''
    if trig_list:
        for t in trig_list:
            trig = t[0]
            if trig == text:
                if len(msg) > 0:
                    msg += '\n'
                msg += _get_response(trig)
    return msg        
        
def command_not_found():
    basic_message("Huh?")
    
def _get_members():
    member_dict = {}
    response = make_request('groups',{"id":MAIN_GROUP})
    if response.status_code == 200:
        groups_data = response.json()["response"]
        for group in groups_data:
            if group['id'] == MAIN_GROUP:
                for member in group["members"]:
                    entry = member
                    member_id = entry["user_id"]
                    del entry["user_id"]
                    member_dict[member_id] = entry
        return member_dict
    return None

def _get_response(trig):
    qry = DB_QUERIES["GET_REPLY"].format(trig)
    return _execute_query(qry)[0][0]

# SQL Functions 
def _pr_table_exists():
    exist = _execute_query(DB_QUERIES["PR_TABLE_EXISTS"])
    return exist[0]

def _execute_query(query):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    log({"query_executed":query})
    cur.execute(query)
    ret = None
    try : 
        ret = cur.fetchall()
    except Exception as err:
        log({"Error":err})
    cur.close()
    conn.commit()
    conn.close()
    if ret : 
        log({"query returned":ret})
        return ret

def log(msg):
  print(str(msg))
  sys.stdout.flush()
  


