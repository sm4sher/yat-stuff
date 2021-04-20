import re

with open("y.at.html", "r") as f:
	s = f.read()

emo_reg = re.compile(r'<span class="add-emoji-button__emoj[^>]+>([^<]+)</span>')


res = emo_reg.findall(s)
print(res)
print(len(res), "emojis")
