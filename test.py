import subprocess
import os
from pathlib import Path

path_to_main = 'main.py'

input_dir = Path('input')
for test_file in input_dir.iterdir():
    with open(test_file, "r") as infile:
        name, expected = test_file.stem.split('-')
        print(f'{name:<20} | Expected: {expected}')
        subprocess.run(['python3', path_to_main], stdin=infile)
