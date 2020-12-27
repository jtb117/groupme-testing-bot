# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 12:41:20 2020

@author: James Brennan
"""
import os
import sys
import requests
import boto3
import psycopg2
import pandas as pd
from matplotlib import pyplot as plt

from flask import Flask, request

from constants import DB_QUERIES, BASE_URL, IMAGE_URL, HEADERS, ID_TO_NAME, 
IMAGE_SEND_BODY

AWS_KEY_ID = os.getenv('AWS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BOT_ID = os.getenv('GROUPME_BOT_ID')
TOKEN = os.getenv('TOKEN')
MAIN_GROUP = os.getenv('MAIN_GROUP')
ADMIN_ID = os.getenv('ADMIN_ID')
DATABASE_URL = os.getenv('DATABASE_URL')
GM_BOT_ID = '850624'

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
        forget(data)
    elif "!triggers" in text:
        print_triggers()
    elif "!likes" in text:
        show_likes()
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
        old_trig = trig
        if not _pr_table_exists():
            _execute_query(DB_QUERIES["CREATE_PR_TABLE"])
        if "'" in trig:
            start = trig.find("'")
            trig  = trig[:start] + "'" + trig[start:]
        qry = DB_QUERIES["PR_INSERT"].format(trig, response)
        _execute_query(qry)
        msg = f'"{old_trig}" will now trigger "{response}"'
    basic_message(msg)
        
def forget(data):
    text = data['text']
    trig = text[13:]
    trig_list = _get_triggers()
    if trig in trig_list:
        qry  = DB_QUERIES['DEL_TRIG'].format(trig)
        _execute_query(qry)
        msg = f'Removed "{trig}"'
    else : msg = f'Trigger "{trig}" does not exist.'
    basic_message(msg)

def check_triggers(text):
    trig_list = _get_triggers()
    msg = ''
    for trig in trig_list:
        if trig.lower() == text.lower():
            if len(msg) > 0:
                msg += '\n'
            msg += _get_response(trig)
    return msg

def print_triggers():
    trig_list = _get_triggers()
    msg = ''
    for trig in trig_list:
        msg += trig + ", "
    if len(msg) > 0 : msg = msg[:-2]
    log("Printing triggers")
    basic_message(msg)
    
def show_likes():
    df = _get_likes()
    _save_likes_figure(df)
    img_url = _upload_image('message_counts.png')
    post_body = IMAGE_SEND_BODY
    post_body['bot_id'] = BOT_ID
    post_body['attachments'][0]['url'] = img_url
    send_message(post_body)
    
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

# Returns dataframe with
#  index: sender_id
#  cols:  message_count, name
def _get_likes():
    df = _get_full_chat()
    mc = pd.DataFrame(df.groupby('sender_id').count().attachments)
    mc.rename(columns={'attachments':'mcount'}, inplace=True)
    id2name = pd.DataFrame(data=ID_TO_NAME.values(),index=ID_TO_NAME.keys())
    mc['name'] = id2name
    mc = mc[['name','mcount']]
    mc = mc.drop(labels=['calendar','system'])
    mc = mc.sort_values(by='mcount', ascending=False)
    return mc

def _save_likes_figure(mc):
    mc.drop(mc[mc['mcount'] < 400].index, inplace=True)
    plt.bar(mc['name'],mc['mcount'])
    plt.xticks(rotation=90)
    plt.title('Message Counts by Fella')
    plt.xlabel('Fella Name')
    plt.ylabel('Number of Messages')
    plt.savefig('message_counts.png')
    
def _upload_image(filename):
    url = IMAGE_URL+'/pictures'
    headers = HEADERS
    headers['x-access-token'] = TOKEN
    img_url = ''
    with open(filename, 'rb') as f:
        response = requests.post(
            url, data=f.read(), json=TOKEN, headers=headers)
        img_url = response.json()['payload']['url']
    return img_url
    
def _get_full_chat():
    s3 = boto3.resource(
        service_name='s3',
        region_name='us-east-2',
        aws_access_key_id=AWS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    obj = s3.Object('groupme-bot','full_text.pickle')
    df = pd.read_pickle(io.BytesIO(obj.get()['Body'].read()))
    return df

# SQL Functions 
def _get_triggers():
    trig_list = _execute_query(DB_QUERIES["GET_TRIGS"])
    return_list = []
    if trig_list:
        for trig in trig_list:
            return_list.append(trig[0])
    return return_list

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
  


