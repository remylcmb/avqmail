
from bs4 import BeautifulSoup
from pprint import pprint 
import time
from pathlib import Path
import email
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import os
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

    try:
        tree = ET.parse(index_file)
        root = tree.getroot()
        messages = root.findall(".//ELEMENT")
    except ET.ParseError as e:
        print(f'[ERROR] Failed to parse XML File')
        return False
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



def parse_email(email_filename, location="/app"):
    with open(f'{location}/mails/{email_filename}', 'r', encoding='utf-8', errors="ignore") as f:
        content = f.read()
    msg = email.message_from_string(content)
    print(msg['Subject'])
    if "@avaloq." in msg.get('from'):

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode('utf-8', errors="replace")
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors="replace")

        soup = BeautifulSoup(body, 'html.parser')

        #
        # 30MN STATUS MAIL
        #

        if "Readiness_Check_PRD_CMBMC" in msg['Subject']:
            table = soup.find("table")
            headers = [th.get_text(strip=True) for th in table.find_all('th')]

            data = []

            for row in table.find_all('tr')[1:]:
                cols = []
                for i, td in enumerate(row.find_all('td')):
                    if headers[i] == "COMMENT":
                        cols.append(td.decode_contents().replace('\n', ''))  # keep HTML
                    else:
                        cols.append(td.get_text(strip=True))
                
                if cols:
                    data.append(dict(zip(headers, cols)))
            return {
                'email_type':'readiness',
                'data':data
            }

        #
        # Batch morning Checks
        #

        elif "EOD Morning status" in msg['Subject']:
            all_table = soup.find_all('table')
            table = all_table[2]
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            data = []
            for row in table.find_all('tr')[1:]:
                cols = []
                for td in row.find_all('td'):
                    cols.append(td.get_text(strip=True))
                if cols:
                    data.append(dict(zip(headers, cols)))
            
            for row in data:
                if row['Status'] == "COMPLETED NORMAL":
                    row.update({
                        'status':3
                    })
                elif row['Status'] == 'NOT COMPLETED':
                    row.update({
                        'status':2
                    })
                elif row['Status'] == 'COMPLETED ABNORMAL':
                    row.update({
                        'status':1
                    })
                else:
                    row.update({
                        'status':0
                    })
                
                row.pop('Status')
            return {
                'email_type':'morningcheck',
                'data':data
            }
        
        #
        # Task 22 BNP Calypso 
        #
        elif "Calypso" in msg['Subject']:
            if "successfully" in body:
                return {
                    'email_type':'endofday',
                    'data':True
                }
            else:
                return {
                    'email_type':'endofday',
                    'data':False
                }
        return None

def sanitize(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()


