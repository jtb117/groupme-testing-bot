# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 15:33:01 2020

@author: James
"""
# Group members
ID_TO_NAME = {
        '10319321':'Ethan',
        '10325200':'Harry',
        '12628601':'Jake',
        '13253250':'Jared',
        '13780560':'Maros',
        '13975396':'Billy',
        '15320546':'Andrej',
        '15544849':'Jack',
        '15544851':'Christian',
        '15629174':'JT',
        '15629175':'Quinn',
        '15629209':'Chase',
        '15629210':'Scott',
        '15629485':'Brandon',
        '15638887':'Dan',
        '15638889':'Jacob',
        '15798868':'Dan Schwartz',
        '15982762':'Nikola',
        '16201150':'Arjun',
        '16201239':'Suddy',
        '17723535':'Stadler',
        '20488669':'Shawn',
        '21868143':'Joe',
        '28926628':'Chris Kwiatowski',
        '28927133':'Dalton Graham',
        '34623055':'Jacob Sheftic',
        '39691625':'PPHtNzP',
        '46185459':'Zo',
        '7019642' :'Gordon',
        '754222'  :'Stock Bot',
        '9826240' :'Josh'
    }

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
        """,
        "DEL_TRIG"  : """
            DELETE FROM predfined_responses WHERE trig = '{}';
        """
    }

# API
BASE_URL  = 'https://api.groupme.com/v3'
IMAGE_URL = 'https://image.groupme.com'
HEADERS   = {'content-type': 'application/json',
             'x-access-token': None}

{
  "bot_id"  : "j5abcdefg",
  "text"    : "Hello world",
  "attachments" : [
    {
      "type"  : "image",
      "url"   : "https://i.groupme.com/somethingsomething.large"
    }
  ]
}
