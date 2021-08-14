import regex
from urllib.parse import urlparse, unquote

def split_yat(yat):
    return regex.findall(r'\X', yat, regex.U)

def get_yat_from_url(url):
    return unquote(urlparse(url).path).replace('/', '')
