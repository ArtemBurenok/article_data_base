import pandas as pd
import openpyxl
from random import randint
import random

authors = pd.read_excel('authors.xlsx')


def rando():
    return random.randint(10000000,11000000)


d = dict()
d = {key: rando() for key in range(0, 365)}

authors['index'] = authors['author_id'].map(d)
# authors['author_id'] = authors['author_id'].fillna(authors['index'].map(d))
print(authors)

authors.to_excel('mydata.xlsx', index=False)