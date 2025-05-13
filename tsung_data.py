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
from collections.abc import Sequence
from enum import Enum
from pathlib import Path

from utils import str_number, str_sec, number, str_bytes, str_bits_per_sec

header7 = ['Name', 'Highest 10sec mean', 'Lowest 10sec mean', 'Highest Rate', 'Mean Rate', 'Mean', 'Count']
tables = {
    'transaction': {
        'done': True,
        'title': 'Transactions Statistics',
        'header': header7,
        'data': []
    },
    'http': {
        'done': True,
        'title': 'HTTP return code',
        'header': ['Code', 'Highest Rate', 'Mean Rate', 'Total number'],
        'data': []
    },
    'match': {
        'done': True,
        'title': 'Match Statistics',
        'header': ['Name', 'Highest Rate', 'Mean Rate', 'Total number'],
        'data': []
    },
    'error': {
        'done': True,
        'title': 'Errors',
        'header': ['Name', 'Highest Rate', 'Total number'],
        'data': []
    },
    'users': {
        'done': True,
        'title': 'Counters Statistics',
        'header': ['Name', 'Max'],
        'data': []
    },
    'main': {
        'done': True,
        'title': 'Main Statistics',
        'header': header7,
        'data': []
    },
    'network': {
        'done': True,
        'title': 'Network Throughput',
        'header': ['Name', 'Highest Rate', 'Total'],
        'data': []
    },
    'server': {
        'done': True,
        'title': 'Server monitoring',
        'header': ['Name', 'Highest 10sec mean', 'Lowest 10sec mean'],
        'data': []
    },
}

charts = {
    'transactions_mean': {
        'title': 'Mean transaction duration',
        'xheader': 'time (sec of running test)',
        'yheader': 'transaction duration (msec)',
        'data': []
    },
    'transactions_rate': {
        'title': 'Transactions rate',
        'xheader': 'time (sec of running test)',
        'yheader': 'transactions/sec',
        'data': []
    },
    'http_rate': {
        'title': 'HTTP code response rate',
        'xheader': 'time (sec of running test)',
        'yheader': 'number/sec',
        'data': []
    },
    'match_rate': {
        'title': 'Matching responses',
        'xheader': 'time (sec of running test)',
        'yheader': 'number/sec',
        'data': []
    },
    'error_rate': {
        'title': 'Errors (rate)',
        'xheader': 'time (sec of running test)',
        'yheader': 'errors/sec',
        'data': []
    },
    'users': {
        'title': 'Simultaneous Users and opened TCP/IP connections',
        'xheader': 'time (sec of running test)',
        'yheader': 'value',
        'data': []
    },
    'users_arrival': {
        'title': 'Users arrival/departure rate',
        'xheader': 'time (sec of running test)',
        'yheader': 'number of users/sec',
        'data': []
    },
    'main': {
        'title': 'Mean request and connection duration',
        'xheader': 'time (sec of running test)',
        'yheader': 'Request duration (msec)',
        'data': []
    },
    'main_rate': {
        'title': 'Request and TCP/IP connection rate',
        'xheader': 'time (sec of running test)',
        'yheader': 'Request rate (r/sec)',
        'data': []
    },
    'cpu': {
        'title': 'CPU% (mean)',
        'xheader': 'time (sec of running test)',
        'yheader': 'cpu',
        'data': []
    },
    'load': {
        'title': 'CPU load (mean)',
        'xheader': 'time (sec of running test)',
        'yheader': 'load',
        'data': []
    },
    'freemem': {
        'title': 'Free memory (mean)',
        'xheader': 'time (sec of running test)',
        'yheader': 'freemem',
        'data': []
    },
    'network': {
        'title': 'Network throughput',
        'xheader': 'time (sec of running test)',
        'yheader': 'Kbits/sec',
        'data': []
    },
}

Data = namedtuple('Data', 'name count_10sec mean_10sec stddev_10sec max min mean count')
DataCounter = namedtuple('DataCounter', 'name count_10sec total')

class Tsung:
    DATA_FILE_NAME = 'tsung.log'
    PREFIX_HEADER = '# stats: dump at'
    PREFIX_HEADER_LENGTH = len(PREFIX_HEADER)
    PREFIX_DATA_SKIP = len('stats: ')
    PREFIX_ERROR = 'error_'
    PREFIX_TRANSACTION = 'tr_'
    # no info about these transactions in report, please ignore:

    def __init__(self):
        self.start_timestamp: int = 0    # int(self.data[0]['timestamp']) - начало теста
        # self.data = [
        #   {'timestamp': 1746441567},
        #   {'timestamp': 1746441577, 'tr_rand_name': Data(name='tr_rand_name', count_10sec='3', mean_10sec='0.35333333333333333', stddev_10sec='0.10977654070378101', max='0.481', min='0.213', mean='0', count='0'), 'tr_get_host_name': Data(name='tr_get_host_name', count_10sec='1', mean_10sec='0.211', stddev_10sec='0', max='0.211', min='0.211', mean='0', count='0'), 'tr_profile': Data(name='tr_profile', count_10sec='1', mean_10sec='92.286', stddev_10sec='0', max='92.286', min='92.286', mean='0', count='0'), 'tr_cb_balance': Data(name='tr_cb_balance', count_10sec='2', mean_10sec='78.20349999999999', stddev_10sec='0.6774999999999984', max='78.881', min='77.526', mean='0', count='0'), 'tr_deposit': Data(name='tr_deposit', count_10sec='2', mean_10sec='210.4145', stddev_10sec='94.92249999999999', max='305.337', min='115.492', mean='0', count='0'), 'tr_cb_bet': Data(name='tr_cb_bet', count_10sec='1', mean_10sec='128.603', stddev_10sec='0', max='128.603', min='128.603', mean='0', count='0'), 'tr_cb_liveness': Data(name='tr_cb_liveness', count_10sec='2', mean_10sec='57.5655', stddev_10sec='0.23550000000000182', max='57.801', min='57.33', mean='0', count='0'), 'tr_set_var': Data(name='tr_set_var', count_10sec='1', mean_10sec='1.319', stddev_10sec='0', max='1.319', min='1.319', mean='0', count='0'), 'tr_game_init_by_alias_100hp': Data(name='tr_game_init_by_alias_100hp', count_10sec='1', mean_10sec='516.781', stddev_10sec='0', max='516.781', min='516.781', mean='0', count='0'), 'tr_registration': Data(name='tr_registration', count_10sec='1', mean_10sec='853.515', stddev_10sec='0', max='853.515', min='853.515', mean='0', count='0'), 'tr_cb_win': Data(name='tr_cb_win', count_10sec='1', mean_10sec='120.871', stddev_10sec='0', max='120.871', min='120.871', mean='0', count='0')},
        #   {'timestamp': 1746441587, 'tr_rand_name': Data(name='tr_rand_name', count_10sec='17', mean_10sec='0.2787058823529412', stddev_10sec='0.08338201576858896', max='0.481', min='0.154', mean='0.35333333333333333', count='3'), 'tr_get_host_name': Data(name='tr_get_host_name', count_10sec='5', mean_10sec='0.09519999999999999', stddev_10sec='9.797958971132722e-4', max='0.211', min='0.094', mean='0.211', count='1'), 'tr_profile': Data(name='tr_profile', count_10sec='3', mean_10sec='68.70466666666668', stddev_10sec='1.733355192169859', max='92.286', min='67.252', mean='92.286', count='1'), 'tr_cb_balance': Data(name='tr_cb_balance', count_10sec='10', mean_10sec='219.93030000000005', stddev_10sec='423.06610577427494', max='1488.985', min='70.918', mean='78.20349999999999', count='2'), 'tr_deposit': Data(name='tr_deposit', count_10sec='10', mean_10sec='256.9764', stddev_10sec='177.17312444453867', max='742.261', min='115.492', mean='210.4145', count='2'), 'tr_cb_bet': Data(name='tr_cb_bet', count_10sec='11', mean_10sec='111.66672727272726', stddev_10sec='6.812481180503231', max='128.603', min='99.866', mean='128.603', count='1'), 'tr_cb_liveness': Data(name='tr_cb_liveness', count_10sec='11', mean_10sec='54.796', stddev_10sec='3.7567712442758854', max='60.75', min='50.013', mean='57.5655', count='2'), 'tr_set_var': Data(name='tr_set_var', count_10sec='5', mean_10sec='0.4328', stddev_10sec='0.025063120316512876', max='1.319', min='0.399', mean='1.319', count='1'), 'tr_game_init_by_alias_100hp': Data(name='tr_game_init_by_alias_100hp', count_10sec='2', mean_10sec='381.39', stddev_10sec='13.959999999999994', max='516.781', min='367.43', mean='516.781', count='1'), 'tr_registration': Data(name='tr_registration', count_10sec='5', mean_10sec='573.5674000000001', stddev_10sec='609.6595576200214', max='1792.548', min='253.876', mean='853.515', count='1'), 'tr_cb_win': Data(name='tr_cb_win', count_10sec='11', mean_10sec='117.02181818181818', stddev_10sec='6.741436531808092', max='129.156', min='104.488', mean='120.871', count='1')}
        # ]
        self.data = []
        # all possible names in all records
        self.names = {
            'main': ('connect', 'page', 'request'),
            'transaction': set(),
            'network': ('size_sent', 'size_rcv'),
            'users': ('connected', 'finish_users_count', 'users', 'users_count'),
            'match': set(),
            'http': set(),
            'error': set(),
            # server sets: cpu, load, freemem
            'cpu': set(),
            'load': set(),
            'freemem': set(),
        }
        # { name1: [mean_10sec_vales], name2: [mean_10sec_vales], ... } for each name
        self.mean = {}
        # { name1: [count_10sec_vales], name2: [count_10sec_vales], ... } for each name
        self.count = {}

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

                # block header with timestamp
                if line.startswith(self.PREFIX_HEADER):
                    # '# stats: dump at 1746469501' - get timestamp
                    if data:
                        self.data.append(data)
                    data = {'timestamp': int(line[self.PREFIX_HEADER_LENGTH:])}
                    continue

                # skip line up to name
                line = line[self.PREFIX_DATA_SKIP:]
                if line.startswith(self.PREFIX_TRANSACTION):
                    # 'stats: tr_cb_login 149 106.13193288590601 9.39066762617517 235.81 93.45 107.17295945945946 74'
                    words = line.split()
                    d = Data(words[0], *map(number, words[1:]))
                    data[d.name] = d
                    continue

                words = line.split()
                # print(f'{words=}')
                name = words[0]

                # http return codes
                if name.isdigit():
                    # stats: 200 11 11
                    d = DataCounter(*words)
                    data[name] = d

                # match records
                elif 'match' in name:
                    # stats: nomatch 362 469
                    d = DataCounter(*words)
                    data[name] = d

                # error records
                elif 'error' in name:
                    # stats: error_json_unparsable 0 1
                    d = DataCounter(*words)
                    data[name] = d

                # users record
                elif name in self.names['users']:
                    # stats: users_count 1 1
                    d = DataCounter(*words)
                    data[name] = d

                # network record
                elif name in self.names['network']:
                    # stats: users_count 1 1
                    d = DataCounter(*words)
                    data[name] = d

                # main statistics
                elif name in self.names['main']:
                    d = Data(name, *map(number, words[1:]))
                    data[name] = d

                # server statistics
                elif name.startswith('{'):
                    # stats: {load,"tsung_controller@f6f41ca75a60"} 1 0.26953125 0.0 0.3203125 0.26953125 0.3203125 1
                    name = name[1:-2].replace(',"', '@')
                    d = Data(name, *map(number, words[1:]))
                    data[name] = d

        self.data.append(data)
        # print(json.dumps(self.data, indent=4))

    def process(self, ignore_transactions: list[str] | None = None):
        """Calculate mean and rate lists."""
        ignore_transactions = ignore_transactions or []
        
        # Collect all names by categories
        for block in self.data:
            for name in block:
                self.add_name_by_category(name)
        # some transactions should be ignored
        self.names['transaction'] -= ignore_transactions

        self.start_timestamp = int(self.data[0]['timestamp'])
        all_names = [name for category, names in self.names.items() for name in names]
        print(f'{all_names=}')
        for name in all_names:
            for block in self.data:
                timestamp = int(block['timestamp'])
                d = block.get(name)
                if not d:
                    continue
                # the first value for this name
                if not self.count.get(name):
                    self.count[name]= {'timestamp': timestamp, 'data': []}
                self.count[name]['data'].append(int(d.count_10sec))

                # only Data, not DataCount has mean_10sec value
                if len(d) > 3:
                    if not self.mean.get(name):
                        self.mean[name]= {'timestamp': timestamp, 'data': []}
                    self.mean[name]['data'].append(d.mean_10sec)

        # print(f'mean: {self.mean}')
        print(f'mean keys: {self.mean.keys()}')
        print(f'count keys: {self.count.keys()}')
        # print(f'count: {self.count}')

    def add_name_by_category(self, name: str):
        """Add name to self.names."""
        if name == 'timestamp':
            return
        if name.startswith('tr_'):
            self.names['transaction'].add(name)
        elif name.isdigit():
            self.names['http'].add(name)
        elif name.startswith('error_'):
            self.names['error'].add(name)
        elif 'match' in name:
            self.names['match'].add(name)
        elif name.startswith('cpu') :
            self.names['cpu'].add(name)
        elif name.startswith('load') :
            self.names['load'].add(name)
        elif name.startswith('freemem') :
            self.names['freemem'].add(name)

    def duration(self, timestamp):
        """Duration in sec from timestamp till self.data[-1]['timestamp']"""
        return int(self.data[-1]['timestamp']) - int(timestamp)

    def tables(self, table_list: list[str]):
        """Fill tables dictionary after parsing and return it."""
        table = {key: value for key, value in tables.items() if key in table_list}

        # Total test duration in sec
        total_duration = self.duration(self.start_timestamp)

        for table_name in table_list:
            match table_name:
                case 'transaction':
                    d = []
                    for name in sorted(self.names['transaction']):
                        values_without_zero = [value for value, count in zip(self.mean[name]['data'], self.count[name]['data']) if count > 0]
                        # print(f'{name=} {values_without_zero=}')
                        highest_mean = max(values_without_zero)
                        lowest_mean = min(values_without_zero)
                        mean = sum(values_without_zero) / len(values_without_zero)

                        total = sum(self.count[name]['data'])
                        rates = [count/10 for count in self.count[name]['data']]
                        highest_rate = max(rates)
                        mean_rate = sum(rates) / len(rates)
                        d.append([name,
                                  str_sec(highest_mean), str_sec(lowest_mean),
                                  str_number(highest_rate, 2, '/sec'), str_number(mean_rate, 2, '/sec'),
                                  str_sec(mean), total])
                    table['transaction']['data'] = d

                case 'main':
                    # main statistics (same as transactions)
                    d = []
                    for name in sorted(self.names['main']):
                        values_without_zero = [value for value, count in zip(self.mean[name]['data'], self.count[name]['data']) if count > 0]
                        # print(f'{name=} {values_without_zero=}')
                        highest_mean = max(values_without_zero)
                        lowest_mean = min(values_without_zero)
                        mean = sum(values_without_zero) / len(values_without_zero)

                        total = sum(self.count[name]['data'])
                        rates = [count/10 for count in self.count[name]['data']]
                        highest_rate = max(rates)
                        mean_rate = sum(rates) / len(rates)
                        d.append([name,
                                  str_sec(highest_mean), str_sec(lowest_mean),
                                  str_number(highest_rate, 2, '/sec'), str_number(mean_rate, 2, '/sec'),
                                  str_sec(mean), total])
                    table['main']['data'] = d

                case 'match':
                    # matching report (same as http table, except name)
                    d = []
                    for name in sorted(self.names['match']):
                        total = sum(self.count[name]['data'])
                        rate_without_zero = [count/10 for count in self.count[name]['data'] if count > 0]
                        highest_rate = max(rate_without_zero)
                        mean_rate = total / total_duration
                        d.append([name,
                                  str_number(highest_rate, 2, '/sec'), str_number(mean_rate, 2, '/sec'),
                                  total])
                    table['match']['data'] = d

                case 'http':
                    # HTTP return code
                    d = []
                    for name in sorted(self.names['http']):
                        total = sum(self.count[name]['data'])
                        rate_without_zero = [count/10 for count in self.count[name]['data'] if count > 0]
                        highest_rate = max(rate_without_zero)
                        # _total_duration = len(rate_without_zero) * 10
                        _total_duration = self.duration(self.count[name]['timestamp'])
                        mean_rate = total / _total_duration
                        d.append([name,
                                  str_number(highest_rate, 2, '/sec'), str_number(mean_rate, 2, '/sec'),
                                  total])
                    table['http']['data'] = d

                case 'error':
                    # Errors
                    d = []
                    for name in sorted(self.names['error']):
                        total = sum(self.count[name]['data'])
                        rate_without_zero = [count/10 for count in self.count[name]['data'] if count > 0]
                        highest_rate = max(rate_without_zero)
                        d.append([name,
                                  str_number(highest_rate, 2, '/sec'),
                                  total])
                    table['error']['data'] = d

                case 'network':
                    # Network (same as Errors)
                    d = []
                    for name in sorted(self.names['network']):
                        total = sum(self.count[name]['data'])
                        rate_without_zero = [count/10 for count in self.count[name]['data'] if count > 0]
                        highest_rate = max(rate_without_zero)
                        d.append([name,
                                  str_bits_per_sec(highest_rate),
                                  str_bytes(total)])
                    table['network']['data'] = d

                case 'users':
                    # Users
                    d = []
                    for name in sorted(self.names['users']):
                        max_value = max(self.count[name]['data'])
                        d.append([name,
                                  max_value])
                    table['users']['data'] = d

                case 'server':
                    # Server (aggregate tabel for cpu, load, freemem)
                    d = []
                    for name in sorted(self.names['cpu']):
                        max_value = max(self.mean[name]['data'])
                        min_value = min(self.mean[name]['data'])
                        d.append([name, str_number(max_value, accuracy=2, unit='%'), str_number(min_value, accuracy=2, unit='%')])
                    for name in sorted(self.names['load']):
                        max_value = max(self.mean[name]['data'])
                        min_value = min(self.mean[name]['data'])
                        d.append([name, str_number(max_value, accuracy=2), str_number(min_value, accuracy=2)])
                    for name in sorted(self.names['freemem']):
                        max_value = max(self.mean[name]['data'])
                        min_value = min(self.mean[name]['data'])
                        d.append([name, str_number(max_value, accuracy=0, unit=' MB'), str_number(min_value, accuracy=0, unit=' MB')])
                    table['server']['data'] = d

                case _:
                    raise ValueError(f'Unknown table "{table_name}"')

        return table

    def one_chart_data(self, names: Sequence[str], get_data_by_name) -> list[dict]:
        """Build (x,y) data for all chart series by names and get_data_by_name function."""
        lines_data = []
        for name in sorted(names):
            data = get_data_by_name(name)
            y = data['data']
            ylen = len(y)
            x0 = (data['timestamp'] - self.start_timestamp)
            points = [{'x': x, 'y': y} for x, y in zip(range(x0, x0 + ylen * 10, 10), y)]

            line_data = {
                "label": name,
                "fill": False,
                "tension": 0,
                "data": points
            }
            lines_data.append(line_data)

        return lines_data

    def charts(self, chart_list: list[str]):
        """Fill charts dictionary after parsing and return it."""
        charts_data = {key: value for key, value in charts.items() if key in chart_list}

        for chart_name in chart_list:
            lines_data = None
            match chart_name:
                case 'transactions_mean':
                    # Mean transaction duration
                    lines_data = self.one_chart_data(self.names['transaction'], lambda name: self.mean[name])

                case 'transactions_rate':
                    # Transaction rate
                    lines_data = self.one_chart_data(self.names['transaction'],
                         lambda _name: {
                             'timestamp': self.count[_name]['timestamp'],
                             'data': [x / 10 for x in self.count[_name]['data']]
                         })

                case 'main':
                    # Main duration
                     lines_data = self.one_chart_data(('connect', 'request'), lambda name: self.mean[name])

                case 'main_rate':
                    # Main rate
                    lines_data = self.one_chart_data(('connect', 'request'),
                         lambda _name: {
                             'timestamp': self.count[_name]['timestamp'],
                             'data': [x / 10 for x in self.count[_name]['data']]
                         })

                case 'network':
                    # Network rate
                    lines_data = self.one_chart_data(self.names['network'],
                         lambda _name: {
                             'timestamp': self.count[_name]['timestamp'],
                             # byte -> bit (*8) -> Kbit (/1024) -> per second (/10)
                             'data': [x * 8 / 10 / 1024 for x in self.count[_name]['data']]
                         })

                case 'match_rate':
                    # Matching report
                    lines_data = self.one_chart_data(self.names['match'],
                         lambda _name: {
                             'timestamp': self.count[_name]['timestamp'],
                             'data': [x / 10 for x in self.count[_name]['data']]
                         })

                case 'http_rate':
                    # HTTP Code Response Rate
                    lines_data = self.one_chart_data(self.names['http'],
                         lambda _name: {
                             'timestamp': self.count[_name]['timestamp'],
                             'data': [x / 10 for x in self.count[_name]['data']]
                         })

                case 'error_rate':
                    # Error rate
                    lines_data = self.one_chart_data(self.names['error'],
                         lambda _name: {
                             'timestamp': self.count[_name]['timestamp'],
                             'data': [x / 10 for x in self.count[_name]['data']]
                         })

                case 'users':
                    # Simultaneous Users
                    lines_data = self.one_chart_data(('users', 'connected'),
                         lambda _name: {
                             'timestamp': self.count[_name]['timestamp'],
                             'data': [x for x in self.count[_name]['data']]
                         })

                case 'users_arrival':
                    # User arrival/depature rate
                    lines_data = self.one_chart_data(('users_count', 'finish_users_count'),
                         lambda _name: {
                             'timestamp': self.count[_name]['timestamp'],
                             'data': [x / 10 for x in self.count[_name]['data']]
                         })
                    print(f'users_arrival len={len(lines_data)}')

                case 'cpu':
                    # Mean cpu%
                    lines_data = self.one_chart_data(self.names['cpu'], lambda name: self.mean[name])

                case 'load':
                    # Mean load
                    lines_data = self.one_chart_data(self.names['load'], lambda name: self.mean[name])

                case 'freemem':
                    # Mean freemem
                    lines_data = self.one_chart_data(self.names['freemem'], lambda name: self.mean[name])

            charts_data[chart_name]['data'] = lines_data
            charts_data[chart_name]['json'] = json.dumps(lines_data)

        return charts_data
