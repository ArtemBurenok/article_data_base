from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from transliterate import translit


def extract_authors_info(xml_filename, output_filename='authors.xlsx'):
    author_fields = {'lastname': [], 'name': [], 'surname': [], 'authorid': [], 'affiliations_list_orgname': [], 'affiliations_list_orgid': []}
    print('hello')
    with open(xml_filename, 'r', encoding='utf-8') as fd:
        xml_file = fd.read()

    soup = BeautifulSoup(xml_file, 'lxml')

    entire_info = set()

    for tag in soup.findAll("item"):
        for author in tag.find('authors').findAll("author"):
            entire_info.add(tuple([author.find('authorid').text if author.find('authorid') is not None else "", "", ""]))

    new_entire_info = set()

    for tag in soup.findAll('item'):
        for author in tag.find('authors').findAll("author"):
            local_id = author.find('authorid').text if author.find('authorid') is not None else ""
            lastname = author.find('lastname').text if author.find('lastname') is not None else ""
            initials = author.find('initials').text if author.find('initials') is not None else ""

            for element in entire_info:
                if local_id == element[0]:
                    new_list = list(element)
                    new_list[1] = lastname
                    new_list[2] = initials
                    new_entire_info.add(tuple(new_list))

    authors = pd.DataFrame(new_entire_info, columns=['author_id', 'lastname', 'initials'])
    unique_lastname = authors[['author_id', 'lastname']].value_counts().index
    unique = []

    for element in unique_lastname:
        id_lastname = list(element)
        for info in new_entire_info:
            if (info[1] == id_lastname[1]) and (info[1] == id_lastname[1]) and (len(info[2]) > 4) and (" " in info[2]):
                id_lastname.append(info[2])
                break
        unique.append(id_lastname)

    for element in unique:
        for info in new_entire_info:
            if (len(element) == 2) and (info[1] == element[1]) and (info[0] == element[0]) and ():
                element.append(info[2])

    unique_authors = pd.DataFrame(unique, columns=['author_id', 'lastname', 'initials'])

    unique_authors['lastname'] = unique_authors['lastname'].apply(lambda x: x.lower())

    unique_authors['lastname'] = unique_authors['lastname'].apply(lambda x: x.replace('ya', 'ja').replace('yu', 'ju'))
    unique_authors['lastname'] = unique_authors['lastname'].apply(lambda x: translit(x, 'ru'))
    unique_authors['lastname'] = unique_authors['lastname'].apply(lambda x: x.replace('ü', 'у'))

    unique_authors['lastname'] = unique_authors['lastname'].apply(lambda x: x.capitalize())

    unique_authors.to_excel('../xml_parser/excel_files/authors.xlsx')


if __name__ == '__main__':
    extract_authors_info('article.xml')
