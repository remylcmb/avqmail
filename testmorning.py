
from bs4 import BeautifulSoup
from pprint import pprint 
import email
from avqmaillib import parse_email
import pymysql
from datetime import datetime
from pprint import pprint



def morning_check(data):
    conn = pymysql.connect(
        host="10.117.10.1",
        user="grafana",
        password="grafanapassword",
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

    for row in data['data']:
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

    cursor.executemany(insert_query, records)
    conn.commit()


if __name__ == "__main__":
    email_filename = "33EF0922CAE24E02A2498F62D65396D9.MAI"
    r = parse_email(email_filename, '.')
    morning_check(r)