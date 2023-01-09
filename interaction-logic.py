import csv
import itertools
import re

import numpy
import pandas as pd
import requests

# files:
# generic_names.xlsx : Multum classification codes Ex: d00001 ACYCLOVIR
# drug_details.csv : Contains the list of drug ids and nanmes extracted fromn drugs.com interaction api
# live_search_url: https://www.drugs.com/js/search/?id=livesearch-interaction&s=a : Gives all the drugs starting with a when enetering a in the drop down at https://www.drugs.com/drug_interactions.html

generic_names_xlsx = 'generic_names.xls'
drug_details_csv = 'drug_details.csv'
drug_pairs_csv = 'drug_pairs.csv'
live_search_url = 'https://www.drugs.com/js/search/?id=livesearch-interaction'


def saveDrugDetails():
    """
    Reads generic_names_xlsx and searchs live_search_url to get
    the ids and drug names and saves it in drug_details_csv
    """
    df = pd.read_excel(generic_names_xlsx)

    drug_details = []
    for index, row in df.iterrows():
        html_data = requests.get(url=live_search_url, params={
            's': row['generic']}).text
        matches = re.findall(
            r'addDrug\(\'(.*?)\', \'(.*?)\', \'(.*?)\', \'(.*?)\', \'(.*?)\'\)', html_data)
        for match in matches:
            id = '-'.join(match[0:3])
            drug = ''
            if match[3] and match[4]:
                drug = match[3] + ' (' + match[4] + ')'
            elif match[3]:
                drug = match[3]
            elif match[4]:
                drug = match[4]
            drug_details.append([id, drug])

    df = pd.DataFrame(drug_details, columns=["drug_id", "drug_name"])
    df.drop_duplicates(inplace=True)
    df.to_csv(drug_details_csv, sep="|", header=True, index=False)


# saveDrugDetails()

def makePairs():

    df = pd.read_csv(drug_details_csv, sep="|")
    drug_ids = df['drug_id'].values
    drug_id_pairs = list(itertools.combinations(drug_ids, 2))

    df = pd.DataFrame(drug_id_pairs, columns=['drug_id_1', 'drug_id_2'])
    df.drop_duplicates(inplace=True)
    df.to_csv(drug_pairs_csv, sep="|", header=True, index=False)


# makePairs()