import sys

url = sys.argv[1]

with open('blacklist.txt', 'w') as f:
    f.write(url)

print(url + " successfully added to blacklist!")