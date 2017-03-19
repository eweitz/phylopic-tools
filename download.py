import json
import os
import re
import subprocess
import sqlite3
import urllib.request
import xml.etree.ElementTree as ET

phylopic_url = 'http://phylopic.org'
api_url = phylopic_url + '/api/a'
count_url = api_url + '/image/count'

ET.register_namespace('', 'http://www.w3.org/2000/svg')
ET.register_namespace('dc', 'http://dublincore.org/documents/dcmi-terms/')

def get_json(response):
    return json.loads(response.read().decode('utf-8'))

def get_metadata(name, uid, license_url, creator):
    source = 'http://phylopic.org/image/' + uid
    description = (
        'Silhouette of ' + name + ', ' +
        'processed by PhyloPic Tools ' +
        '(https://github.com/eweitz/phylopic-tools)'
    )
    creator_element = ''
    if creator != None:
        creator_element = '<dc:creator>' + creator + '</dc:creator>'
    metadata = (
        '<metadata xmlns:dc="http://dublincore.org/documents/dcmi-terms/">' +
          '<dc:description>' + description + '</dc:description>' +
          '<dc:source>' + source + '</dc:source>' +
          creator_element +
          '<dc:license>' + license_url + '</dc:license>' +
        '</metadata>'
    )
    return metadata

print('Fetching total image count from PhyloPic...')
with urllib.request.urlopen(count_url) as f:
    count = str(get_json(f)['result'])
print('Total PhyloPic images: ' + count)

#count = '10' # DEBUG
options = 'string+credit+licenseURL+directNames'
images_url = api_url + '/image/list/0/' + count + '?options=' + options

license_names = {
    'http://creativecommons.org/licenses/by/3.0/': 'by',
    'http://creativecommons.org/licenses/by-nc/3.0/': 'by-nc',
    'http://creativecommons.org/licenses/by-nc-sa/3.0/': 'by-nc-sa',
    'http://creativecommons.org/licenses/by-sa/3.0/': 'by-sa',
    'http://creativecommons.org/publicdomain/mark/1.0/': 'mark',
    'http://creativecommons.org/publicdomain/zero/1.0/': 'zero'
}

print('Fetching all image URLs...')
with urllib.request.urlopen(images_url) as f:
    image_data = get_json(f)['result']

taxon_image_count = {}

phylopics_data = []

for i, d in enumerate(image_data):
    print(str(i) + ' of ' + count + ': ' + str(d))

    uid = d['uid']

    license_url = d['licenseURL']
    license = license_names[license_url]

    #if license not in set(('mark', 'zero')):
    #      continue

    credit = d['credit']

    if len(d['directNames']) == 0:
        #  e.g. http://phylopic.org/api/a/image/5e0d65db-501f-4e21-8a6c-a4791afcbc6f?options=directName
        continue

    # Names of organism this image depicts
    name_uid = d['directNames'][0]['uid']

    options = 'string+type+citationStart'
    name_url = api_url + '/name/' + name_uid + '?options=' + options
    with urllib.request.urlopen(name_url) as f:
        name_data = get_json(f)['result']

    citation_start = name_data['citationStart']
    name = name_data['string']
    if citation_start:
        name = name[:citation_start].strip()
    #name_type = name_data['type']
    slug_name = name.lower().replace(' ', '-')

    # Append a number when there are multiple images for the same taxon
    if slug_name not in taxon_image_count:
        taxon_image_count[slug_name] = 1
    else:
        taxon_image_count[slug_name] += 1
        slug_name += "_" + str(taxon_image_count[slug_name]) # e.g. homo-sapiens_2

    svg_url = phylopic_url + '/assets/images/submissions/' + uid + '.svg'
    try:
        with urllib.request.urlopen(svg_url) as f:
            svg_raw = f.read().decode('utf-8')
            svg_xml = ET.fromstring(svg_raw)
            metadata_raw = get_metadata(name, uid, license_url, credit)
            metadata = ET.fromstring(metadata_raw)
            svg_xml.insert(0, metadata)
            svg_etree = ET.ElementTree(svg_xml)


    except urllib.error.HTTPError as e:
        continue
    phylopics_data.append({
        'organism': name,
        'uid': uid,
        'license': license,
        'credit': credit,
        'slug': slug_name
    })
    #open('images/' + slug_name + '.svg', 'w').write(svg)
    svg_etree.write('images/' + slug_name + '.svg',
           xml_declaration=False, method="xml")

phylopics_data = {'images': phylopics_data}
open('images_metadata.json', 'w').write(json.dumps(phylopics_data))

for base_dir, dirs, files in os.walk('images'):
    for file_name in files:
        file_path = 'images/' + file_name
        file_size = os.path.getsize(file_path) # in bytes
        if file_size > 4E6: # > 4 MB
            print('File too large (' + str(file_size) + '): ' + file_path)
            os.remove(file_path)

subprocess.call(['svgo', '--disable', 'removeMetadata', '-f', 'images'])
