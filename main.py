
import time
from avqmaillib import get_last_email, parse_email, sanitize
from influxdb import InfluxDBClient
from datetime import datetime




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
    if r_za:
        print(f'[{datetime.now():%H:%M:%S}] - readiness written to influx ZA.')
    if r_bank:
        print(f'[{datetime.now():%H:%M:%S}] - readiness written to influx Bank.')


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
                    write2influx(json_body)
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
                            'endtime':row['endTime']
                        }
                    })
                write2influx(json_body)
        else:
            print(f'[{datetime.now():%H:%M:%S}] new email but no data')