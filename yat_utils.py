import regex
from urllib.parse import urlparse, unquote

def split_yat(yat):
    return regex.findall(r'\X', yat, regex.U)

def get_yat_from_url(url):
    return unquote(urlparse(url).path).replace('/', '')

def twitter_sanitize(s, max_length=None):
    # escape urls by replacing x.xx with x[.]xx (low effort, I don't care that much)
    s = regex.sub(r'(\S)\.(\S{2,})', r'\1[.]\2', s)
    # avoid mention injection
    s = s.replace('@', '@.')
    if max_length and len(s) > max_length:
        l = (max_length - 10) // 2
        s = s[:l] + " [...] " + s[-l:]
    return s