#!/usr/bin/env /home/seven/.cache/pypoetry/virtualenvs/scrapper-kV-O4N2m-py3.8/bin/python3.8

import os
import requests
import json
import time
from lxml import html


class Scrapper(object):
    history_file = 'history.json'

    def __init__(self, history_file=None):
        if history_file:
            self.history_file = history_file

    def _get(self, url: str):
        req_data = {'subCategoryKey': 'border-crossings-status'}
        headers = {
            'Origin': 'https://www.hak.hr',
            'Referer': 'https://www.hak.hr/info/stanje-na-cestama/?lang=en',
            'Accept-Language': 'en-US,en',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }
        resp = requests.post(url, req_data, headers=headers)
        return json.loads(resp.text)

    def scrap(self, url: str):
        data = self._get(url)
        events = data['data']['EventGroups'][0]['Events']

        extracted_data = []

        for event in events:
            info = event['InfoboxContent']
            x = event['CoordinateX']
            y = event['CoordinateY']
            tree = html.fromstring(info)

            crossing = tree.xpath('//tbody/tr/td[1]/strong/text()')
            to_cro = tree.xpath('//tbody/tr/td[2]/text()')
            from_cro = tree.xpath('//tbody/tr/td[4]/text()')

            extracted_data.append({
                'crossing': crossing[0] if crossing else '',
                'to_cro': to_cro[0] if to_cro else '',
                'from_cro': from_cro[0] if from_cro else '',
                'coordinate_x': x,
                'coordinate_y': y,
            })

        return extracted_data

    def store_event(self, event_data):
        filename = self.history_file
        history = {}
        try:
            with open(filename, 'r') as reader:
                history = json.loads(reader.read())
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            pass

        with open(filename, 'w') as writer:
            timestamp = int(time.time())
            history[timestamp] = event_data
            writer.write(json.dumps(history))

