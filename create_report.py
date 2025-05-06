from pathlib import Path

from tsung_data import Tsung

if __name__ == "__main__":
    dirname = './log_examples/tsung_20250505-1039'
    tsung = Tsung()
    tsung.parse(dirname)
