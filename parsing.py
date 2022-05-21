from selenium import webdriver
import requests
from bs4 import BeautifulSoup
# post_id =
# url = "https://m.facebook.com/%"%post_id
url ="https://m.facebook.com/groups/CyMoM/permalink/486264849016293/"
# re = requests.get(url)

# html_doc = re.text

driver = webdriver.Firefox()
driver.get(url)
soup = BeautifulSoup(html_doc, 'html.parser')

print(soup.prettify())