# -*- coding: utf-8 -*-
"""
Created on Fri Jan  1 15:14:12 2021

@author: James
"""
group_info = {
    'name':rgi['name'],
    'description':rgi['description'],
    'image_url':rgi['image_url'],
    'created_at':rgi['created_at']
}
with open('group_info.json', 'w') as file:
    json.dump(group_info, file)
    
messages = []
for ind, row in df2.iterrows():
    entry = {
        "author":row['sender_id'],
        "created_at":row['created_at'],
        'text':row['text'],
        "favorited_by":row['favorited_by'],
        'attachments':row['attachments']
    }
    messages.append(entry)

output = {}
for person in members:
    output[person['user_id']] = {
        "name":person['nickname'],
        "avatar_url":person["img_url"]
    }

with ('people.json', 'w') as file:
    json.dump(output, file)
    
with open('messages.json', 'w') as file:
    json.dump(messages, file)

 att_url = []
for ind, row in df2.iterrows():
    for a in row.attachments:
        if a['type'] == 'image':
            att_url.append(a['url'])
            
for att_url in att_urls:
            file_name = att_url.split('/')[-1]
            att_path = 'attachments/%s.%s' % (file_name, "*")
            att_full_path = os.path.join(output_dir, att_path)
            if len(glob.glob(att_full_path)) == 0:
                r = requests.get(att_url)
                img_type = r.headers['content-type'].split('/')[1]
                att_path = 'attachments/%s.%s' % (file_name, img_type)
                att_full_path = os.path.join(output_dir, att_path)

                with open(att_full_path, 'wb') as fp:
                    fp.write(r.content)
                    
for k, v in output.items():
    url = v['avatar_url']
    if url:
        r = requests.get("%s.avatar" % (url))
        img_type = r.headers['content-type'].split('/')[1]
        avatar_path = os.path.join(avatars_path,
                                   '%s.avatar.%s' % (k, img_type))
        with open(avatar_path, 'wb') as fp:
            fp.write(r.content)