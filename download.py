import argparse
from bs4 import BeautifulSoup
import os
from requests import get as get_url
import threading
import coloredlogs
import logging
from time import sleep

parser = argparse.ArgumentParser(description='''Python script to Clone a Web Page
Author(s) : Sai Kiran Goud, forked by Downj05''')

parser.add_argument('-u', '--url', help='Url to visit', required=True)
parser.add_argument('-o', '--output', help='Output Directory')
parser.add_argument('-n', '--name', help='HTML file name to save, e.g [name].html')
parser.add_argument("-v", "--verbose", help="Increase output verbosity",
                    action="store_true")

args = parser.parse_args()

if args.verbose:
    coloredlogs.install(level='DEBUG')
else:
    coloredlogs.install(level='INFO')



#defining headers as some servers mandiate it
headers = {
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

worker_array = []

def worker(element, site_url, index):
    try:
        url = element['href']
        if 'https://' in url or 'http://' in url:
            logging.debug(f'[{index}] {url} is on external server, not downloading')
            return

        if len(url) < 2:
            logging.debug(f'[{index}] {element} href is not a url, not downloading')
            return
        if url[0] != '/':
            logging.debug(f"[{index}] Prefixing '/' to {url}")
            url = '/' + url

        filename = url.split('/')[1] # Get filename for saving
        logging.debug(f"[{index}] Downloading {url}")
        r = get_url(site_url+url, allow_redirects=True)

        with open(filename, 'wb') as f:
            f.write(r.content)
        logging.info(f"[{index}] Downloaded {filename}")
    except Exception as e:
        logging.error(f"[{index}] Error when downloading {url}, filename {filename} from {element}. \n{e}")
    finally:
        worker_array[index] = 0 # zero equals finished



if __name__ == '__main__':

    # GET url, receive response
    logging.info(f'Getting url {args.url}')
    response = get_url(url=args.url, headers=headers, allow_redirects=True)
    if int(response.status_code) > 299:
        logging.warning(f'Connection responded with non 2xx error code')
    else:
        logging.debug(f'Url get successful')

    # Create BS4 parser
    logging.debug('Creating soup parser')
    soup = BeautifulSoup(response.content.decode('utf-8', 'ignore'), 'html.parser')

    # Get filename
    if response.headers.get("Content-Disposition") == None and args.name == None: # Webserver and user didnt specify filename
        filename = 'index.html'
        logging.debug('No filename specified by web server or user, using default index.html')

    elif args.name == None and response.headers.get("Content-Disposition") != None: # User didnt specify filename but webserver did
        filename = response.headers.get("Content-Disposition").split("filename=")[1]
        logging.debug(f'No provieded filename, webserver specified filename as {filename}')

    else: # User must have specified filename
        filename = args.name+'.html'
        logging.debug(f'Using user specified filename {filename}')

    if args.output is None: # No specified directory name
        directory_name = filename.split('.')[1]
    else: # Specified directory name
        directory_name = args.output
        
    # Make directory
    logging.info(f'Make directory {directory_name}')
    if os.path.isdir(directory_name):
        logging.info(f'Directory {directory_name} already exists!')
    else:
        os.mkdir(directory_name)

    logging.debug(f'CD into {directory_name}')
    os.chdir(directory_name)
    logging.debug(f'Write html to file')

    # Write HTML to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(soup.prettify()) # Prettify HTML before saving

    #Get all files
    logging.info(f"Get external media")
    elements = soup.find_all(href=True) # Has href 
    for elemement in elements: # we do this before making threads to prevent concurrency errors
        worker_array.append(1) # 1 equals job due

    for index,element in enumerate(elements):
        t = threading.Thread(target=worker, args=(element, args.url, index))
        
        t.start()
        logging.debug(f"Create thread [{index}] and append to worker array [{len(worker_array)}]")

    while 1 in worker_array:
        sleep(0.1)
        
    logging.info(f"Finished download")