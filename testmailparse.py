
from bs4 import BeautifulSoup
from pprint import pprint 
import email
from avqmaillib import parse_email
import pymysql
from datetime import datetime

# Connexion
conn = pymysql.connect(
    host="10.117.10.1",
    user="grafana",
    password="grafanapassword",
    database="monitoring",
)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS emailreporting (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        check_date  DATE         NOT NULL,
        rpa_id      VARCHAR(100) NOT NULL,
        description VARCHAR(255),
        status      TINYINT(1),
        comment     TEXT,
        inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uq_date_rpa (inserted_at, rpa_id)
    )
""")
LOCATION = "."


if __name__ == "__main__":
    email_filename = "09494BFE8F1246D2801C4ED48DFF2536.MAI"
    r = parse_email(email_filename, '.')
    records = []
    for row in r['data']:
        rpa_id = row.get('RPA ID')
        if not rpa_id:
            continue
        records.append({
            "check_date": datetime.today().date(),
            "rpa_id":     rpa_id,
            "description": row.get('DESCRIPTION'),
            "status":     1 if row.get(' ') == "OK" else 0,
            "comment":    row.get('COMMENT')
        })

    insert_query = """
        INSERT INTO emailreporting (check_date, rpa_id, description, status, comment)
        VALUES (%(check_date)s, %(rpa_id)s, %(description)s, %(status)s, %(comment)s)
        ON DUPLICATE KEY UPDATE
            status      = VALUES(status),
            comment     = VALUES(comment),
            description = VALUES(description),
            inserted_at = CURRENT_TIMESTAMP
    """

    cursor.executemany(insert_query, records)
    conn.commit()