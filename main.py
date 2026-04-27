
import time
from avqmaillib import get_last_email, parse_email, sanitize
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
        data = parse_email(last_email_name)
        if data:
            if data['email_type'] == "readiness":
                for row in data['data']:
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
                    write2influx(json_body, data['email_type'])
            if data['email_type'] == "morningcheck":
                json_body = []
                for row in data['data']:
                    json_body.append({
                        "measurement": "avqmorningcheck",
                        "tags": {
                            "milestone":row['Milestone'].replace(' ',''),
                        },
                        "fields": {
                            'status':row['status'],
                            'endtime':row['EndTime']
                        }
                    })
                write2influx(json_body, data['email_type'])

            if data['email_type'] == "endofday":
                json_body = []
                json_body.append({
                    "measurement": "avqendofday",
                    "tags": {
                        "milestone":"calypso",
                    },
                    "fields": {
                        'status': 1 if data['data'] else 0,
                    }
                })
                write2influx(json_body, data['email_type'])
        else:
            print(f'[{datetime.now():%H:%M:%S}] new email but no data')