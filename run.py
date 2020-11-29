from src import run_code
import sys


if len(sys.argv) >= 2:
    with open(sys.argv[1],'r') as file:
        code = file.read()
    run_code(code)
else:
    print('Usage: python3 run.py <filename>')
    raise TypeError('Expected a <file>')