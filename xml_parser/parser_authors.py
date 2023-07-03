from bs4 import BeautifulSoup
import pandas as pd

author_fields = {'lastname': [], 'name': [], 'authorid': [], 'affiliations_list_orgname': [], 'affiliations_list_orgid': []}

fd = open('article.xml', 'r', encoding='utf-8')
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
authors.to_excel('authors.xlsx')
