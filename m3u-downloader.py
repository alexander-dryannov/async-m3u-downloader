import re
import os
import sys
import asyncio
import aiohttp
import requests
from tqdm import tqdm


class DownloaderM3U:
    def __init__(self, path_file, path_file_output):
        self.path_file = path_file
        self.path_file_output = path_file_output
        self._track_name = []
        self._url_track = []

    """Подготовка словаря"""
    @staticmethod
    def dictionary_preparation(track_name, url_track):
        dict_song = dict(zip(track_name, url_track))
        return dict_song

    """Подготовка списков"""
    def preparation_of_lists(self):
        with open(self.path_file, 'r') as f:
            playlist = f.readlines()
        playlist = [a for a in playlist if a != '\n']
        for i in playlist[1:]:
            if re.search('#EX', i):
                self._track_name.append(i.split(',')[-1].split('\n')[0])
            else:
                self._url_track.append(i.split('\n')[0])
        return 0

    """Создание папки для загрузки и смена рабочей директории"""
    @staticmethod
    def create_folder(path_file_output):
        try:
            os.chdir(path_file_output)
        except FileNotFoundError:
            os.mkdir(path_file_output)
            os.chdir(path_file_output)

    """Получение словаря"""
    def getting_dictionary(self):
        self.preparation_of_lists()
        return self.dictionary_preparation(self._track_name, self._url_track)

    """ Синхронный загрузчик файлов """
    def synchronous_file_upload(self):
        files = self.getting_dictionary()
        self.create_folder(self.path_file_output)
        for file in files:
            try:
                r = requests.get(files[file], stream=True)
                total_size = int(r.headers['content-length'])
                with open(f'{file + "." + files[file].split(".")[-1]}', 'wb') as f:
                    for data in tqdm(desc=file, iterable=r.iter_content(1024), total=int(total_size/1024),
                                     unit='KB', unit_scale=True,):
                        f.write(data)
            except OSError:
                print('[-] Нет соединение с сервером')
                break

    """ Асинхронный загрузчик """
    @staticmethod
    async def asynchronous_file_upload(session, url, name_file):
        async with session.get(url) as response:
            if response.status == 200:
                size = int(response.headers.get('content-length', 0)) or None
                progressbar = tqdm(desc=name_file, total=size, leave=False, unit='B', unit_scale=True, )
                with open(name_file, mode='ab') as f, progressbar:
                    async for chunk in response.content.iter_chunked(1024):
                        f.write(chunk)
                        progressbar.update(len(chunk))
            else:
                print(f"""Ошибка получения файла: {name_file} 
Код ошибки: {response.status}""")

    """ Подготовка к асинхронному скачиванию """
    async def preparing_for_asynchronous_download(self):
        files = self.getting_dictionary()
        self.create_folder(self.path_file_output)

        async with aiohttp.ClientSession() as session:
            tasks = [self.asynchronous_file_upload(session, files[file], f'{file + "." + files[file].split(".")[-1]}') for file in files]
            await asyncio.gather(*tasks, return_exceptions=True)

    def main(self):
        asyncio.run(self.preparing_for_asynchronous_download())


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('[ - ] не хватает аргументов')
    else:
        if sys.argv[1] == '-a' and sys.argv[3] == '-o':
            DownloaderM3U(sys.argv[2], sys.argv[4]).main()
        elif sys.argv[1] == '-s' and sys.argv[3] == '-o':
            DownloaderM3U(sys.argv[2], sys.argv[4]).synchronous_file_upload()
