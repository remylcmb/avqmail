
import time
from avqmaillib import get_last_email, parse_email, sanitize, insert_morning_checks
from influxdb import InfluxDBClient
from datetime import datetime
import urllib3
urllib3.disable_warnings()



def write2influx(body, emailtype):
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
    if r_za:
        print(f'[{datetime.now():%H:%M:%S}] - {emailtype} written to influx ZA.')
    else:
        print(f'[{datetime.now():%H:%M:%S}] - ERROR - failed to write {emailtype} to influx ZA.')
    if r_bank:
        print(f'[{datetime.now():%H:%M:%S}] - {emailtype} written to influx Bank.')
    else:
        print(f'[{datetime.now():%H:%M:%S}] - ERROR - failed to write {emailtype} to influx Bank.')
    

if __name__ == "__main__":

    while True:
        last_email_name = get_last_email()
        if not last_email_name:
            print(f'[{datetime.now():%H:%M:%S}] no new mail.')
            time.sleep(30)
            continue
        else:
            parse_email(last_email_name)
            print(f'[{datetime.now():%H:%M:%S}] new email!')