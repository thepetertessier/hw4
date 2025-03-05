import subprocess
from pathlib import Path
from termcolor import colored
import sys

path_to_main = 'min.py' if sys.argv[1] == 'min' else 'main.py'

input_dir = Path('input')
header = f'{"Test Name":<20} | {"Expected":<8} | {"Actual":<8} | Result'
print(header)
print('-'*len(header))
for test_file in input_dir.iterdir():
    with open(test_file, "r") as infile:
        name, expected = test_file.stem.split('-')
        print(f'{name:<20} | {expected:<8} | ', end='')
        actual = subprocess.run(['python3', path_to_main], stdin=infile, capture_output=True, text=True).stdout.strip()
        result = colored('Passed', 'green') if actual == expected else colored('Failed', 'red')
        print(f'{actual:<8} | {result}')
