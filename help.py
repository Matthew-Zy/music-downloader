import re
import sys

try:
    makefiles = sys.argv[1].split()
except IndexError:
    print("Please provide a makefile file for argv[1]")
    sys.exit()
commands = []

for makefile in makefiles:
    with open(makefile, encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^([a-zA-Z_-]+):.*?## (.*)$", line)
            if match:
                commands.append(match.groups())

print("Available Commands:")

for name, description in sorted(commands):
    print(f"\033[36m{name:<15}\033[0m {description}")