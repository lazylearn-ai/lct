def write_temp(s):
    with open("tempstorage.txt", "w") as f:
        f.write(s)


def read_temp():
    with open("tempstorage.txt", "r") as f:
        return f.read()