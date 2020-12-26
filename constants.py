# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 15:33:01 2020

@author: James
"""

# SQL 
DB_QUERIES = {
        "CREATE_PR_TABLE" : """
            CREATE TABLE predfined_responses(
                trig TEXT PRIMARY KEY NOT NULL,
                response TEXT NOT NULL
            );
        """,
        "PR_TABLE_EXISTS" : """
            SELECT EXISTS(
                SELECT * FROM predfined_responses
            );
        """,
        "PR_INSERT" : """
            INSERT INTO predfined_responses (trig, response) VALUES ('{}','{}') 
            ON CONFLICT (trig) DO UPDATE SET response = EXCLUDED.response;    
        """,
        "GET_TRIGS" : """
            SELECT trig FROM predfined_responses;
        """,
        "GET_REPLY" : """
            SELECT response FROM predfined_responses WHERE trig = '{}';
        """
    }

# Other
BASE_URL = 'https://api.groupme.com/v3'