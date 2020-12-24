# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 12:41:20 2020

@author: James
"""
import os
import sys

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, request

BOT_ID = os.getenv('GROUPME_BOT_ID')
TOKEN = os.getenv('TOKEN')
MAIN_GROUP = os.getenv('MAIN_GROUP')
ADMIN_ID = '15629174'
BASE_URL = 'https://api.groupme.com/v3/'

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
  data = request.get_json()
  user_id = data['user_id']
  if user_id == ADMIN_ID:
      if "@bot" in msg:
          find_call(data)
  log('Recieved {}'.format(data))
  return "ok", 200

def send_message(data):
  url  = BASE_URL+'bots/post'
  log(f'message sent: {data["text"]}')
  request = Request(url, urlencode(data).encode())
  js = urlopen(request).read().decode()
  
def make_request(resource, payload):
    url = f'{BASE_URL}/{resource}?token={TOKEN}'
    return requests.get(url=url, params=payload)
  
def find_call(data):
    msg = data['text']
    if '@all' in msg:
        mention_all()
    else:
        not_found()
        
def mention_all():
    members = _get_members()
    data = {'bot_id' : BOT_ID}
    text = ''
    attachments = []
    attach_dict = {'type':'mentions', 'user_ids':[]}
    for mem in members:
        text += ' @'
        text += members[mem]['nickname']
        attach_dict['user_ids'].append(mem)
    data['text'] = text
    data['attachments'] = attachments
    send_message(data)

def not_found():
    data = {
        'bot_id' : BOT_ID
        'text': 'Huh?'
        }
    send_message(not_found)
    
def _get_members():
    member_dict = {}
    response = make_request('groups',{'id':MAIN_GROUP})
    print(response)
    if response.status_code == 200:
        groups_data = response.json()['response']
        for group in groups_data:
            if group['id'] == MAIN_GROUP:
                for member in group['members']:
                    entry = member
                    member_id = entry['user_id']
                    del entry['user_id']
                    member_dict[member_id] = entry
        return member_dict
    return None

def log(msg):
  print(str(msg))
  sys.stdout.flush()
  


