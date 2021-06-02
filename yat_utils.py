import regex

def split_yat(yat):
    return regex.findall(r'\X', yat, regex.U)