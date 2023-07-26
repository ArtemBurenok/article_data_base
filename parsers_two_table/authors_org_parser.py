import pandas as pd
from bs4 import BeautifulSoup
from check_errors import main_fix
import tkinter
from tkinter import messagebox
import numpy as np


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

            try:
                for aff in author.find('affiliations'):
                    aff_id = aff.find('orgid').text if aff.find('orgid') is not None else " "
                    aff_name = aff.find('orgname').text if aff.find('orgname') is not None else " "

                    counter += 1
                    author_organisation.append([counter, author_id, author_name, author_initials, aff_id, aff_name])
            except TypeError:
                continue

    fd.close()

    authors_organisations = pd.DataFrame(author_organisation, columns=['counter', 'author_id', 'author_name', 'author_initials', 'org_id', 'org_name'])

    # example_authors = pd.read_excel('authors_example.xlsx')['Фамилия']
    # different_lastname_set = set(authors_organisations['author_name']) - set(example_authors)
    #
    # for i in range(authors_organisations.shape[0]):
    #     lastname = authors_organisations['author_name'].iloc[i]
    #     if lastname not in different_lastname_set:
    #         if lastname != main_fix(lastname)[0]:
    #             root = tkinter.Tk()
    #             root.withdraw()
    #
    #             variant_list = np.unique([f"{main_fix(lastname)[i]}" for i in range(len(main_fix(lastname)))])
    #             messagebox.showerror('Ошибка', f'Возможно неправильное написание слова: {lastname} \n'
    #                                            f'Варианты написания: \n {variant_list}')

    authors_organisations.to_excel('authors_organisations.xlsx')


if __name__ == '__main__':
    parse_affilations_to_excel('../xml_parser/article.xml')