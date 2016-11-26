import argparse
import json
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument('--create', dest="create",
                    help='Create local PhyloPics database')
parser.add_argument('--organism', dest="organism",
                    help='Organism filter, e.g. "Homo sapiens"')
parser.add_argument('--license', dest="license",
                    help='License filter, e.g. zero')
parser.add_argument('--credit', dest="credit",
                    help='Credit filter e.g. "T. Michael Keesey"')
args = parser.parse_args()

create = args.create
organism = args.organism
license = args.license
credit = args.credit

conn = sqlite3.connect('phylopics.db')
c = conn.cursor()

def create_db():
    c.execute('''CREATE TABLE phylopics
                 (organism text, uid text, license text, credit text)''')
    phylopics = []
    with open('images_metadata.json') as f:
        image_data = json.loads(f.read())['images']

    for image in image_data:
        phylopics.append((
            image['organism'],
            image['uid'],
            image['license'],
            image['credit']
        ))

    c.executemany('INSERT INTO phylopics VALUES (?,?,?,?)', phylopics)

def filter(selection):
    where = selection[0][0] + ' = ?'
    t = (selection[1][0], )
    c.execute('SELECT * FROM phylopics WHERE ' + where, t)
    for row in c:
        print(row)

selection = [[], []]
if organism != None:
    selection[0].append('organism')
    selection[1].append(organism)

filter(selection)

conn.commit()
conn.close()
