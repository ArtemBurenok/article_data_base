from bs4 import BeautifulSoup
import pandas as pd

fields = {"id":[], "item_id": [], 'linkurl': [], 'genre': [], 'type': [], "journal_title": [], "issn": [], "eissn": [],
          "publisher": [], "vak": [], "rcsi": [], "wos": [], "scopus": [], "quartile": [], "year": [], "number": [],
          'contnumber': [], "volume": [], "page_begin": [], "page_end": [], "language": [], "title_article": [],
          "doi": [], "edn": [], 'grnti': [], 'risc': [], 'corerisc': [], 'lastname': [], 'name': [], 'authorid': [],
          'affiliations_list_orgname': [], 'affiliations_list_orgid': []}

fd = open('../xml_parser/article.xml', 'r', encoding='utf-8')
xml_file = fd.read()
soup = BeautifulSoup(xml_file, 'lxml')

counter = 0
for tag in soup.findAll("item"):
    counter += 1
    fields['id'].append(counter)
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

    # authors
    lastname_list, initials_list, author_id_list = [], [], []

    for author in tag.find('authors').findAll("author"):
        lastname_list.append(author.find('lastname').text if author.find('lastname') is not None else "")
        initials_list.append(author.find('initials').text if author.find('initials') is not None else "")
        author_id_list.append(author.find('authorid').text if author.find('authorid') is not None else "")

    fields['lastname'].append(lastname_list)
    fields['name'].append(initials_list)
    fields['authorid'].append(author_id_list)

    affilation_orgname_list = []
    affilation_orgid_list = []

    for affilation in tag.find('affiliations').findAll("affiliation"):
        affilation_orgname_list.append(affilation.find('orgname').text if affilation.find('orgname') is not None else "")
        affilation_orgid_list.append(affilation.find('orgid').text if affilation.find('orgid') is not None else "")

    fields['affiliations_list_orgname'].append(affilation_orgname_list)
    fields['affiliations_list_orgid'].append(affilation_orgid_list)

fd.close()

data = pd.DataFrame(data=fields)

data = data.explode(['lastname', 'name', 'authorid'])
data = data.explode(['affiliations_list_orgname', 'affiliations_list_orgid'])

data.to_excel("article_data.xlsx")