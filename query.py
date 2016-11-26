import argparse
import json
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument('--create', dest='create',
                    help='Create local PhyloPics database')
parser.add_argument('--organism', dest='organism',
                    help='Organism filter, e.g. "Homo sapiens"')
parser.add_argument('--license', dest='license',
                    help='License filter, e.g. zero')
parser.add_argument('--credit', dest='credit',
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


def get_selection():
    selection = {}
    raw_facets = [
        ['organism', organism],
        ['license', license],
        ['credit', credit]
    ]
    for pair in raw_facets:
        name = pair[0]
        raw_filter = pair[1]
        if raw_filter == None:
            continue
        filters = []
        if ',' in raw_filter:
            raw_filter = raw_filter.split(',')
            for i, filt in enumerate(raw_filter):
                filters.append([name + '_' + str(i), filt.strip()])
        else:
            filters.append([name, raw_filter])
        selection[name] = filters

    return selection


def faceted_search(selection):

    where = []
    t = {}
    for facet in selection:
        filters = []
        for filter in selection[facet]:
            print(filter)
            filters.append(facet + '=:' + filter[0])
            t[filter[0]] = filter[1]
        filters = '(' + ' OR '.join(filters) + ')'
        where.append(filters)
    where = ' AND '.join(where)
    #print(where)

    c.execute('SELECT * FROM phylopics WHERE ' + where, t)
    for row in c:
        print(row)

selection = get_selection()

if len(selection.keys()) > 0:
    faceted_search(selection)

conn.commit()
conn.close()
