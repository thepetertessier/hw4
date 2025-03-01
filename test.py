import subprocess

path_to_main = 'main.py'

with open("example_input.txt", "r") as infile:
    subprocess.run(['python3', path_to_main], stdin=infile)
