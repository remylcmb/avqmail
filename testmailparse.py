
from bs4 import BeautifulSoup
from pprint import pprint 
import email
from avqmaillib import parse_email
LOCATION = "."


if __name__ == "__main__":
    email_filename = "29A007E9A3F24DD2BF3AD334963709C5.MAI"
    r = parse_email(email_filename, '.')
    print(r)