import argparse
import configparser
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from locust_data import Locust
from tsung_data import Tsung

base_dir = Path(__file__).parent

def create_report(report_dirname: Path, report_date: str, tables: dict, charts: dict):
    environment = Environment(loader=FileSystemLoader(base_dir / "templates/"))
    template = environment.get_template("main.html")

    filename = f"report_{report_date}.html"
    content = template.render(
        title = report_date,
        tables=tables,
        charts=charts
    )
    with open(report_dirname / filename, mode="w", encoding="utf-8") as message:
        message.write(content)
        print(f"... wrote {filename}")

if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("framework", help='Choose framework: tsung, locust')

    argparser.add_argument("dirname", help='Path to directory with tsung.log file')
    args = argparser.parse_args()
    log_dirname = Path(args.dirname).resolve().absolute()
    log_datetime = log_dirname.name

    config = configparser.RawConfigParser(allow_no_value=True)
    # или файл в текущей директории, или файл по умолчанию
    file = Path('report.ini')
    if not file.exists():
        file = base_dir / file
    config.read(file)

    match args.framework:
        case 'tsung':
            tsung = Tsung()
            tsung.parse(log_dirname)
            tsung.process(ignore_transactions=set(config['tr_ignore']))
            create_report(log_dirname, log_datetime, tsung.tables(list(config['tables'])), tsung.charts(list(config['charts'])))

        case 'locust':
            locust = Locust()
            locust.parse(log_dirname)
            # locust.process(ignore_transactions=set(config['tr_ignore']))
            locust.process()
            charts_names = ['transactions_rate', 'transactions_p50']
            # create_report(log_dirname, log_datetime, locust.tables(list(config['tables'])), locust.charts(list(config['charts'])))
            create_report(log_dirname.parent, log_datetime, locust.tables(list(config['tables'])), locust.charts(charts_names))
            # create_report(log_dirname.parent, log_datetime, locust.tables(list()), locust.charts(charts_names))
