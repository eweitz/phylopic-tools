import argparse
import json
import os
import sqlite3
import textwrap

from ete3 import NCBITaxa

parser = argparse.ArgumentParser(
    description='Query local PhyloPics database',
    epilog=textwrap.dedent('''
        EXAMPLES:

        All images of human:
        python3 query.py --organism "Homo sapiens"

        All images of primates:
        python3 query.py --organism "Primates" --descendants

        All images of chicken or pig:
        python3 query.py --organism "Gallus gallus,Sus scrofa"

        All images that are in the public domain
        python3 query.py --license "zero,mark"

        All images of Carnivora that are in the public domain:
        python3 query.py --organism "Carnivora" --descendants --license "zero,mark"
        '''),
    formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument('--create', dest='create', action='store_true',
                    help='Create local PhyloPics database and dependencies')

parser.add_argument('--organism', dest='organism',
                    help='Organism filter, e.g. "Homo sapiens"')
parser.add_argument('--taxid', dest='taxid',
                    help='NCBI Taxonomy ID filter, e.g. 9606')
parser.add_argument('--descendants', dest='descendants', action='store_true',
                    help='Include descendant taxa of "organism" filter')

parser.add_argument('--license', dest='license',
                    help='License filter, e.g. zero')
parser.add_argument('--credit', dest='credit',
                    help='Credit filter e.g. "T. Michael Keesey"')
args = parser.parse_args()

create = args.create
organism = args.organism
taxid = args.taxid
descendants = args.descendants
license = args.license
credit = args.credit

ncbi = NCBITaxa()

conn = sqlite3.connect('phylopics.db')
c = conn.cursor()

def normalize_organism(organism, ncbi_cursor):
    '''Normalizes PhyloPic organism name to one in NCBI Taxonomy database'''

    words = organism.split()

    ncbi_cursor.execute('SELECT taxid FROM synonym WHERE spname = ?', (organism, ))
    for taxid in ncbi_cursor:
        #print('Normalization success: ' + organism)
        return ncbi.get_taxid_translator([taxid])[taxid]

    if len(words) > 2:
        normalized_organism = ' '.join(words[:2])
        if len(ncbi.get_name_translator([normalized_organism])) > 0:
            #print('Normalization success: ' + normalized_organism)
            return normalized_organism
        else:
            #print('Normalization failure: ' + organism)
            return organism
    else:
        #print('Normalization failure; len(words) <= 2: ' + organism)
        return organism


def create_db():

    if os.path.exists(ncbi.dbfile) == False:
        ncbi.update_taxonomy_database()

    ncbi_conn = sqlite3.connect(ncbi.dbfile)
    ncbi_cursor = ncbi_conn.cursor()

    c.execute('''DROP TABLE IF EXISTS phylopics''')
    c.execute('''CREATE TABLE phylopics (organism text,
                 uid text, license text, credit text, slug text)''')

    phylopics = []
    with open('images_metadata.json') as f:
        image_data = json.loads(f.read())['images']

    for image in image_data:

        organism = image['organism']
        if len(ncbi.get_name_translator([organism])) == 0:
            organism = normalize_organism(organism, ncbi_cursor)

        phylopics.append((
            organism,
            image['uid'],
            image['license'],
            image['credit'],
            image['slug']
        ))

    c.executemany('INSERT INTO phylopics VALUES (?,?,?,?,?)', phylopics)


def add_descendants(selection):
    organisms = selection['organism']
    new_orgs = organisms.copy()
    num_orgs = len(organisms)
    for pair in organisms:
        organism = pair[1]
        descendants = ncbi.get_descendant_taxa(organism, intermediate_nodes=True)
        descendants = ncbi.get_taxid_translator(descendants)
        descendants = list(descendants.values())
        for i, descendant in enumerate(descendants):
            new_orgs.append(['organism_' + str(num_orgs + i), descendant])
    selection['organism'] = new_orgs
    return selection


def get_selection():
    global organism, taxid, descendants, organism, license, credit
    selection = {}
    if taxid != None:
        if ',' in taxid:
            taxid = [int(t) for t in taxid.split(',')]
            taxid_orgs = ncbi.get_taxid_translator(taxid)
            organism = [taxid_orgs[t] for t in taxid_orgs]
        else:
            taxid = int(taxid)
            organism = [ncbi.get_taxid_translator([taxid])[taxid]]
        organism = ','.join(organism)
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

    if organism != None and descendants != False:
        selection = add_descendants(selection)

    return selection


def faceted_search(selection):

    where = []
    t = {}
    for facet in selection:
        filters = []
        for filter in selection[facet]:
            # print(filter)
            filters.append(facet + '=:' + filter[0])
            t[filter[0]] = filter[1]
        filters = '(' + ' OR '.join(filters) + ')'
        where.append(filters)
    where = ' AND '.join(where)
    #print(where)

    c.execute('SELECT slug FROM phylopics WHERE ' + where, t)
    for row in c:
        print('images/' + row[0] + '.svg')

if create != None:
    create_db()

selection = get_selection()

if len(selection.keys()) > 0:
    faceted_search(selection)

conn.commit()
conn.close()
