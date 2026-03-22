"""
Read Locust *_full_data_stats_history.csv file, convert to dict with data.
CSV headers:
Timestamp,User Count,Type,Name,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%,Total Request Count,Total Failure Count,Total Median Response Time,Total Average Response Time,Total Min Response Time,Total Max Response Time,Total Average Content Size
To headers:
timestamp,user_count,type,name,rps,fail_rps,p50,p66,p75,p80,p90,p95,p98,p99,p999,p9999,p100,total_count,total_falure_count,total_median_response_time,total_avr_response_time,total_min_response_time,total_max_response_time,total_avr_content_size
1753970290,6,GET,payments~currencies,0.333333,0.000000,85,89,89,99,99,99,99,99,99,99,99,6,0,85,87.52131665823981,76.93610002752393,98.96810003556311,2635.0

[
  {
    'timestamp': 1746469501,
    "/v1/auth/login": Data("/v1/auth/login", "1", "853.515", "0", "853.515", "853.515", "0", "0"),
    "users~banners": Data("users~banners", "1", "853.515", "0", "853.515", "853.515", "0", "0"),
    "match": CountData("match", "3", "15"),
  }
]
"""
import csv
from collections import namedtuple, defaultdict
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Collection

from utils import str_number, str_sec, number, str_bytes, str_bits_per_sec

CHART_DURATION_TEMPLATE = {
        'title': '{} transaction duration',
        'xheader': 'time (sec of running test)',
        'yheader': 'transaction duration (msec)',
        'data': []
    }

charts = {
    'transactions_rate': {
        'title': 'Transactions rate',
        'xheader': 'time (sec of running test)',
        'yheader': 'transactions/sec',
        'data': []
    },
    # 'sum_transactions_rate': {
    #     'title': 'Transactions rate per service',
    #     'xheader': 'time (sec of running test)',
    #     'yheader': 'transactions/sec',
    #     'data': []
    # },
    'transactions_p50': {
        'title': 'Median transaction duration',
        'xheader': 'time (sec of running test)',
        'yheader': 'transaction duration (msec)',
        'data': []
    },
}
# PERCENTILE_HEADERS = 'p50 p66 p75 p80 p90 p95 p98 p99 p999 p9999 p100'
PERCENTILE_HEADERS = 'p50 p60 p70 p80 p90 p100'
COLUMN_HEADERS = f'type name timestamp user_count rps fail_rps {PERCENTILE_HEADERS} total_count total_falure_count total_median_response_time total_avr_response_time total_min_response_time total_max_response_time total_avr_content_size'
DATA_HEADERS = f'user_count rps fail_rps {PERCENTILE_HEADERS} total_count total_falure_count total_median_response_time total_avr_response_time total_min_response_time total_max_response_time total_avr_content_size'.split()
Data = namedtuple('Data', 'type name timestamp user_count rps fail_rps p50 p66 p75 p80 p90 p95 p98 p99 p999 p9999 p100 total_count total_falure_count total_median_response_time total_avr_response_time total_min_response_time total_max_response_time total_avr_content_size')
ValueAtTime = namedtuple('ValueAtTime', 'timestamp value')

class Locust:

    def __init__(self):
        self.start_timestamp: int = 0    # int(self.data[0]['timestamp']) - начало теста
        # self.data = [
        #   {'timestamp': 1746441577, 'payments~currencies': Data(name='currencies', count='3', mean='0.35333333333333333', stddev_10sec='0.10977654070378101', max='0.481', min='0.213', mean='0', count='0'), 'tr_get_host_name': Data(name='tr_get_host_name', count_10sec='1', mean_10sec='0.211', stddev_10sec='0', max='0.211', min='0.211', mean='0', count='0'), 'tr_profile': Data(name='tr_profile', count_10sec='1', mean_10sec='92.286', stddev_10sec='0', max='92.286', min='92.286', mean='0', count='0'), 'tr_cb_balance': Data(name='tr_cb_balance', count_10sec='2', mean_10sec='78.20349999999999', stddev_10sec='0.6774999999999984', max='78.881', min='77.526', mean='0', count='0'), 'tr_deposit': Data(name='tr_deposit', count_10sec='2', mean_10sec='210.4145', stddev_10sec='94.92249999999999', max='305.337', min='115.492', mean='0', count='0'), 'tr_cb_bet': Data(name='tr_cb_bet', count_10sec='1', mean_10sec='128.603', stddev_10sec='0', max='128.603', min='128.603', mean='0', count='0'), 'tr_cb_liveness': Data(name='tr_cb_liveness', count_10sec='2', mean_10sec='57.5655', stddev_10sec='0.23550000000000182', max='57.801', min='57.33', mean='0', count='0'), 'tr_set_var': Data(name='tr_set_var', count_10sec='1', mean_10sec='1.319', stddev_10sec='0', max='1.319', min='1.319', mean='0', count='0'), 'tr_game_init_by_alias_100hp': Data(name='tr_game_init_by_alias_100hp', count_10sec='1', mean_10sec='516.781', stddev_10sec='0', max='516.781', min='516.781', mean='0', count='0'), 'tr_registration': Data(name='tr_registration', count_10sec='1', mean_10sec='853.515', stddev_10sec='0', max='853.515', min='853.515', mean='0', count='0'), 'tr_cb_win': Data(name='tr_cb_win', count_10sec='1', mean_10sec='120.871', stddev_10sec='0', max='120.871', min='120.871', mean='0', count='0')},
        #   {'timestamp': 1746441587, 'user~profile': Data(name='profile', count='17', mean='0.2787058823529412', stddev_10sec='0.08338201576858896', max='0.481', min='0.154', mean='0.35333333333333333', count='3'), 'tr_get_host_name': Data(name='tr_get_host_name', count_10sec='5', mean_10sec='0.09519999999999999', stddev_10sec='9.797958971132722e-4', max='0.211', min='0.094', mean='0.211', count='1'), 'tr_profile': Data(name='tr_profile', count_10sec='3', mean_10sec='68.70466666666668', stddev_10sec='1.733355192169859', max='92.286', min='67.252', mean='92.286', count='1'), 'tr_cb_balance': Data(name='tr_cb_balance', count_10sec='10', mean_10sec='219.93030000000005', stddev_10sec='423.06610577427494', max='1488.985', min='70.918', mean='78.20349999999999', count='2'), 'tr_deposit': Data(name='tr_deposit', count_10sec='10', mean_10sec='256.9764', stddev_10sec='177.17312444453867', max='742.261', min='115.492', mean='210.4145', count='2'), 'tr_cb_bet': Data(name='tr_cb_bet', count_10sec='11', mean_10sec='111.66672727272726', stddev_10sec='6.812481180503231', max='128.603', min='99.866', mean='128.603', count='1'), 'tr_cb_liveness': Data(name='tr_cb_liveness', count_10sec='11', mean_10sec='54.796', stddev_10sec='3.7567712442758854', max='60.75', min='50.013', mean='57.5655', count='2'), 'tr_set_var': Data(name='tr_set_var', count_10sec='5', mean_10sec='0.4328', stddev_10sec='0.025063120316512876', max='1.319', min='0.399', mean='1.319', count='1'), 'tr_game_init_by_alias_100hp': Data(name='tr_game_init_by_alias_100hp', count_10sec='2', mean_10sec='381.39', stddev_10sec='13.959999999999994', max='516.781', min='367.43', mean='516.781', count='1'), 'tr_registration': Data(name='tr_registration', count_10sec='5', mean_10sec='573.5674000000001', stddev_10sec='609.6595576200214', max='1792.548', min='253.876', mean='853.515', count='1'), 'tr_cb_win': Data(name='tr_cb_win', count_10sec='11', mean_10sec='117.02181818181818', stddev_10sec='6.741436531808092', max='129.156', min='104.488', mean='120.871', count='1')}
        # ]
        self.data = []
        # ??? all possible names in all records
        # { name1: [mean_10sec_vales], name2: [mean_10sec_vales], ... } for each name
        # self.mean = {}
        # { name1: [count_10sec_vales], name2: [count_10sec_vales], ... } for each name
        # self.count = {}

    def __str__(self):
        return json.dumps(self.data)


    def parse(self, filepath: str | Path):
        """Parse full_history.cvs from dirpath."""
        with open(filepath, 'r') as csvfile:
            # print(next(csvfile))
            reader = csv.reader(csvfile, delimiter=',')
            print(next(reader))

            for row in reader:
                if not row or "N/A" in row:
                    continue
                # Users = 0
                row_numbers = map(lambda x: float(x) if '.' in x else int(x), [row[1]] + row[4:])
                #d = Data(row[2], row[3], *row_numbers)
                d = {
                    'timestamp': int(row[0]),
                    'name': row[3],
                    'type': row[2]
                }
                d.update(dict(zip(DATA_HEADERS, row_numbers)))
                print(d)
                if d['user_count'] == '0' or d['name'] == 'Aggregated':
                    continue

                # data = {'timestamp': d.timestamp, d.name: d}
                self.data.append(d)

    @staticmethod
    def get_names(data: list[dict]):
        return set(record['name'] for record in data)

    def process(self, ignore_transactions: Collection[str] | None = None):
        """Aggregate data by names for charts
        self.xydata = {
            '/v1/users/login': {
                'rps': [{'timestamp':1753970288, 'value':0.333333},],
                'fail_rps': [{'timestamp':1753970288, 'value':0.1},],
            },
            'payments~currencies': {
                'rps': [{'timestamp':1753970288, 'value':0.333333},],
                'fail_rps': [{'timestamp':1753970288, 'value':0.1},],
            },
        }
        """
        self.endpoints = self.get_names(self.data)
        print(self.endpoints)
        self.xydata = {}
        for endpoint in self.endpoints:
            self.xydata[endpoint] = {header: list() for header in DATA_HEADERS}
            self.xydata[endpoint]['timestamp'] = 0 # dummy timestamp
        self.start_timestamp = self.data[0]['timestamp']
        for data in self.data:
            name = data['name']
            timestamp = data['timestamp']
            if not self.xydata[name]['timestamp']:
                self.xydata[name]['timestamp'] = timestamp
            for header in DATA_HEADERS:
                self.xydata[name][header].append(data[header])
        print(self.xydata)

    def tables(self, table_list: list[str]):
        return {}

    def one_chart_data(self, names: Collection[str], get_data_by_name) -> list[dict]:
        """Build (x,y) data for all chart series by names and get_data_by_name function."""
        lines_data = []
        for name in sorted(names):
            data = get_data_by_name(name)
            y = data
            ylen = len(y)
            x0 = self.xydata[name]['timestamp'] - self.start_timestamp
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
                case 'transactions_p50':
                    # Mean transaction duration
                    lines_data = self.one_chart_data(self.endpoints, lambda name: self.xydata[name]['p50'])

                case  'transactions_rate':
                    lines_data = self.one_chart_data(self.endpoints, lambda name: self.xydata[name]['rps'])

            charts_data[chart_name]['data'] = lines_data
            charts_data[chart_name]['json'] = json.dumps(lines_data)

        return charts_data



if __name__ == '__main__':
    locust = Locust()
    filename = Path(__file__).resolve().parent / 'log_examples/locust_data/short_full_data_stats_history.csv'
    print(filename)
    # with open(filename) as fin:
    #     for line in fin:
    #         print(line)
    locust.parse(filename)
    # print(locust.data)
    locust.process()

