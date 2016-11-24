import json
import re
import subprocess
import sqlite3
import urllib.request

phylopic_url = 'http://phylopic.org'
api_url = phylopic_url + '/api/a'
count_url = api_url + '/image/count'

def get_json(response):
    return json.loads(response.read().decode('utf-8'))

with urllib.request.urlopen(count_url) as f:
    count = str(get_json(f)['result'])

#count = '10'
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

with urllib.request.urlopen(images_url) as f:
    image_data = get_json(f)['result']

taxon_image_count = {}

phylopics_data = []

for d in image_data:
    print(d)

    uid = d['uid']

    license = license_names[d['licenseURL']]
    print(license)
    if license not in set(('mark', 'zero')):
        continue

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

    if slug_name not in taxon_image_count:
        taxon_image_count[slug_name] = 1
    else:
        taxon_image_count[slug_name] += 1
        slug_name += "_" + str(taxon_image_count[slug_name]) # e.g. homo-sapiens_2

    svg_url = phylopic_url + '/assets/images/submissions/' + uid + '.svg'
    try:
        with urllib.request.urlopen(svg_url) as f:
            svg = f.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        continue
    phylopics_data.append({
        'organism': name,
        'uid': uid,
        'license': license,
        'credit': credit
    })
    open('images/' + slug_name + '.svg', 'w').write(svg)

phylopics_data = {'images': phylopics_data}
open('images_metadata.json', 'w').write(json.dumps(phylopics_data))

subprocess.call(['svgo', '-f', 'images'])
