
from bs4 import BeautifulSoup
from pprint import pprint 
import email
from avqmaillib import parse_email
LOCATION = "."


if __name__ == "__main__":
    email_filename = "A0A5CB80A8CD4916957C4D14741C5B69.MAI"
    r = parse_email(email_filename, '.')
    print(r)