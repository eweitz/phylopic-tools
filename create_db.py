import json
import sqlite3


conn = sqlite3.connect('phylopics.db')
c = conn.cursor()
c.execute('''CREATE TABLE phylopics
             (organism text, uid text, license text, credit text)''')
phylopics = []
with open('images_metadata.json') as f:
    image_data = json.loads(f.read().decode('utf-8'))['images']

for image in image_data:
    phylopics.append((
        image['organism'],
        image['uid'],
        image['license'],
        image['credit']
    ))

c.executemany('INSERT INTO phylopics VALUES (?,?,?,?)', phylopics)
conn.commit()
conn.close()
