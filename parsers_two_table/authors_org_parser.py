import pandas as pd
from bs4 import BeautifulSoup


def parse_affilations_to_excel(xml_filename):
    fd = open(xml_filename, 'r', encoding='utf-8')
    xml_file = fd.read()
    soup = BeautifulSoup(xml_file, 'lxml')

    author_organisation = []
    counter = 0

    for tag in soup.findAll("item"):
        for author in tag.find('authors').findAll('author'):
            author_id = author.find('authorid').text if author.find('authorid') is not None else " "
            author_name = author.find('lastname').text if author.find('lastname') is not None else ""
            author_initials = author.find('initials').text if author.find('initials') is not None else ""

            for affilation in tag.find('affiliations').findAll("affiliation"):
                counter += 1
                aff_id = affilation.find('orgid').text if affilation.find('orgid') is not None else " "
                aff_name = affilation.find('orgname').text if affilation.find('orgname') is not None else " "
                author_organisation.append([counter, author_id, author_name, author_initials, aff_id, aff_name])

    fd.close()

    authors_organisations = pd.DataFrame(author_organisation, columns=['counter', 'author_id', 'author_name', 'author_initials', 'org_id', 'org_name'])

    authors_organisations.to_excel('authors_organisations.xlsx')


if __name__ == '__main__':
    parse_affilations_to_excel('../xml_parser/article.xml')