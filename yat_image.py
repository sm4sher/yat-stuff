from PIL import Image, ImageDraw, ImageFont
import regex
import math
from io import BytesIO
from yat_api import get_infos, get_emoji_list

fonts = [
	{
		'font': ImageFont.truetype("fonts/AppleColorEmoji.ttf", 109), 
		'size': 109,
		'name': "Apple",
	},
	{
		'font': ImageFont.truetype("fonts/twemoji_JF.ttf", 61), 
		'size': 61,
		'name': "Twitter & Discord",
	},
	{
		'font': ImageFont.truetype("fonts/NotoColorEmoji.ttf", 109), 
		'size': 109,
		'name': "Android",
	},
	{
		'font': ImageFont.truetype("fonts/Samsung.ttf", 92), 
		'size': 92,
		'name': "Samsung",
	},
	
]
NAME_FONT = ImageFont.truetype("truetype/lberation/LiberationSansNarrow-Regular.ttf", 20)
TITLE_FONT = ImageFont.truetype("truetype/lberation/LiberationSans-Bold.ttf", 20)
INFO_FONT = ImageFont.truetype("truetype/lberation/LiberationSans-Regular.ttf", 20)
CREDIT_FONT = ImageFont.truetype("truetype/lberation/LiberationSans-Bold.ttf", 10)

'''
emojis = ['😂', '😇', '🙃', '😍', '😜', '😘', '🤓', '😎', '😢', '😱', '🤔', '😶', '😵', '🤐', '🤢', '🤧', '😷', '🤕', '🤑', '🤠', '😈', '🤡', '💩', '👻', '☠️', '👽', '👾', '🤖', '🎃', '💪', '💋', '💄', '👂', '👃', '👣', '👁️', '👀', '👶', '👏', '🤝', '🙌', '👍', '👎', '✊', '✌️', '🤘', '👌', '👉', '👋', '✍️', '🙏', '💅', '🤳', '💃', '👕', '👖', '👗', '👙', '👘', '👠', '👢', '👞', '👟', '🎩', '👒', '🎓', '👑', '💍', '👛', '💼', '🎒', '🐶', '🐱', '🐭', '🐰', '🦊', '🐻', '🐼', '🐮', '🐨', '🐯', '🦁', '🐷', '🐽', '🐸', '🐵', '🙈', '🐔', '🐧', '🐣', '🦆', '🦅', '🦉', '🦇', '🐺', '🐗', '🐴', '🦄', '🐝', '🐛', '🦋', '🐌', '🐞', '🐜', '🕷️', '🕸️', '🦂', '🐢', '🐍', '🦎', '🐊', '🦍', '🦏', '🐙', '🦀', '🐬', '🐋', '🦈', '🐘', '🐪', '🐃', '🐑', '🐐', '🦌', '🦃', '🐀', '🐾', '🐉', '🌵', '🌲', '🌴', '🍀', '🎋', '🍁', '🍄', '🐚', '💐', '🌹', '🌸', '🌻', '🌕', '🌙', '⭐', '⚡', '☄️', '💥', '🔥', '🌪️', '🌈', '☀️', '☁️', '❄️', '⛄', '💨', '💦', '🌊', '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', '🍑', '🍍', '🥝', '🍆', '🥑', '🥒', '🌶️', '🌽', '🥕', '🥔', '🥐', '🍞', '🧀', '🥚', '🍳', '🥞', '🥓', '🍗', '🌭', '🍔', '🍟', '🍕', '🥙', '🌮', '🌯', '🥗', '🍝', '🍜', '🍣', '🍱', '🍤', '🍚', '🍘', '🍥', '🍡', '🍦', '🎂', '🍭', '🍬', '🍫', '🍿', '🍩', '🍪', '🥜', '🌰', '🍯', '🥛', '🍼', '☕', '🍵', '🍶', '🍺', '🍷', '🥃', '🍸', '🍾', '🥄', '🍽️', '⚽', '🏀', '🏈', '⚾', '🎾', '🏐', '🎱', '🏓', '🏸', '🏒', '🏏', '🥅', '⛳', '🏹', '🎣', '🥊', '🥋', '🎽', '⛸️', '🎿', '🏆', '🎖️', '🎟️', '🎪', '🎭', '🎨', '🎬', '🎤', '🎧', '🎼', '🎹', '🥁', '🎷', '🎺', '🎸', '🎻', '🎲', '♟️', '🎯', '🎳', '🎮', '🎰', '🚗', '🏎️', '🚓', '🚑', '🚒', '🚚', '🚜', '🚲', '🛵', '🏍️', '🚨', '🚠', '🚂', '✈️', '💺', '🚀', '🚁', '🛶', '⛵', '🚢', '⚓', '🚧', '🚦', '🗺️', '🗿', '🗽', '🗼', '🏰', '🏯', '🏟️', '🎡', '🎢', '🎠', '🏖️', '⛰️', '🏕️', '🏠', '🏭', '🏥', '🏦', '🏛️', '⛪', '🕌', '🕍', '🗾', '⌚', '📱', '💻', '🖨️', '🕹️', '💾', '📷', '🎥', '📟', '📺', '📻', '🎛️', '⏰', '⌛', '📡', '🔋', '🔌', '💡', '🔦', '🕯️', '🛢️', '💵', '💰', '💳', '💎', '⚖️', '🔧', '🔩', '⚙️', '⛓️', '🔫', '💣', '🔪', '🗡️', '🛡️', '🚬', '⚰️', '🏺', '🔮', '📿', '💈', '🔭', '🔬', '🕳️', '💊', '💉', '🚽', '🚰', '🚿', '🛋️', '🔑', '🚪', '🗄️', '📎', '📏', '📐', '📌', '✂️', '🗑️', '🖼️', '🛍️', '🛒', '🎁', '🎈', '🎏', '🎀', '🎉', '🎎', '🏮', '🎐', '✉️', '📦', '📜', '📈', '🗞️', '📓', '📖', '🖍️', '✏️', '🔒', '❤️', '💔', '✝️', '☪️', '🕉️', '☸️', '✡️', '🕎', '☯️', '☦️', '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓', '🆔', '⚛️', '☢️', '🆚', '🆘', '🚫', '🚭', '💯', '❗', '❓', '⚠️', '🔱', '⚜️', '♻️', '🏧', '🆒', '🆕', '🆓', '🆙', '🎵', '➕', '💱', '🔔', '♠️', '♣️', '🃏', '🀄', '🏁']
'''
emojis = get_emoji_list()

WD = 400
HT = 650

def make_background():
	imgsize = (WD, HT) #The size of the image

	image = Image.new('RGBA', imgsize) #Create the image

	innerColor = [200, 200, 255] #Color at the center
	outerColor = [80, 80, 255] #Color at the corners


	for y in range(imgsize[1]):
		for x in range(imgsize[0]):

		    #Find the distance to the center
		    distanceToCenter = math.sqrt((x - imgsize[0]/2) ** 2 + (y - imgsize[1]/2) ** 2)

		    #Make it on a scale from 0 to 1
		    distanceToCenter = float(distanceToCenter) / (math.sqrt(2) * imgsize[0]/2)

		    #Calculate r, g, and b values
		    r = outerColor[0] * distanceToCenter + innerColor[0] * (1 - distanceToCenter)
		    g = outerColor[1] * distanceToCenter + innerColor[1] * (1 - distanceToCenter)
		    b = outerColor[2] * distanceToCenter + innerColor[2] * (1 - distanceToCenter)


		    #Place the pixel        
		    image.putpixel((x, y), (int(r), int(g), int(b)))
	return image

def check_seq(seq):
	if not 1 <= len(seq) <= 5:
		return False, "Invalid length"
	for emo in seq:
		if emo not in emojis and emo + b'\xef\xb8\x8f'.decode() not in emojis: # emojis might have the variation modifier or not. Are they other modifiers that could be annoying like that?
			return False, "Invalid emoji ({})".format(emo)
	return True, ""

def make_img(seq):
	res, msg = check_seq(seq)
	if not res:
		print(msg)
		return
	txt = ''.join(seq)
	#img = Image.new("RGBA", (900, 1000), (255, 255, 255, 0))
	img = make_background()
	d = ImageDraw.Draw(img)
	inner_wd = round(0.9*WD)
	margin = (WD - inner_wd) // 2
	x = margin
	d.text((WD//2, x), "Here's how your Yat looks on", anchor="mt", font=TITLE_FONT)
	x += 40
	for i, fnt in enumerate(fonts):
		d.text((margin, x), fnt['name'], font=NAME_FONT)
		x += 35
		emo_strip = make_emo_strip(txt, fnt, inner_wd)
		img.paste(emo_strip, (margin, x), emo_strip) # alpha from emo_strip used as mask =)
		x += emo_strip.height + margin
	
	info_strip = make_info_strip(txt)
	img.paste(info_strip, (0, x), info_strip)
	credit_strip = make_credit()
	img.paste(credit_strip, (WD-credit_strip.width-2, HT-credit_strip.height-2), credit_strip)
	#img.show()
	f = BytesIO()
	img.save(f, "png")
	f.seek(0)
	#with open('test.png', 'wb+') as t:
	#	t.write(f.read())
	return f

def make_emo_strip(txt, font, wd):
	strip_wd = round(6.2*font['size'])
	strip_ht = round(1.3*font['size'])
	emo_strip = Image.new("RGBA", (strip_wd, strip_ht))
	d_strip = ImageDraw.Draw(emo_strip)
	d_strip.text((strip_wd//2,strip_ht//2), txt, anchor="mm", font=font['font'], embedded_color=True)
	factor = wd / strip_wd
	final_ht = round(factor*strip_ht)
	emo_strip = emo_strip.resize((wd, final_ht))
	return emo_strip


def inttohex(n):
	return hex(n).replace('0x', '').zfill(2)

def rs_gradient(rs):
	s = 170
	##666666 to #ffd700
	# red: 102 to 255 linear
	red = math.floor(s + rs * (255-s) / 100)
	# green: 102 to 215 linear
	green = math.floor(s + rs * (215-s) / 100)
	# blue: 102 to 0 linear
	blue = math.floor(s - rs * s / 100)
	return "#{}{}{}".format(*map(inttohex, [red, green, blue]))

def make_info_strip(emoji_id):
	infos = get_infos(emoji_id).get('res')
	if not infos:
		rs = '?'
		rs_col = None
		avail = '???'
		hype = '???'
	else:
		rs = infos.get('rhythm_score')
		rs_col = rs_gradient(rs)
		avail = infos.get('availability')
		hype = min(100, infos.get('stats')[0].get('value'))
	avail_col = None
	if avail == "Taken":
		avail_col = "#CC0000"
	elif avail == "Available":
		avail_col = "#00FF00"

	info_strip = Image.new("RGBA", (WD, 50))
	inner_wd = round(0.9*WD)
	margin = (WD - inner_wd) // 2
	d = ImageDraw.Draw(info_strip)
	d.text((margin, 0), "RS{}".format(rs), anchor="lt", font=INFO_FONT, fill=rs_col)
	d.text((WD//2, 0), avail, anchor="mt", font=INFO_FONT, fill=avail_col)
	d.text((WD-margin, 0), "{}% hype".format(hype), anchor="rt", font=INFO_FONT)
	return info_strip	

def make_credit():
	credit_strip = Image.new("RGBA", (120, 20))
	d = ImageDraw.Draw(credit_strip)
	d.text((0, 0), "By", font=CREDIT_FONT)
	emo_strip = make_emo_strip("🥚🐣🦆🍗", fonts[0], 70)
	credit_strip.paste(emo_strip, (12, 0))
	d.text((emo_strip.width+9, 0), ". y . at", font=CREDIT_FONT)
	return credit_strip

def parse_string(s):
	return regex.findall(r'\X', s, regex.U)

def find_font_size():
	sizes = []
	for i in range(250):
		try:
			fnt = ImageFont.truetype("fonts/Samsung.ttf", i)
		except OSError:
			continue
		sizes.append(i)
	print(sizes)

if __name__ == "__main__":
	print(len(emojis))
	inp = "🐣🐣🐣"
	seq = parse_string(inp)
	make_img(seq)
	#find_font_size()
	exit()
	for e in seq:
		print(e)
	for e in emojis:
		if len(e) != 1:
			print(e, len(e))
