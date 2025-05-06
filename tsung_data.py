"""
Read TSUNG tsung.log file, convert to dict with data.
[
  {
    'timestamp': 1746469501,
    "tr_registration": Data("tr_registration", "1", "853.515", "0", "853.515", "853.515", "0", "0"),
    "match": CountData("match", "3", "15"),
  }
]
"""
from collections import namedtuple
import json
from enum import Enum
from pathlib import Path

class Tsung:
    DATA_FILE_NAME = 'tsung.log'
    PREFIX_HEADER = '# stats: dump at'
    PREFIX_HEADER_LENGTH = len(PREFIX_HEADER)
    PREFIX_DATA_SKIP = len('stats: ')
    PREFIX_ERROR = 'error_'
    PREFIX_TRANSACTION = 'tr_'
    Data = namedtuple('Data', 'name cout_10sec mean_10sec stddev_10sec max min mean count')

    def __init__(self):
        self.data = []
        self.transactions = set()
        self.http_codes = set()
        self.errors = set()

    def __str__(self):
        return json.dumps(self.data)

    def parse(self, dirpath: str | Path):
        """Parse tsung.log from dirpath."""
        filename = Path(dirpath).resolve() / self.DATA_FILE_NAME
        data = {}
        with open(filename, 'r') as fin:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                print(line)
                if line.startswith(self.PREFIX_HEADER):
                    # '# stats: dump at 1746469501' - get timestamp
                    if data:
                        self.data.append(data)
                        print('-------')
                        print(self.data)
                    data = {'timestamp': int(line[self.PREFIX_HEADER_LENGTH:])}

                # skip line up to name
                line = line[self.PREFIX_DATA_SKIP:]
                if line.startswith(self.PREFIX_TRANSACTION):
                    # 'stats: tr_cb_login 149 106.13193288590601 9.39066762617517 235.81 93.45 107.17295945945946 74'
                    d = self.Data(*line.split())
                    data[d.name] = d
                    print(d)

        print(json.dumps(self.data, indent=4))
