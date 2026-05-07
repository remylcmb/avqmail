
import time
from avqmaillib import get_last_email, parse_email, sanitize, insert_morning_checks
from influxdb import InfluxDBClient
from datetime import datetime
import urllib3
urllib3.disable_warnings()

  

if __name__ == "__main__":

    while True:
        last_emails = get_last_email()
        if not last_emails:
            print(f'[{datetime.now():%H:%M:%S}] no new mail.')
            time.sleep(30)
            continue
        else:
            print(f'[{datetime.now():%H:%M:%S}] {len(last_emails)} new mails.')
            for mail in last_emails:
                print(f'[{datetime.now():%H:%M:%S}] parsing file {mail}.')
                parse_email(mail)
            