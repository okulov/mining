import os
from pathlib import Path
import json
import time

import requests


class Parse5ka:
    _headers = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:82.0) Gecko/20100101 Firefox/82.0",
    }
    _params = {
        'records_per_page': 50,
    }

    def __init__(self, start_url, cat):
        self.start_url = start_url
        self.cat_url = cat  # добавили собственную переменную класса со списком категорий

    @staticmethod
    def _get(*args, **kwargs) -> requests.Response:
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code != 200:
                    # todo Создать класс исключение
                    raise Exception
                return response
            except Exception:
                time.sleep(0.25)

    def parse(self, url, cat_number):  # добавляем как аргумент номер категории, который далее используем в параметрах
        params = self._params
        params['categories'] = cat_number  # добавляем категорию в параметры
        while url:
            response: requests.Response = self._get(url, params=params, headers=self._headers)
            if params:
                params = {}
            data: dict = response.json()
            url = data.get('next')
            yield data.get('results')

    # урезанная функция парсинга для категории - только взять номера и имена категорий
    def parse_category(self, url):
        while url:
            response: requests.Response = self._get(url, headers=self._headers)
            data: dict = response.json()
            return data  # возвращаем как словарь состоящий из названия и номера категории. Просто весь файл в виде json

    # старый run - для сравнения
    def run_old(self):
        for products in self.parse(self.start_url):
            for product in products:
                self._save_to_file(product)
            time.sleep(0.1)

    def run(self):
        # так как у нас теперь не просто 1 список с товарами а у каждой категории такой, сначала идем по категориям
        for cat in self.parse_category(self.cat_url):  # по возвращенному функцией parse_category списку категорий
            # cat = {'parent_group_code': '443', 'parent_group_name': 'Алкоголь'}
            cat['products'] = []  # добавляем элемент с ключем products и значением - пустым списком
            # cat = {'parent_group_code': '443', 'parent_group_name': 'Алкоголь', 'products': []}

            # идем по списку продуктов с этой категории (как и раньше) только как аргумент добавляем еще номер категории
            for products in self.parse(self.start_url, cat_number=cat['parent_group_code']):
                for product in products:
                    cat['products'].append(product)  # тут не сразу пишем в файл, а добавляем в массив products
                self._save_to_file(cat, cat_name=cat['parent_group_name'])  # и записываем весь словарь в файл
                time.sleep(0.1)

    @staticmethod
    def _save_to_file(product, cat_name):  # добавился cat_name для использования в качестве имени файла
        path = Path(os.path.dirname(__file__)).joinpath('products').joinpath(
            f'{cat_name}.json')  # заменили имя файла на имя категории, которую передаем как аргумент
        with open(path, 'w', encoding='UTF-8') as file:
            json.dump(product, file, ensure_ascii=False)


if __name__ == '__main__':
    # добавили url со списком категорий в конструктор класса
    parser = Parse5ka('https://5ka.ru/api/v2/special_offers/', cat='https://5ka.ru/api/v2/categories/')
    parser.run()
