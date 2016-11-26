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

if ',' in organism:
    organism = [org.strip() for org in organism.split(',')]
else:
    organism = [organism]

if ',' in license:
    license = [lic.strip() for lic in license.split(',')]
else:
    license = [license]

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

def apply_filter(selection):

    where = []
    t = {}
    for facet in selection:
        filters = []
        for filter in selection[facet]:
            print(filter)
            filters.append(facet + '=:' + filter[0])
            t[filter[0]] = filter[1]
        filters = " OR ".join(filters)
        where.append(filters)
    where = " AND ".join(where)
    print(where)

    c.execute('SELECT * FROM phylopics WHERE ' + where, t)
    for row in c:
        print(row)

selection = {}
if organism != None:
    orgs = []
    for i, org in enumerate(organism):
        orgs.append(['organism_' + str(i), org])
    selection['organism'] = orgs

if license != None:
    lics = []
    for i, lic in enumerate(license):
        lics.append(['license_' + str(i), lic])
    selection['license'] = lics

apply_filter(selection)

conn.commit()
conn.close()
