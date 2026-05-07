
from bs4 import BeautifulSoup
from pprint import pprint 
import time
from pathlib import Path
import email
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import os
import pymysql
from datetime import datetime
import urllib3
urllib3.disable_warnings()
from influxdb import InfluxDBClient
import os

def write2influx(body):
    influx_za = InfluxDBClient(
            host="influxdbreporting.za.cmb.mc",
            port=8086,
            username="admin",
            password="admin123",
            database="avqmail",
            ssl=True
    )
    influx_bank = InfluxDBClient(
            host="influxdb.cmb.mc",
            port=8086,
            username="admin",
            password="UMzyWJgJJwscj98",
            database="avqmail",
            ssl=True
    )
    r_za = influx_za.write_points(body)
    r_bank = influx_bank.write_points(body)


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
                new_messages.append(filename)
                

        if new_messages:
            with open(processed_file, "a") as f:
                for filename in new_messages:
                    f.write(filename + "\n")
        else:
            return False
    return new_messages

def insert_morning_checks(data):
    conn = pymysql.connect(
        host="10.117.10.1",
        user="grafana",
        password=os.environ.get('sql_pwd'),
        database="monitoring",
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avqmorningcheck (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            endtime  DATE         NOT NULL,
            milestone      VARCHAR(100) NOT NULL,
            status VARCHAR(255),
            inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_date_mc (inserted_at, milestone)
        )
    """)

    records = []

    for row in data:
        records.append({
            "endtime": row['EndTime'],
            "milestone": row['Milestone'],
            "status": row['Status']
        })

    insert_query = """
        INSERT INTO avqmorningcheck (endtime, milestone, status)
        VALUES (%(endtime)s, %(milestone)s, %(status)s)
        ON DUPLICATE KEY UPDATE
            endtime      = VALUES(endtime),
            milestone     = VALUES(milestone),
            status = VALUES(status),
            inserted_at = CURRENT_TIMESTAMP
    """
    
    print(f'[{datetime.now():%H:%M:%S}] {len(records)} records written to SQL')
    cursor.executemany(insert_query, records)
    conn.commit()



def parse_email(email_filename, location="/app", debug=False):
    with open(f'{location}/mails/{email_filename}', 'r', encoding='utf-8', errors="ignore") as f:
        content = f.read()
    msg = email.message_from_string(content)
    if "@avaloq." in msg.get('from'):

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode('utf-8', errors="replace")
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors="replace")
        print(f'[{datetime.now():%H:%M:%S}] Parsing email: {msg["Subject"]}')
        soup = BeautifulSoup(body, 'html.parser')

        #
        # 30MN STATUS MAIL
        #
        if debug:
            return msg['Subject']

        
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
            
            for row in data:
                rpa_id = row.get('RPA ID')
                if not rpa_id:
                    continue
                metric_name = sanitize(rpa_id)
                json_body = [{
                    "measurement": "emailreportingn",
                    "tags": {
                        "description":row.get('DESCRIPTION'),
                        'metric_name':metric_name
                    },
                    "fields": {
                        'status':1 if row.get('STATUS') == "OK" else 0,
                        'comment':row.get('COMMENT')
                    }
                }]
                write2influx(json_body)
            print(f'[{datetime.now():%H:%M:%S}] {len(data)} records written to InfluxDB')
            print(f'[{datetime.now():%H:%M:%S}] - *End of Readiness*')
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
            
            insert_morning_checks(data)
            print(f'[{datetime.now():%H:%M:%S}] - *End of Morning Check*')
        
        #
        # Task 22 BNP Calypso 
        #
        elif "Calypso" in msg['Subject']:
            data = {
                "endtime": datetime.now(),
                "milestone": 'Calypso',
                "status": "OK" if "successfully" in body else "FAILED"
            }
            insert_morning_checks(data)
            print(f'[{datetime.now():%H:%M:%S}] - *End of Calypso*')
            
        return None

def sanitize(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()


