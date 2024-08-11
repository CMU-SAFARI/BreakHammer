import wget

url = 'https://zenodo.org/records/13293692/files/cputraces.tar.gz?download=1'

wget.download(url, 'cputraces.tar.gz')