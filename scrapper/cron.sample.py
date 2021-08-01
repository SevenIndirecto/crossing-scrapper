#!/usr/bin/env /home/seven/.cache/pypoetry/virtualenvs/scrapper-kV-O4N2m-py3.8/bin/python3.8
import os

from hrk_promet import Scrapper

def main():
    scrapper = Scrapper(history_file='test.history.json')
    data = scrapper.scrap(url='https://www.hak.hr/info/stanje-na-cestama-novo/events')
    scrapper.store_event(data)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
