from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from tsung_data import Tsung

def create_report(report_date: str, tables: dict, charts: dict):
    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("main.html")

    filename = f"report_{report_date}.html"
    content = template.render(
        title = report_date,
        tables=tables
    )
    with open(filename, mode="w", encoding="utf-8") as message:
        message.write(content)
        print(f"... wrote {filename}")

if __name__ == "__main__":
    dirname = './log_examples/tsung_20250505-1039'
    tsung = Tsung()
    tsung.parse(dirname)
    tsung.process()
    create_report(dirname[-13:], tsung.tables(), tsung.charts())
