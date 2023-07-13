from sklearn.neighbors import NearestNeighbors
import pandas as pd
from transliterate import translit
import numpy as np
import random
import tkinter
from tkinter import messagebox


class fix_mistake:
    def __init__(self, path_example_file: str):
        self.table = pd.read_excel(path_example_file)
        self.letter = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л','м', 'н', 'о', 'п', 'р', 'с',
                       'т', 'у', 'ф', 'х', 'ц', 'ч','ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я', '-']

        self.dict_letter = dict()

        for key in self.letter:
            self.dict_letter[key] = random.randint(0, 1000)

        example_author_lastname = self.table['Фамилия'].apply(lambda x: x.lower())
        example_author_lastname.apply(lambda x: translit(x, 'ru'))

        self.list_lastname = np.array(example_author_lastname)

    def contains_in_example(self, word):
        return None

    def create_word_vector(self, word: str):
        new_word = translit(word, 'ru').lower()
        vector = np.zeros(16)

        for i in range(len(new_word)):
            vector[i] = self.dict_letter[new_word[i]]

        return np.array(vector)

    def create_vectors_example(self):
        list_vectors = []

        for lastname in self.list_lastname:
            list_zero = np.zeros(16)
            for i in range(len(lastname)):
                list_zero[i] = self.dict_letter[lastname[i]]
            list_vectors.append(list_zero)

        return np.array(list_vectors)

    def find_same_vector(self, example_vectors, word_vector):
        neighbor = NearestNeighbors(n_neighbors=4, radius=0.3).fit(example_vectors)
        distances, indices = neighbor.kneighbors(word_vector.reshape(1, -1), n_neighbors=8)

        return distances, indices

    def find_neighbour(self, indices):
        samples = []
        for i in range(len(indices)):
            samples.append(self.table['Фамилия'].iloc[indices[i]])
        return samples


def main_fix(word: str):
    fixer = fix_mistake('authors_example.xlsx')
    example_vectors = fixer.create_vectors_example()
    vector = fixer.create_word_vector(word)

    distance, index = fixer.find_same_vector(example_vectors, vector)

    return fixer.find_neighbour(index[0])


if __name__ == '__main__':
    word = 'Еримин'
    if main_fix(word)[0] != word:
        root = tkinter.Tk()
        root.withdraw()
        variant_list = np.unique([f"{main_fix(word)[i]}" for i in range(len(main_fix(word)))])
        messagebox.showerror('Ошибка', f'Возможно неправильное написание слова: {word} \n'
                                       f'Варианты написания: \n {variant_list}')
