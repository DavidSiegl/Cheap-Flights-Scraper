from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options 
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.keys import Keys
import time
import re
import csv
import argparse
import sys

parser = argparse.ArgumentParser(
    prog = "A webscraper for detecting cheap flights",
    description = "A webscraper tool for detecting cheap flights by scraping the website 'flug.check24.de' for a given one-way flight route. The retrieved data is then generated and saved as a .csv file within the current working directory.",
)

parser.add_argument("-d", "--departure_airport", dest="departure_airport", required=True, type=str, help="Required: Provide the 3-letter code of your departure airport (e. g. VIE for Vienna).")
parser.add_argument("-a", "--arrival_airport", dest="arrival_airport", required=True, type=str, help="Required: Provide the 3-letter code of your arrival airport (e. g. SVQ for Sevilla).")
parser.add_argument("-fd", "--flight_date", dest="flight_date", required=True, type=str, help="Required: Provide the expected date for your flight booking (must be in format YYYY-MM-DD). Note: the scraper takes for the given date a window of +/-3 days into account.")
parser.add_argument("-p", "--passengers", dest="passengers", required=False, type=int, choices=[1,2], help="Optional: Provide the number of passengers for your flight booking (default: 1 passenger).")
parser.add_argument("-t", "--travel_time", dest="travel_time", required=False, type=int, help="Optional: Provide the maximum number of hours you would like your flight to take.")

args = parser.parse_args()

departure_airport = args.departure_airport
arrival_airport = args.arrival_airport
flight_date = args.flight_date
passengers = args.passengers
travel_time = args.travel_time

pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
if not re.match(pattern, flight_date):
    print("Invalid date format. Please enter date in the format YYYY-MM-DD.")
    sys.exit(1)

options = Options()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options, service=Service(executable_path=GeckoDriverManager().install()))

driver.get("https://flug.check24.de/")

driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/div[3]/a[2]").click()
time.sleep(2)

if passengers == 2:
    driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[2]/div[1]/div/div[2]/div/div[1]/div/div/div[5]/div/div").click()
    driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[2]/div[1]/div/div[2]/div/div[1]/div/div/div[5]/div/div/div[2]/div/div[1]/div/div/div/ul/li[1]/div[2]/button[2]").click()
    driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[2]/div[1]/div/div[2]/div/div[1]/div/div/div[5]/div/div/div[2]/div/div[1]/div/div/button").click()

driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[2]/div[1]/div/div[2]/div/div[1]/div/div/div[2]").click()
driver.find_element(By.ID, "fl-airportOrigin1").send_keys(departure_airport, Keys.TAB)
driver.find_element(By.ID, "fl-airportDestination1").send_keys(arrival_airport, Keys.TAB)
driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[2]/div[1]/div/div[2]/div/div[2]/div/div[4]/div/div[2]/div/div/div[1]/div/div/div").click()
driver.find_element(By.XPATH,"/html/body/div[3]/div[2]/div/div/div/main/div[2]/div[1]/div/div[2]/div/div[2]/div/div[4]/div/div[2]/div/div/div[1]/div/div/div/select/option[4]").click()

# iterating through date navigation until requested date is found
date_element_found = False
while not date_element_found:
    try:
        datetime_element = driver.find_element(By.XPATH, "//time[@datetime='" + flight_date + "']")
        datetime_value = datetime_element.get_attribute("datetime")
        parent_element = datetime_element.find_element(By.XPATH, "..")
        parent_element.click()
        date_element_found = True
    except NoSuchElementException:
        driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[2]/div[1]/div/div[2]/div/div[2]/div/div[4]/div/div[2]/div/div/div[2]/div/div/div[2]/div/div[2]/button").click()

driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[2]/div[1]/div/div[2]/div/div[2]/div/div[5]/button").click()


# next page
time.sleep(2)

# manipulating url string for correct filter settings
current_url = driver.current_url

if type(travel_time) is not type(None):
    current_url = current_url + "travelTime2/3600," + str(travel_time * 3600) # setting travel time cutoff

modified_url = re.sub(r"ow\/*\w+\/\w+", "ow/" + departure_airport + "/" + departure_airport, current_url)
modified_url = re.sub(r"(\d\d\.\d\d\.\d\d\d\d\/)(\w+\/\w+)", lambda match: match.group(1) + arrival_airport + "/" + arrival_airport, modified_url, count=1)
driver.get(modified_url)

time.sleep(5)
driver.find_element(By.XPATH, "//button[@data-testid='filter_transferCount_1']").click() # setting max. 1 transfer

time.sleep(15)
driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[1]/div/div[2]/div/div[2]/ul/li[2]/button").click()

# retrieving flights data (excluding banner elements in loop)
ls_rows = []

for i in range(1, 18):

    if i == 2 or i == 4:
        continue
    else:
        try:
            ls_temp = []
            departure = driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[1]/div/div[2]/div/div[2]/div[1]/div[" + str(i) + "]/div[1]/div/div/div[1]/div[1]/strong").text
            arrival = driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[1]/div/div[2]/div/div[2]/div[1]/div[" + str(i) + "]/div[1]/div/div/div[1]/div[3]/strong").text
            price = driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[1]/div/div[2]/div/div[2]/div[1]/div[" + str(i) + "]/div[2]/div/div[3]/div[1]/strong").text
            stops = driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[1]/div/div[2]/div/div[2]/div[1]/div[" + str(i) + "]/div[1]/div/div/div[1]/div[2]/span[2]").text
            try: # checking for airport change exception
                driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[1]/div/div[2]/div/div[2]/div[1]/div[" + str(i) + "]/div[1]/div/div/div[2]/span")
                line = driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[1]/div/div[2]/div/div[2]/div[1]/div[" + str(i) + "]/div[1]/div/div/div[3]/div/span").text
            except NoSuchElementException:
                line = driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div/main/div[1]/div/div[2]/div/div[2]/div[1]/div[" + str(i) + "]/div[1]/div/div/div[2]/div/span").text
            ls_temp.append(departure_airport)
            ls_temp.append(arrival_airport)
            ls_temp.append(departure)
            ls_temp.append(arrival)
            ls_temp.append(price)
            ls_temp.append(stops)
            ls_temp.append(line)
            ls_rows.append(ls_temp)
        except NoSuchElementException:
            break

time.sleep(5)
driver.quit()

header = ["von", "nach", "abflug", "ankunft", "preis", "stops", "fluglinie"]

with open(departure_airport + "_" + arrival_airport + "_" + flight_date + ".csv", "w") as file:
    write = csv.writer(file)
    write.writerow(header)
    write.writerows(ls_rows)
