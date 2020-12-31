# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 15:24:13 2020

@author: James
"""
import psycopg2
import boto3
import os
import pandas as pd
import io
from memory_profiler import profile

import app
from constants import DB_QUERIES, S3_BUCKET

class DataAccess():
    def __init__(self, db_url):
        self.db_url = db_url
        self._aws_key_id = os.getenv('AWS_KEY_ID')
        self._aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.s3 = self._get_s3()
    
    # S3 Functions
    def _get_s3(self):
        s3 = boto3.resource(
            service_name='s3',
            region_name='us-east-2',
            aws_access_key_id=self._aws_key_id,
            aws_secret_access_key=self._aws_secret_key
        )
        return s3
    
    @profile
    def get_full_chat(self, file_type='pickle', time_convert=False):
        app._log('fetching chat')
        s3 = self.s3
        obj = s3.Object('groupme-bot',f'full_text.{file_type}')
        if file_type == 'pickle':
            df = pd.read_pickle(io.BytesIO(obj.get()['Body'].read()), 
                                compression='zip')
        elif file_type == 'json':
            df = pd.read_json(io.BytesIO(obj.get()['Body'].read()),  
                              convert_dates=False, convert_axes=False)
            if time_convert:
                df['created_at'] = pd.to_datetime(df['created_at'], unit='ms')
                df.sort_values(by='created_at', inplace=True)
        df.index.name = 'id'
        app._log('returning chat')
        return df
    
    def upload_df(self, df, file_name, extension='.pickle'):
        full_name = file_name+extension
        if extension=='.pickle':
            df.to_pickle(full_name, compression='zip')
        elif extension=='.json':
            df.to_json(full_name)
        else:
            raise Exception('Unsupported file type')
        self.s3.Bucket(S3_BUCKET).upload_file(full_name, full_name)
            
    # SQL Functions 
    def get_triggers(self):
        trig_list = self.execute_query(DB_QUERIES["GET_TRIGS"])
        return_list = []
        if trig_list:
            for trig in trig_list:
                return_list.append(trig[0])
        return return_list
    
    def get_response(self, trig):
        qry = DB_QUERIES["GET_REPLY"].format(trig)
        return self.execute_query(qry)[0][0]
    
    def pr_table_exists(self):
        exist = self.execute_query(DB_QUERIES["PR_TABLE_EXISTS"])
        return exist[0]
    
    def execute_query(self, query):
        conn = psycopg2.connect(self.db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute(query)
        ret = None
        try : 
            ret = cur.fetchall()
        except Exception as err:
            app._log({"Error":err})
        cur.close()
        conn.commit()
        conn.close()
        if ret : 
            app._log({"query returned":ret})
            return ret