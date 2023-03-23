import csv
import itertools
import re

import numpy
import pandas as pd
import requests

import lxml.html

# files:
# generic_names.xlsx : Multum classification codes Ex: d00001 ACYCLOVIR
# drug_details.csv : Contains the list of drug ids and nanmes extracted fromn drugs.com interaction api
# live_search_url: https://www.drugs.com/js/search/?id=livesearch-interaction&s=a : Gives all the drugs starting with a when enetering a in the drop down at https://www.drugs.com/drug_interactions.html

generic_names_xlsx = 'generic_names.xlsx'
drug_details_csv = 'drug_details.csv'
drug_pairs_csv = 'drug_pairs.csv'
live_search_url = 'https://www.drugs.com/js/search/?id=livesearch-interaction'
interaction_url = 'https://www.drugs.com/interactions-check.php'


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


def getDrugIdentifier(drug_id):
    return drug_id.rsplit('-', 1)[0]


def getTextFromXpath(doc, xpath):
    return [element.text_content().strip() for element in doc.xpath(xpath)]


def getInteraction():

    df = pd.read_csv(drug_pairs_csv, sep="|").head(1)

    for index, row in df.iterrows():

        # drug_1 = getDrugIdentifier(row['drug_id_1'])
        # drug_2 = getDrugIdentifier(row['drug_id_2'])
        drug_1 = "1476-0"
        drug_2 = "2311-0"
        # drug_1 = "11-2689"
        # drug_2 = "11-2744"
        # drug_1 = "2024-0"
        # drug_2 = "2136-0"
        html_data = requests.get(url=interaction_url, params={
            'drug_list': drug_1 + ',' + drug_2, 'professional': '1'}).text

        doc = lxml.html.fromstring(html_data)

        print('*********************************************')


        ### Note to do: Modify references to handle multiple interactions

        severity = getTextFromXpath(
            doc, '(//div[contains(@class,"interactions-reference")])[1]//span[contains(@class,"status")]')
        interaction = getTextFromXpath(
            doc, '((//div[contains(@class,"interactions-reference")])[1]//p)[2]')
        references = getTextFromXpath(
            doc, '(//div[contains(@class,"interactions-reference")])[1]//div[contains(@class,"reference-list")]//li')

        print(severity)
        print(interaction)
        print(references)

        print('*********************************************')

        drug = getTextFromXpath(
            doc, '//h2[text()="Drug and food interactions"]//following::div[1]//h3')

        severity = getTextFromXpath(
            doc, '//h2[text()="Drug and food interactions"]//following::div[1]//span')

        foodInteraction = getTextFromXpath(
            doc, '//h2[text()="Drug and food interactions"]//following::div[@class="interactions-reference"]/p[1]')

        references = getTextFromXpath(
            doc, ' //h2[text()="Drug and food interactions"]//following::div[@class="interactions-reference"]/div[contains(@class,"reference-list")]')

        drug = [x.split()[0] for x in drug]

        print(drug)
        print(severity)
        print(foodInteraction)
        print(references)

        print('*********************************************')

        duplicationCategory = getTextFromXpath(
            doc, '(//div[@class="interactions-reference-wrapper"])[3]//h3')

        duplicaitonText = getTextFromXpath(
            doc, '(//div[@class="interactions-reference-wrapper"])[3]//div[@class="interactions-reference"]//descendant::p[2]')

        # duplicationList = getTextFromXpath(
        #     doc, '(//div[@class="interactions-reference-wrapper"])[3]//div[@class="interactions-reference"]//descendant::ul')

        # duplicationP2 = getTextFromXpath(
        #     doc, '(//div[@class="interactions-reference-wrapper"])[3]//div[@class="interactions-reference"]//descendant::p[3]')

        print(duplicationCategory)
        print(duplicaitonText)
        # print(duplicationList)
        # print(duplicationP2)

        print('*********************************************')


if __name__ == "__main__":
    getInteraction()
