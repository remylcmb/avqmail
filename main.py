
import time
from avqmaillib import get_last_email, parse_email, sanitize
from influxdb import InfluxDBClient
from datetime import datetime
if __name__ == "__main__":
    client = InfluxDBClient(
            host="10.40.38.3",
            port=8089,
            username="admin",
            password="admin123",
            database="avqmail"
    )

    while True:
        last_email_name = get_last_email()
        if not last_email_name:
            print(f'[{datetime.now():%H:%M:%S}] no new mail.')
            time.sleep(30)
            continue
        data = parse_email(last_email_name)
        if data:  
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
                print(json_body)
                r = client.write_points(json_body)
                if r:
                    print(f'[{datetime.now():%H:%M:%S}] data written to influx.')
        else:
            print(f'[{datetime.now():%H:%M:%S}] new email but no data')