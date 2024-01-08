import os

def state_name(s):
    return s.replace("africa_", "").split("_orthogra")[0].split("_(orth")[0].replace("_", " ").strip()

res = ""

for f in filter(lambda s : '.svg' in s, os.listdir()):
    res += '{ "question": { "type": "image","content": "'+f+'"},"answer": {"type": "text","content": "'+state_name(f)+'" }, "importance": 0.5},\n'

with open("out.json", "w") as f:
    f.write(res)