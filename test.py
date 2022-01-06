import re

f = open("2.json", "r")
aa = f.read()

a = re.sub(r'color:(.*?);', '', aa)


f.close()

f = open("3.json", "a")
f.write(a)
f.close()

