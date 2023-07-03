import pandas as pd
from bs4 import BeautifulSoup

fd = open('article.xml', 'r', encoding='utf-8')
xml_file = fd.read()
soup = BeautifulSoup(xml_file, 'lxml')

author_organisation = []
organisation = []

for tag in soup.findAll("item"):
    for author in tag.find('authors').findAll('author'):
        author_id = author.find('authorid').text if author.find('authorid') is not None else " "
        for affilation in tag.find('affiliations').findAll("affiliation"):
            aff_id = affilation.find('orgid').text if affilation.find('orgid') is not None else " "
            aff_name = affilation.find('orgname').text if affilation.find('orgname') is not None else " "
            author_organisation.append([author_id, aff_id])
            organisation.append(([aff_id, aff_name]))

authors_organisations = pd.DataFrame(author_organisation, columns=['author_id', 'org_id'])
organisations = pd.DataFrame(organisation, columns=['org_id', 'org_name'])

authors_organisations.to_excel('authors_organisations.xlsx')
organisations.to_excel('organisations.xlsx')
