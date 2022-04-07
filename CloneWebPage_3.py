import argparse
from bs4 import BeautifulSoup
import os
from requests import get as get_url
import threading
import coloredlogs
import logging

parser = argparse.ArgumentParser(description='''Python script to Clone a Web Page
Author(s) : Sai Kiran Goud, forked by Downj05''')

parser.add_argument('-u', '--url', help='Url to visit', required=True)
parser.add_argument("-v", "--verbose", help="Increase output verbosity",
                    action="store_true")

args = parser.parse_args()

if args.verbose:
    coloredlogs.install(level='DEBUG')
else:
    coloredlogs.intall(level='INFO')



#defining headers as some servers mandiate it
headers = {
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

def worker(element, site_url):
    url = element['href']
    if 'https://' in url or 'http://' in url:
        logging.debug(f'{url} is on external server, not downloading')
        continue

    if url[0] != '/':
        logging.debug(f"Prefixing '/' to {url}")
        url = '/' + url

    filename = url.split('/')[1] # Get filename for saving
    logging.debug(f"Downloading {url}")
    r = get_url(site_url+url, allow_redirects=True)

    with open(filename, 'wb') as f:
        f.write(r.content)
    logging.debug(f"Downloaded {filename}")


logging.info(f'Getting url {args.url}')
response = get_url(url=args.url, headers=headers, allow_redirects=True)
if int(response.status_code) > 299:
    logging.warning(f'Connection responded with non 2xx error code')
else:
    logging.debug(f'Url get successful')


logging.debug('Creating soup parser')
soup = BeautifulSoup(response.text, 'html.parser')

if response.headers.get("Content-Disposition") == None:
    filename = 'index.html'
    logging.debug('No filename specified by web server, using default index.html')
else:
    filename = response.headers.get("Content-Disposition").split("filename=")[1]
    logging.debug(f'Filename specified as {filename}')



directory_name = filename.split('.')[1]
logging.info(f'Make directory {directory_name}')
if os.path.isdir(directory_name):
    logging.info(f'Directory {directory_name} already exists!')
else:
    os.mkdir(directory_name)

logging.debug(f'CD into {directory_name}')
os.chdir(directory_name)
logging.debug(f'Write html to file')

f = open(filename, 'w', encoding='utf-8')
f.write(str(soup))
f.close()

#Get all files
logging.info(f"Get external media")
elements = soup.find_all(href=True) # Has href 
for element in elements:
    

logging.info(f'Site cloned!')