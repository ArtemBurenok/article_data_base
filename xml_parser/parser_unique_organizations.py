import pandas as pd
from bs4 import BeautifulSoup


def parse_affilations_to_excel(xml_filename):
    fd = open(xml_filename, 'r', encoding='utf-8')
    xml_file = fd.read()
    soup = BeautifulSoup(xml_file, 'lxml')

    author_organisation = []
    organisation = []

    for tag in soup.findAll("item"):
        for author in tag.find('authors').findAll('author'):
            author_id = author.find('authorid').text if author.find('authorid') is not None else " "
            author_name = author.find('lastname').text if author.find('lastname') is not None else ""

            for affilation in tag.find('affiliations').findAll("affiliation"):
                aff_id = affilation.find('orgid').text if affilation.find('orgid') is not None else " "
                aff_name = affilation.find('orgname').text if affilation.find('orgname') is not None else " "

                author_organisation.append([author_id, author_name, aff_id, aff_name])
                organisation.append(([aff_id, aff_name]))

    fd.close()

    authors_organisations = pd.DataFrame(author_organisation, columns=['author_id', 'author_name', 'org_id', 'org_name'])

    organisations = pd.DataFrame(organisation, columns=['org_id', 'org_name'])
    unique_org = organisations.drop_duplicates().reset_index(drop=True)

    res = (unique_org.groupby('org_id')[['org_id', 'org_name']].apply(lambda x: tuple(x.values)).reset_index(name='info'))

    one_org_index = []
    index_unique_list = list(res['org_id'].value_counts().index)

    for i in range(len(index_unique_list)):
        if index_unique_list[i] != " " and index_unique_list[i] != "570":
            one_org_index.append([index_unique_list[i], res['info'][i][0][1]])
        elif index_unique_list[i] == "570":
            one_org_index.append([index_unique_list[i], 'ИПНГ РАН'])

    for i in range(len(res['info'][0])):
        if res['info'][0][i][1] != 'Tyumen Scientifi c Centre, Siberian Branch, Russian Academy of Sciences' and \
            res['info'][0][i][1] != 'George Washington University':
            one_org_index.append([" ", res['info'][0][i][1]])

    data = pd.DataFrame(one_org_index, columns=['org_id', 'org_name'])

    for pairs in range(authors_organisations.shape[0]):
        for org in range(data.shape[0]):
            if authors_organisations.iloc[pairs]['org_id'] == data.iloc[org]['org_id']:
                authors_organisations.iloc[pairs]['org_name'] = data.iloc[org]['org_name']

    new = authors_organisations.drop_duplicates()
    data.to_excel('../xml_parser/excel_files/one_unique_organisations.xlsx')
    new.to_excel('../xml_parser/excel_files/new_one_authors_organisations.xlsx')


if __name__ == "__main__":
    parse_affilations_to_excel('article.xml')
