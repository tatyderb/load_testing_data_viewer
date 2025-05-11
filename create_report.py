import argparse
import configparser
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from tsung_data import Tsung

def create_report(report_dirname: Path, report_date: str, tables: dict, charts: dict):
    environment = Environment(loader=FileSystemLoader("templates/"))
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
    argparser.add_argument("dirname", help='Path to directory with tsung.log file')
    args = argparser.parse_args()
    log_dirname = Path(args.dirname).resolve().absolute()
    log_datetime = log_dirname.name

    config = configparser.RawConfigParser(allow_no_value=True)
    config.read('report.ini')

    tsung = Tsung()
    tsung.parse(log_dirname)
    tsung.process()
    create_report(log_dirname, log_datetime, tsung.tables(list(config['tables'])), tsung.charts(list(config['charts'])))
