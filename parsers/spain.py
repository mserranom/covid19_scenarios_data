import sys
import requests
import csv
import io
import datetime
import unidecode

from .utils import write_tsv

LOC = "case-counts/Europe/Southern Europe/Spain"
cols = ['time', 'cases', 'deaths', 'hospitalized', 'ICU', 'recovered']

cases_url = 'https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_casos.csv'
deaths_url = 'https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_fallecidos.csv'
icu_url = 'https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_uci.csv'
recovered_url = 'https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_altas.csv'


# ------------------------------------------------------------------------
# Functions

def get_region_dict(url):
    r = requests.get(url)
    if not r.ok:
        print(f"Failed to fetch {url}", file=sys.stderr)
        r.close()
        exit(1)

    fd = io.StringIO(r.text)
    rdr = csv.reader(fd)
    hdr = next(rdr)
    days = list(hdr)[2:]  # days start in the 3rd column

    # 'data' is a dictionary using region name as key. Values are also dictionaries,
    # using the date as key
    data = {}
    for row in rdr:
        region = unidecode.unidecode(row[1])
        region_data = {}
        current_col = 2 # because days start in the 3rd column
        for day in days:
            region_data[day] = row[current_col]
            current_col = current_col + 1
        data[region] = region_data
    return data


# ------------------------------------------------------------------------
# Main point of entry

def parse():
    data_cases = get_region_dict(cases_url)
    data_deaths = get_region_dict(deaths_url)
    data_icu = get_region_dict(icu_url)
    data_recovered = get_region_dict(recovered_url)

    regions = list(data_cases.keys())

    initial_date = datetime.datetime(2020, 1, 25)
    last_date = datetime.datetime.now() + datetime.timedelta(days=2)

    for region in regions:
        region_data = []
        current_date = initial_date;
        while current_date < last_date:
            date = current_date.strftime('%d/%m/%Y')
            get_value = lambda data: data[region][date] if date in data[region] else 0
            entry = [
                current_date.strftime('%Y-%m-%d'),
                get_value(data_cases),
                get_value(data_deaths),
                0,  # no data for hospitalisation
                get_value(data_icu),
                get_value(data_recovered)]
            if entry[1] or entry[2] or entry[3] or entry[4]:
                # prevent days with no data from being added
                region_data.append(entry)
            current_date = current_date + datetime.timedelta(days=1)
        if region == 'Total':
            write_tsv(f"{LOC}/Spain.tsv", cols, region_data, "spain")
        else:
            write_tsv(f"{LOC}/{region}.tsv", cols, region_data, "spain")
