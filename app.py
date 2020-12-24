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
ADMIN_ID = 15629174

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
  data = request.get_json()
  user_id = data['user_id']
  if user_id == ADMIN_ID:
      msg = data['text']
      if "@bot" in msg:
          send_message("What's good")
  log('Recieved {}'.format(data))
  return "ok", 200

def send_message(msg):
  url  = 'https://api.groupme.com/v3/bots/post'

  data = {
          'bot_id' : BOT_ID,
          'text'   : msg,
         }
  log(f'message sent: {msg}')
  request = Request(url, urlencode(data).encode())
  js = urlopen(request).read().decode()
  
def log(msg):
  print(str(msg))
  sys.stdout.flush()
  


