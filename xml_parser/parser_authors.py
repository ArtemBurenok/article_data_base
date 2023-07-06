from bs4 import BeautifulSoup
import pandas as pd

def extract_authors_info(xml_filename, output_filename='authors.xlsx'):
    author_fields = {'lastname': [], 'name': [], 'authorid': [], 'affiliations_list_orgname': [], 'affiliations_list_orgid': []}
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
            name = author.find('initials').text if author.find('initials') is not None else ""

            for element in entire_info:
                if local_id == element[0]:
                    new_list = list(element)
                    new_list[1] = lastname
                    new_list[2] = name
                    new_entire_info.add(tuple(new_list))


authors = pd.DataFrame(new_entire_info, columns=['author_id', 'lastname', 'initials'])
unique_lastname = authors[['author_id', 'lastname']].value_counts().index
unique = []

for element in unique_lastname:
    id_lastname = list(element)
    for info in new_entire_info:
        if info[1] == id_lastname[1]:
            id_lastname.append(info[2])
            break
    unique.append(id_lastname)

unique_authors = pd.DataFrame(unique, columns=['author_id', 'lastname', 'initials'])

unique_authors.to_excel('authors.xlsx')

authors = pd.DataFrame(new_entire_info, columns=['author_id', 'lastname', 'initials'])
authors.to_excel(output_filename)
