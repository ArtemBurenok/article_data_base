from bs4 import BeautifulSoup
import pandas as pd
from xml_parser.check_errors import main_fix
from transliterate import translit
import tkinter
from tkinter import messagebox
import numpy as np


def extract_authors_info(xml_filename):
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

    example_authors = pd.read_excel('authors_example.xlsx')['Фамилия']
    different_lastname_set = set(unique_authors['lastname']) - set(example_authors)

    for i in range(unique_authors.shape[0]):
        lastname = unique_authors['lastname'].iloc[i]
        if lastname not in different_lastname_set:
            if lastname != main_fix(lastname)[0]:
                root = tkinter.Tk()
                root.withdraw()

                variant_list = np.unique([f"{main_fix(lastname)[i]}" for i in range(len(main_fix(lastname)))])
                messagebox.showerror('Ошибка', f'Возможно неправильное написание слова: {lastname} \n'
                                               f'Варианты написания: \n {variant_list}')


    unique_authors.to_excel('authors.xlsx')


if __name__ == '__main__':
    extract_authors_info('article.xml')


