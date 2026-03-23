
from bs4 import BeautifulSoup
from pprint import pprint 
import time
from pathlib import Path
import email
import xml.etree.ElementTree as ET
from pathlib import Path
import re
#LOCATION = '/opt/docker_containers/avqmail'
#in contaienr, uncomment:
LOCATION = '/app'
def get_last_email():
    """
    return the last email FILENAME or False if it was already inserted

    """
    index_file = f'{LOCATION}/mails/_index.xml'
    processed_file = f'{LOCATION}/processed_emails.txt'
    with open(processed_file, "r") as f:
        processed = set(line.strip() for line in f)

    tree = ET.parse(index_file)
    root = tree.getroot()
    messages = root.findall(".//ELEMENT")

    if not messages:
        return False
    else:
        new_messages = []

        for msg_elem in messages:
            filename = msg_elem.attrib.get('ID')
            if filename not in processed and filename != "DEFAULT.MAI":
                print(f"New email detected: {filename}")
                new_messages.append(filename)
                

        if new_messages:
            with open(processed_file, "a") as f:
                for filename in new_messages:
                    f.write(filename + "\n")
        else:
            return False
    return filename



def parse_email(email_filename):
    with open(f'{LOCATION}/mails/{email_filename}', 'r', encoding='utf-8', errors="ignore") as f:
        content = f.read()
    msg = email.message_from_string(content)
    if "@avaloq.ch" in msg.get('from'):

        body = msg.get_payload(decode=True).decode()
        soup = BeautifulSoup(body, 'html.parser')
        table = soup.find("table")
        if not table: #the email type is not the 30mn report
            return None
        headers = [th.get_text(strip=True) for th in table.find_all('th')]

        data = []

        for row in table.find_all('tr')[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all('td')]
            if cols:
                data.append(dict(zip(headers,cols)))
        return data


def sanitize(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()

