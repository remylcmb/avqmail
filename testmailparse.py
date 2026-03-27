
from bs4 import BeautifulSoup
from pprint import pprint 
import email

LOCATION = "."


if __name__ == "__main__":
    email_filename = "AB3EC074E7674CA58184E04EB1F22997.MAI"
    with open(f'{LOCATION}/mails/{email_filename}', 'r', encoding='utf-8', errors="ignore") as f:
        content = f.read()
    msg = email.message_from_string(content)

    if "Readiness_Check_PRD_CMBMC" in msg['Subject']:
        
        body = msg.get_payload(decode=True).decode()
        soup = BeautifulSoup(body, 'html.parser')
        table = soup.find("table")
        if not table: #the email type is not the 30mn report
            exit(1)
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
        pprint(data)
    elif "Morning status" in msg['Subject']:
        print("Morning check")