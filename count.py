from os import walk, path
lens = 0
for address, dirs, files in walk(path.curdir):
    for file in files:
        if file.split(".")[-1] == 'py' and ".venv" not in address and "migrations" not in address:
            with open(f"{address}/{file}", "r") as fl:
                lines = fl.readlines()
                lens += len(lines)

print()
