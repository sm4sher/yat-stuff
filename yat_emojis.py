import re
import config

from selenium import webdriver
from selenium.webdriver.common.by import By


emo_reg = re.compile(r'<span class="add-emoji-button__emoj[^>]+>([^<]+)</span>')

def get_page():
    driver = webdriver.Firefox()
    driver.implicitly_wait(3)
    driver.get("https://y.at/create")
    btns = driver.find_elements_by_css_selector('.add-emoji-button__emoji')
    emojis = [btn.text for btn in btns]
    return emojis

def parse(s):
    res = emo_reg.findall(s)
    return res

if __name__ == "__main__":
    print(get_page())
    exit()
    with open("y.at.html", "r") as f:
        s = f.read()

    res = parse(s)
    print(res)
    print(len(res), "emojis")
