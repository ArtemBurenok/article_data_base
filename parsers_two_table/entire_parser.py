from bs4 import BeautifulSoup
import pandas as pd
from check_errors import main_fix
import tkinter
from tkinter import messagebox
import numpy as np


def parse_articles_to_excel(xml_filename):
    fields = {"item_id": [], 'linkurl': [], 'genre': [], 'type': [], "journal_title": [], "issn": [], "eissn": [],
              "publisher": [], "vak": [], "rcsi": [], "wos": [], "scopus": [], "quartile": [], "year": [], "number": [],
              'contnumber': [], "volume": [], "page_begin": [], "page_end": [], "language": [], "title_article": [],
              "doi": [], "edn": [], 'grnti': [], 'risc': [], 'corerisc': [], 'counter': []}

    fd = open(xml_filename, 'r', encoding='utf-8')
    xml_file = fd.read()
    soup = BeautifulSoup(xml_file, 'lxml')

    author_organisation = []
    counter = 0

    counter_all = 0
    for tag in soup.findAll("item"):
        # item
        fields['item_id'].append(tag['id'])
        fields['linkurl'].append(tag.find('linkurl').text if tag.find('linkurl') is not None else "")
        fields['genre'].append(tag.find('genre').text if tag.find('genre') is not None else "")
        fields['type'].append(tag.find('type').text if tag.find('type') is not None else "")

        # journal
        fields['journal_title'].append(tag.find('journal').find('title').text if tag.find('journal').find('title') is not None else "")
        fields['issn'].append(tag.find('journal').find('issn').text if tag.find('journal').find('issn') is not None else "")
        fields['eissn'].append(tag.find('journal').find('eissn').text if tag.find('journal').find('eissn') is not None else "")
        fields['publisher'].append(tag.find('journal').find('publisher').text if tag.find('journal').find('publisher') is not None else "")
        fields['vak'].append(tag.find('journal').find('vak').text if tag.find('journal').find('vak') is not None else "")
        fields['rcsi'].append(tag.find('journal').find('rcsi').text if tag.find('journal').find('rcsi') is not None else "")
        fields['wos'].append(tag.find('journal').find('wos').text if tag.find('journal').find('wos') is not None else "")
        fields['scopus'].append(tag.find('journal').find('scopus').text if tag.find('journal').find('scopus') is not None else "")
        fields['quartile'].append("")

        # issue
        fields['year'].append(tag.find('issue').find('year').text if tag.find('issue').find('year') is not None else "")
        fields['number'].append(tag.find('issue').find('number').text if tag.find('issue').find('number') is not None else "")
        fields['contnumber'].append(tag.find('issue').find('contnumber').text if tag.find('issue').find('contnumber') is not None else "")
        fields['volume'].append(tag.find('issue').find('volume').text if tag.find('issue').find('volume') is not None else "")

        # item
        list_pages = tag.find('pages').text.split("-") if tag.find('pages') is not None else [" "]
        if len(list_pages) == 2:
            fields["page_begin"].append(list_pages[0])
            fields["page_end"].append(list_pages[1])
        else:
            fields["page_begin"].append(list_pages[0])
            fields["page_end"].append(list_pages[0])
        fields['language'].append(tag.find('language').text if tag.find('language') is not None else "")

        # titles
        fields['title_article'].append(tag.find('titles').find('title').text if tag.find('titles').find('title') is not None else "")

        # item
        fields['doi'].append(tag.find('doi').text if tag.find('doi') is not None else "")
        fields['edn'].append(tag.find('edn').text if tag.find('edn') is not None else "")
        fields['grnti'].append(tag.find('grnti').text if tag.find('grnti') is not None else "")
        fields['risc'].append(tag.find('risc').text if tag.find('risc') is not None else "")
        fields['corerisc'].append(tag.find('corerisc').text if tag.find('corerisc') is not None else "")

        count_author_org = []

        # count of organisations
        for author in tag.find('authors').findAll('author'):
            author_id = author.find('authorid').text if author.find('authorid') is not None else " "
            author_name = author.find('lastname').text if author.find('lastname') is not None else ""
            author_initials = author.find('initials').text if author.find('initials') is not None else ""

            try:
                for aff in author.find('affiliations'):
                    aff_id = aff.find('orgid').text if aff.find('orgid') is not None else " "
                    aff_name = aff.find('orgname').text if aff.find('orgname') is not None else " "

                    counter_all += 1
                    count_author_org.append(counter_all)

                    counter += 1
                    author_organisation.append([counter, author_id, author_name, author_initials, aff_id, aff_name])
            except TypeError:
                continue

        fields['counter'].append(count_author_org)

    article = pd.DataFrame(data=fields)
    article = article.explode('counter')

    authors_organisations = pd.DataFrame(author_organisation, columns=['counter', 'author_id', 'author_name',
                                                                       'author_initials', 'org_id', 'org_name'])

    whole_table = article.merge(authors_organisations, how='inner')
    whole_table.to_excel('whole_table.xlsx')
    fd.close()


if __name__ == "__main__":
    parse_articles_to_excel('../xml_parser/article.xml')


