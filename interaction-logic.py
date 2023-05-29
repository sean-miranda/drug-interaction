# files:
# generic_names.xlsx : Multum classification codes Ex: d00001 ACYCLOVIR
# drug_details.csv : Contains the list of drug ids and nanmes extracted fromn drugs.com interaction api
# live_search_url: https://www.drugs.com/js/search/?id=livesearch-interaction&s=a : Gives all the drugs starting with a when enetering a in the drop down at https://www.drugs.com/drug_interactions.html

import lxml.html
import requests
import pandas as pd
import re
import itertools
import re

generic_names_xlsx = 'generic_names.xlsx'
drug_details_csv = 'drug_details.csv'
drug_pairs_csv = 'drug_pairs.csv'
live_search_url = 'https://www.drugs.com/js/search/?id=livesearch-interaction'
interaction_url = 'https://www.drugs.com/interactions-check.php'
drug_1_name = '//h1[text()="Drug Interaction Report"]//following::ul[1]/li[1]'
drug_2_name = '//h1[text()="Drug Interaction Report"]//following::ul[1]/li[2]'

drug_interaction_severity_xpath = '(//div[contains(@class,"interactions-reference")])[1]//span[contains(@class,"status")]'
drug_interaction_interaction_xpath = '((//div[contains(@class,"interactions-reference")])[1]//p)[2]'
drug_interaction_references_xpath = '(//div[contains(@class,"interactions-reference")])[1]//div[contains(@class,"reference-list")]'

food_interaction_drug_xpath = '//h2[text()="Drug and food interactions"]//following::div[1]//h3//following::p[1]'
food_interaction_severity_xpath = '//h2[text()="Drug and food interactions"]//following::div[1]//span'
food_interacion_inteteracion_xpath = '//h2[text()="Drug and food interactions"]//following::div[@class="interactions-reference"]/p[1]'
food_interaction_references_xpath = '//h2[text()="Drug and food interactions"]//following::div[@class="interactions-reference"]/div[contains(@class,"reference-list")]'

therapeutic_duplication_category_xpath = '(//div[@class="interactions-reference-wrapper"])[3]//h3'
therapeutic_duplication_text_xpath = '(//div[@class="interactions-reference-wrapper"])[3]//div[@class="interactions-reference"]//descendant::p[2]'

drug_interaction_csv = 'drug_interaction.csv'
food_interaction_csv = 'food_interaction.csv'
therapeutic_duplication_csv = 'therapeutic_duplication.csv'


class DrugInteraction:

    def __init__(self, drug_id_1: str, drug_id_2: str, drug_1_name: str, drug_2_name):
        print("Drug interaction")
        self.drug_id_1 = drug_id_1
        self.drug_id_2 = drug_id_2
        self.drug_1_name = drug_1_name
        self.drug_2_name = drug_2_name
        self.severity = ""
        self.interaction = ""
        self.references = []

    def addSeverity(self, severity: str):
        self.severity = severity

    def addInteraction(self, interaction: str):
        self.interaction = interaction

    def addReference(self, reference: str):
        if not re.search("View all \d+ references", reference):
            self.references.append(reference.replace("\t", "").strip())

    def getContents(self):

        output = {'drug_id_1': self.drug_id_1,
                  'drug_id_2': self.drug_id_2,
                  'drug_1_name': self.drug_1_name,
                  'drug_2_name': self.drug_2_name,
                  'severity': self.severity,
                  'interaction': self.interaction,
                  'references': self.references}

        return output


class FoodInteraction:

    def __init__(self, drug_id: str):
        print("Food Interaction")
        self.drug_id = drug_id
        self.severity = ""
        self.interaction = ""
        self.references = []

    def addSeverity(self, severity: str):
        self.severity = severity

    def addInteraction(self, interaction: str):
        self.interaction = interaction

    def addReference(self, reference: str):
        if not re.search("View all \d+ references", reference):
            self.references.append(reference.replace("\t", "").strip())

    def getContents(self):

        output = {'drug_id': self.drug_id,
                  'severity': self.severity,
                  'interaction': self.interaction,
                  'references': self.references}

        return output


class TherapeuticDuplication:

    def __init__(self, drug_id_1: str, drug_id_2: str, drug_1_name: str, drug_2_name):
        print("Therapeutic Duplicaiton")
        self.drug_id_1 = drug_id_1
        self.drug_id_2 = drug_id_2
        self.drug_1_name = drug_1_name
        self.drug_2_name = drug_2_name
        self.category = ""
        self.text = ""

    def addCategory(self, category: str):
        self.category = category

    def addText(self, text: str):
        self.text = text

    def getContents(self):

        output = {'drug_id_1': self.drug_id_1,
                  'drug_id_2': self.drug_id_2,
                  'drug_1_name': self.drug_1_name,
                  'drug_2_name': self.drug_2_name,
                  'category': self.category,
                  'text': self.text}

        return output


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


def getDrugName(drug_id):
    df_drug_details = pd.read_csv(drug_details_csv, sep="|")
    return df_drug_details.at[drug_id, 'drug_id']


def getInteraction():

    drug_pairs_df = pd.read_csv(drug_pairs_csv, sep="|")
    drug_details_df = pd.read_csv(drug_details_csv, sep="|")
    print()

    drugInteractions = []
    foodInteractions = []
    therapeuticDuplicaitons = []

    for index, row in drug_pairs_df.iterrows():

        drug_id_1 = row['drug_id_1']
        drug_id_2 = row['drug_id_2']

        drug_1_name = drug_details_df.loc[drug_details_df['drug_id']
                                          == drug_id_1, 'drug_name,,,'].values[0].replace(",,,", "")
        drug_2_name = drug_details_df.loc[drug_details_df['drug_id']
                                          == drug_id_2, 'drug_name,,,'].values[0].replace(",,,", "")

        print("*** " + drug_1_name)
        print("*** " + drug_2_name)

        # drug_id_1 = "1115-0"
        # drug_id_2 = "1839-0"

        html_data = requests.get(url=interaction_url, params={
            'drug_list': getDrugIdentifier(drug_id_1) + ',' + getDrugIdentifier(drug_id_2), 'professional': '1'}).text

        # html_data = requests.get(url=interaction_url, params={
        #     'drug_list': '1115-0,1839-0', 'professional': '1'}).text

        doc = lxml.html.fromstring(html_data)

        ##########################
        # Drug interaction
        ##########################

        severities = getTextFromXpath(
            doc, drug_interaction_severity_xpath)
        interactions = getTextFromXpath(
            doc, drug_interaction_interaction_xpath)
        referenceList = getTextFromXpath(
            doc, drug_interaction_references_xpath)

        if severities and interactions and referenceList:
            drugInteraction = DrugInteraction(
                drug_id_1, drug_id_2, drug_1_name, drug_2_name)

        for severity, interaction, references in zip(severities, interactions, referenceList):
            drugInteraction.addSeverity(severity)
            drugInteraction.addInteraction(interaction)
            for reference in references.split("\n")[1:]:
                drugInteraction.addReference(reference)
            drugInteractions.append(drugInteraction.getContents())

        ##########################
        # Food interaction
        ##########################

        drugs = getTextFromXpath(doc, food_interaction_drug_xpath)
        severities = getTextFromXpath(doc, food_interaction_severity_xpath)
        interactions = getTextFromXpath(
            doc, food_interacion_inteteracion_xpath)
        referenceList = getTextFromXpath(
            doc, food_interaction_references_xpath)

        for drug, severity, interaction, references in zip(drugs, severities, interactions, referenceList):
            foodInteraction = FoodInteraction(drug.split(":")[1].strip())
            foodInteraction.addSeverity(severity)
            foodInteraction.addInteraction(interaction)
            for reference in references.split("\n")[1:]:
                foodInteraction.addReference(reference)
            foodInteractions.append(foodInteraction.getContents())

        ##########################
        # Therapeutic duplication
        ##########################

        categories = getTextFromXpath(
            doc, therapeutic_duplication_category_xpath)
        texts = getTextFromXpath(
            doc, therapeutic_duplication_text_xpath)

        if categories and texts:
            therapeuticDuplicaiton = TherapeuticDuplication(
                drug_id_1, drug_id_2, drug_1_name, drug_2_name)

        for category, text in zip(categories, texts):
            therapeuticDuplicaiton.addCategory(category)
            therapeuticDuplicaiton.addText(text)
            therapeuticDuplicaitons.append(
                therapeuticDuplicaiton.getContents())

        print()
        print("--------------------------------")

    pd.DataFrame.from_dict(drugInteractions).to_csv(drug_interaction_csv)
    pd.DataFrame.from_dict(foodInteractions).to_csv(food_interaction_csv)
    pd.DataFrame.from_dict(therapeuticDuplicaitons).to_csv(
        therapeutic_duplication_csv)


if __name__ == "__main__":
    getInteraction()
