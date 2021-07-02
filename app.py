# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 12:41:20 2020

@author: James Brennan

TODO:
    Pinned messages
"""
import os
import sys
import requests
import io
import pandas as pd
from matplotlib import pyplot as plt

from flask import Flask, request

from DataAccess import DataAccess
from constants import DB_QUERIES, BASE_URL, IMAGE_URL, HEADERS, ID_TO_NAME, IMAGE_SEND_BODY

AWS_KEY_ID = os.getenv('AWS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BOT_ID = os.getenv('GROUPME_BOT_ID')
TOKEN = os.getenv('TOKEN')
MAIN_GROUP = os.getenv('MAIN_GROUP')
ADMIN_ID = os.getenv('ADMIN_ID')
DATABASE_URL = os.getenv('DATABASE_URL')
GM_BOT_ID = '850624'
GROUP_ID  = '29766648'
ALL_DATES = (pd.to_datetime('2010-01-01'), pd.to_datetime('today'))

data_access = DataAccess(DATABASE_URL)

app = Flask(__name__)

# Enter here
@app.route('/', methods=['POST'])
def webhook():
  data = request.get_json()
  if "@bot" in data['text']:
      find_call(data)
      _log('===============FINDING CALL===============')
  else:
      if data['sender_id'] != GM_BOT_ID:
          msg = check_triggers(data['text'])
          if len(msg) > 0:
              flag = msg[-2:]
              if flag == '-i':
                  send_image(msg[:-3])
              elif flag == '-v':
                  send_image(msg[:-3], typ='video')
              else:
                  basic_message(msg)
  return "ok", 200

def send_message(data):
  url  = BASE_URL+'/bots/post'
  _log(f'message sent: {data}')
  request = requests.post(url, json=data)
  return request

def send_image(img_urls, send=True, typ='image'):
    post_body = IMAGE_SEND_BODY
    post_body['bot_id'] = BOT_ID
    for img in img_urls:
        post_body['attachments'].append({
            'type':typ,
            'url':img
        })
    if send: send_message(post_body)
    return post_body

def send_image_context(post_body):
    pass
  
def make_request(resource, payload):
    url = f'{BASE_URL}/{resource}?token={TOKEN}'
    response = requests.get(url=url, params=payload)
    _log('Request to GroupMe: \n\t'+
        f'url: {url}\n\t'+
        f'payload: {payload}\n\t'+
        f'status: {str(response.status_code)}')
    return response
  
def find_call(data):
    text = data["text"][5:]
    command = text.split(' ')[0]
    if command[0] == '!':
        func = CALLS[command]
        if func : func(data)
        else    : command_not_found()
    else:
        command_not_found()
        
def basic_message(msg):
    data = {
        "bot_id" : BOT_ID,
        "text": msg
    }
    send_message(data)
    
def commands(data):
    msg = ''
    for key in CALLS.keys():
        msg+= key+'\n'
    basic_message(msg)

def fuck_jacob(data):
    text = data["text"][11:]
    i = 10
    if len(text) > 0:
        try: i = int(text)
        except: command_not_found()
    for i in range(i):
        basic_message('fuck jacob')
        
def mention_all(data):
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
        if not data_access.table_exists():
            data_access.execute_query(DB_QUERIES["CREATE_PR_TABLE"])
        if "'" in trig:
            start = trig.find("'")
            trig  = trig[:start] + "'" + trig[start:]
        qry = DB_QUERIES["PR_INSERT"].format(trig, response)
        data_access.execute_query(qry)
        msg = f'"{old_trig}" will now trigger "{response}"'
    basic_message(msg)
    
def program(data):
    text = data['text'][8:]
    exec(text)
    
def pinned(data):
    pass    
        
def forget(data):
    text = data['text']
    trig = text[13:]
    trig_list = data_access.get_triggers()
    if trig in trig_list:
        qry  = DB_QUERIES['DEL_TRIG'].format(trig)
        data_access.execute_query(qry)
        msg = f'Removed "{trig}"'
    else : msg = f'Trigger "{trig}" does not exist.'
    basic_message(msg)

def check_triggers(text):
    trig_list = data_access.get_triggers()
    msg = ''
    for trig in trig_list:
        if trig.lower() == text.lower():
            if len(msg) > 0:
                msg += '\n'
            msg += data_access.get_response(trig)
    return msg

def print_triggers(data):
    trig_list = data_access.get_triggers()
    msg = ''
    for trig in trig_list:
        msg += trig + ", "
    if len(msg) > 0 : msg = msg[:-2]
    _log("Printing triggers")
    basic_message(msg)
    
def show_message_count(data):
    df = _get_message_counts()
    _save_likes_figure(df)
    img_url = _upload_image('message_counts.png')
    img_url = [img_url]
    send_image(img_url)
    
def update_data(data):
    msg = 'Beginning update data'
    basic_message(msg)
    _log(msg)
    # get old data
    old_df = data_access.get_full_chat(file_type='json')
    old_df['created_at'] = pd.to_datetime(old_df['created_at'],unit='ms')
    end_of_old = old_df.iloc[-1]['created_at']
    # get new data
    recents = _get_messages()
    new_df = pd.DataFrame(recents)
    recent_start = pd.to_datetime(recents[-1]['created_at'], unit='s')
    before_id = recents[-1]['id']
    # retrieve new messages until overlap
    while (end_of_old < recent_start):
        recents = _get_messages(before_id=before_id)
        new_df = new_df.append(recents)
        before_id = recents[-1]['id']
        recent_start = pd.to_datetime(recents[-1]['created_at'], unit='s')
    # merge dataframes and drop conflicts
    new_df.set_index('id', inplace=True)
    new_df['created_at'] = pd.to_datetime(new_df['created_at'],unit='s')
    updated_df = pd.concat([old_df, new_df])
    updated_df.drop(updated_df.loc[updated_df.index.duplicated()].index)
    updated_df = updated_df.sort_values(by='created_at')
    # upload combined data
    data_access.upload_df(updated_df, 'full_text')
    msg = 'Updated S3 data from {end_of_old} to {recent_start}'
    basic_message(msg)
    _log(msg)
    
def get_random_pic(data):
    try:
        # Parameters
        params = data['text'][17:]
        params = params.split(' ')
        threshold = 0
        start_date = pd.to_datetime('2010-01-01') # TODO: constant
        end_date = pd.to_datetime('today')
        if len(params) == 1 and params[0] != '':
            threshold = params[0]
        elif len(params) >= 2:
            threshold = params[0]
            start_date = pd.to_datetime(params[1])
        if len(params) == 3:
            end_date = pd.to_datetime(params[2])
        if len(params) > 3:
            raise Exception('Invalid input: '+data['text'])
        date_range = (start_date, end_date)
        # Get image
        img_urls = _get_random_pic(threshold, date_range)
        send_image(img_urls)
    except Exception as err:
        basic_message(err)
        _log({"error":err})
    
def command_not_found():
    basic_message("Huh?")
    
def _get_random_pic(threshold=0,date_range=None, context=False):
    df = data_access.get_full_chat()
    df = _get_thresholded_imgs_pd(df, threshold, date_range)
    
    if context:
        pass
    else:
        attachments = df.sample().attachments[0]
        img_urls = []
        for i in attachments:
            if i['type'] == 'image':
                img_urls.append(i['url'])
    return img_urls

def _get_thresholded_imgs_pd(df, threshold, date_range):
    if not 'num_likes' in df.columns:
        df = _add_like_count(df)
    df['is_img'] = df['attachments'].apply(
        lambda x: True in [i['type']=='image' for i in x])
    df = df[df['is_img']] 
    # filter by parameters
    df = df[df['num_likes'] >= threshold] # df only includes those above threshold
    df = df[(df['created_at'] > date_range[0]) & (df['created_at'] < date_range[1])]
    return df

def _add_like_count(df):
    df['num_likes'] = df['favorited_by'].apply(len)
    return df
    
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

def _get_messages(before_id=None, limit=100):
    url = f'https://api.groupme.com/v3/groups/{GROUP_ID}/messages'
    params = {'token':TOKEN,
              'limit':limit,
              'before_id':before_id}
    r = requests.get(url, params=params)
    messages = r.json()['response']['messages']
    return messages

def _log(msg):
  print(str(msg))
  sys.stdout.flush()
  

# ====== Image Functions =====

# Returns dataframe with
#  index: sender_id
#  cols:  message_count, name
def _get_message_counts():
    _log('fetching messages')
    df = data_access.get_full_chat()
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
    
CALLS = {
            "!all":mention_all,
            "!remember":remember,
            "!forget":forget,
            "!triggers":print_triggers,
            "!message-count":show_message_count,
            "!update-data":update_data,
            "!random-pic":get_random_pic,
            "!fuck-jacob":fuck_jacob,
            "!commands":commands,
        }
