import csv
import itertools
import re

import numpy
import pandas as pd
import requests

import lxml.html


class DrugInteraction:

    def __init__(self, drug1: str, drug2: str):
        self.drug1 = drug1
        self.drug2 = drug2
        self.severity
        self.interaction
        self.references = []

    def addSeverity(self, severity: str):
        self.severity = severity

    def addInteraction(self, interaction: str):
        self.interaction = interaction

    def addReference(self, reference: str):
        self.references.apppend(reference)


class FoodInteraction:

    def __init__(self, drug: str):
        self.drug = drug
        self.severity
        self.interaction
        self.references = []

    def addSeverity(self, severity: str):
        self.severity = severity

    def addInteraction(self, interaction: str):
        self.interaction = interaction

    def addReference(self, reference: str):
        self.references.apppend(reference)


class TherapeuticDuplication:

    def __init__(self, drug1: str, drug2: str):
        self.drug1 = drug1
        self.drug2 = drug2
        self.category = []
        self.text = []

    def addCategory(self, category: str):
        self.category.append(category)

    def addReference(self, tex: str):
        self.text.apppend(text)


# files:
# generic_names.xlsx : Multum classification codes Ex: d00001 ACYCLOVIR
# drug_details.csv : Contains the list of drug ids and nanmes extracted fromn drugs.com interaction api
# live_search_url: https://www.drugs.com/js/search/?id=livesearch-interaction&s=a : Gives all the drugs starting with a when enetering a in the drop down at https://www.drugs.com/drug_interactions.html

generic_names_xlsx = 'generic_names.xlsx'
drug_details_csv = 'drug_details.csv'
drug_pairs_csv = 'drug_pairs.csv'
live_search_url = 'https://www.drugs.com/js/search/?id=livesearch-interaction'
interaction_url = 'https://www.drugs.com/interactions-check.php'

drug_interaction_severity_xpath = '(//div[contains(@class,"interactions-reference")])[1]//span[contains(@class,"status")]'
drug_interaction_interaction_xpath = '((//div[contains(@class,"interactions-reference")])[1]//p)[2]'
drug_interaction_references_xpath = '(//div[contains(@class,"interactions-reference")])[1]//div[contains(@class,"reference-list")]//li'

food_interaction_drug_xpath = '//h2[text()="Drug and food interactions"]//following::div[1]//h3'
food_interaction_severity_xpath = '//h2[text()="Drug and food interactions"]//following::div[1]//span'
food_interacion_inteteracion_xpath = '//h2[text()="Drug and food interactions"]//following::div[@class="interactions-reference"]/p[1]'
food_interaction_references_xpath = '//h2[text()="Drug and food interactions"]//following::div[@class="interactions-reference"]/div[contains(@class,"reference-list")]'

therapeutic_duplication_category_xpath = '(//div[@class="interactions-reference-wrapper"])[3]//h3'
therapeutic_duplication_text_xpath = '(//div[@class="interactions-reference-wrapper"])[3]//div[@class="interactions-reference"]//descendant::p[2]'


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

    interactionDetails = []

    for index, row in df.iterrows():

        drug_1 = getDrugIdentifier(row['drug_id_1'])
        drug_2 = getDrugIdentifier(row['drug_id_2'])
        html_data = requests.get(url=interaction_url, params={
            'drug_list': drug_1 + ',' + drug_2, 'professional': '1'}).text

        doc = lxml.html.fromstring(html_data)

        ##########################
        # Drug interaction
        ##########################

        severities = getTextFromXpath(
            doc, drug_interaction_severity_xpath)
        interactions = getTextFromXpath(
            doc, drug_interaction_interaction_xpath)
        referencesList = getTextFromXpath(
            doc, drug_interaction_references_xpath)

        if len(severities) > 1:
            print("Multiple severities found for drug interaction : (",
                  drug_1, " : ", drug_2)

        if len(interactions) > 1:
            print("Multiple interactions found for drug interaction : (",
                  drug_1, " : ", drug_2)

        # Note: To add drug Ids

        drugInteraction = DrugInteraction(drug_1, drug_2)

        for severity, interaction, references in zip(severities, interaction, referencesList):
            drugInteraction.addSeverity(severity)
            drugInteraction.addInteraction(interaction)
            for reference in references:
                drugInteraction.addReference(reference)

        ##########################
        # Food interaction
        ##########################

        drugs = getTextFromXpath(doc, food_interaction_drug_xpath)
        severities = getTextFromXpath(doc, food_interaction_severity_xpath)
        interactions = getTextFromXpath(
            doc, food_interacion_inteteracion_xpath)
        referenceList = getTextFromXpath(
            doc, food_interaction_references_xpath)

        for drug, severity, interaction, references in zip(drugs, severities, referenceList):
            foodInteraction = DrugInteraction(drugs.split()[0])
            foodInteraction.addSeverity(severity)
            foodInteraction.addInteraction(interaction)
            for interaction in interactions:
                foodInteraction.add(interaction)

        ##########################
        # Therapeutic duplication
        ##########################

        categories = getTextFromXpath(
            doc, therapeutic_duplication_category_xpath)
        texts = getTextFromXpath(
            doc, therapeutic_duplication_text_xpath)

        therapeuticDuplicaiton = TherapeuticDuplication(drug_1, drug_2)

        for category, text in zip(categories, texts):
            therapeuticDuplicaiton.category(category)
            therapeuticDuplicaiton.text(text)


if __name__ == "__main__":
    getInteraction()
