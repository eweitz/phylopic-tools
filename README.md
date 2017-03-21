# phylopic-tools

Enhanced search for silhouette images of organisms from [PhyloPic](http://phylopic.org/). 

Easily query all PhyloPic SVGs by calling a Python script, using simplied syntax.  Or construct more complex queries in a local SQLite database.  `phylopic-tools` also offers retrieval of organism images by querying higher-level taxonomic names (e.g. Primates), enabled by [ETE3](https://github.com/etetoolkit/ete) and data from [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy).

Features:
* Local copy of all PhyloPic SVG images
* SVGs compressed for better page load times
* Get all PhyloPic SVGs by:
  * Organism (e.g. _Homo sapiens_)
  * Taxonomic descendants (e.g. all Homininae, or all Primates)
  * License (e.g. public domain)
  * Creator (e.g. T. Michael Keesey)

# Installation
## Local copy of all PhyloPic SVG images
Simply clone this repo:
```
$ git clone https://github.com/eweitz/phylopic-tools.git
```
or download and unzip it:
```
$ curl "https://codeload.github.com/eweitz/phylopic-tools/zip/master" -o "phylopic-tools.zip"
$ unzip phylopic-tools.zip
```

## Enhanced search
To enable querying of PhyloPic SVGs, clone this repo as described above, then:
```
$ cd phylopic-tools
$ virtualenv -p python3 env
$ pip install -r requirements.txt
$ python3 query.py --create
```

# Examples

All images of human:
```
python3 query.py --organism "Homo sapiens"
```

All images of primates:
```
python3 query.py --organism "Primates" --descendants
```

All images of chicken or pig:
```
python3 query.py --organism "Gallus gallus,Sus scrofa"
```

All images that are in the public domain
```
python3 query.py --license "zero,mark"
```
All images of Carnivora that are in the public domain:
```
python3 query.py --organism "Carnivora" --descendants --license "zero,mark"
```
