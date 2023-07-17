from bs4 import BeautifulSoup
import pandas as pd
from xml_parser.check_errors import main_fix
import tkinter
from tkinter import messagebox
import numpy as np


def extract_authors_info(xml_filename, output_filename='authors.xlsx'):
    author_fields = {'lastname': [], 'name': [], 'authorid': [], 'affiliations_list_orgname': [], 'affiliations_list_orgid': []}
    with open(xml_filename, 'r', encoding='utf-8') as fd:
        xml_file = fd.read()

    soup = BeautifulSoup(xml_file, 'lxml')

    entire_info = set()

    for tag in soup.findAll("item"):
        list_num = []
        for author in tag.find('authors').findAll("author"):
            num = author['num']
            if num not in list_num:
                list_num.append(author['num'])
                entire_info.add(tuple([author.find('authorid').text if author.find('authorid') is not None else "", "", ""]))

    new_entire_info = set()

    for tag in soup.findAll('item'):
        list_num = []
        for author in tag.find('authors').findAll("author"):
            num = author['num']
            if num not in list_num:
                list_num.append(author['num'])
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
    authors['lastname'] = authors['lastname'].apply(lambda x: x.lower().capitalize())
    authors['initials'] = authors['initials'].apply(lambda x: x if '.' in x else ' '.join([name_part.lower().capitalize() for name_part in x.split()]))

    # unique_authors['lastname'] = unique_authors['lastname'].apply(lambda x: x.replace('ya', 'ja').replace('yu', 'ju'))
    # unique_authors['lastname'] = unique_authors['lastname'].apply(lambda x: translit(x, 'ru'))
    # unique_authors['lastname'] = unique_authors['lastname'].apply(lambda x: x.replace('ü', 'у'))

    example_authors = pd.read_excel('authors_example.xlsx')['Фамилия']
    different_lastname_set = set(authors['lastname']) - set(example_authors)

    for i in range(authors.shape[0]):
        lastname = authors['lastname'].iloc[i]
        if lastname not in different_lastname_set:
            if lastname != main_fix(lastname)[0]:
                root = tkinter.Tk()
                root.withdraw()

                variant_list = np.unique([f"{main_fix(lastname)[i]}" for i in range(len(main_fix(lastname)))])
                messagebox.showerror('Ошибка', f'Возможно неправильное написание слова: {lastname} \n'
                                               f'Варианты написания: \n {variant_list}')
    authors.to_excel(output_filename)


if __name__ == '__main__':
    extract_authors_info('new_article.xml')


