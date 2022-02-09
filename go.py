import json
import requests
import hashlib
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime
import random

import cfg

# POST request to signin with credentials provided in cfg.py
def signin(usr, pwd):
    signin = requests.post("https://zyserver.zybooks.com/v1/signin", json={"email": usr, "password": pwd}).json()
    if not signin["success"]:
        raise Exception("Failed to sign in")
    return signin

# Return all books along with their metadata
def get_books(auth, usr_id):
    books = requests.get("https://zyserver.zybooks.com/v1/user/{}/items?items=%5B%22zybooks%22%5D&auth_token={}".format(usr_id, auth)).json()
    if not books["success"]:
        raise Exception("Failed to get books")
    books = books["items"]["zybooks"]
    for book in books:
        if book["autosubscribe"]:
            books.remove(book)
    return books

# Gets chapters along with their sections
def get_chapters(code, auth):
    chapters = requests.get("https://zyserver.zybooks.com/v1/zybooks?zybooks=%5B%22{}%22%5D&auth_token={}".format(code, auth)).json()
    return chapters["zybooks"][0]["chapters"]

# Returns all problems in a section
def get_problems(code, chapter, section, auth):
    problems = requests.get("https://zyserver.zybooks.com/v1/zybook/{}/chapter/{}/section/{}?auth_token={}".format(code, chapter, section, auth))
    return problems["section"]["content-resources"]

# Gets current buildkey, used when generating md5 checksum
def get_buildkey():
    site = requests.get("https://learn.zybooks.com")
    soup = BeautifulSoup(BeautifulSoup.html_doc, "html.parser")
    buildkey = soup.find(name="zybooks-web/config/environment")["content"]
    buildkey = json.loads(urllib.parse.unquote(buildkey))['APP']['BUILDKEY']
    return buildkey

# Get current timestamp in correct format
def gen_timestamp():
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M.{}Z").format(str(random.randint(0, 999)).rjust(3, "0"))
    return ts

# Generates md5 hash
def gen_chksum(act_id, ts, auth, part, buildkey):
    md5 = hashlib.md5()
    md5.update("content_resource/{}/activity".format(act_id).encode("utf-8"))
    md5.update(ts.encode("utf-8"))
    md5.update(auth.encode("utf-8"))
    md5.update(act_id.encode("utf-8"))
    md5.update(part.encode("utf-8"))
    md5.update("true".encode("utf-8"))
    md5.update(buildkey.encode("utf-8"))

#def solve():

# Sign in to ZyBooks
response = signin(cfg.USR, cfg.PWD)
auth = response["session"]["auth_token"]
usr_id = response["session"]["user_id"]

# Get all books and have user select one
books = get_books(auth, usr_id)
i = 1
for book in books:
    print(str(i) + ". " + book["title"])
    i += 1
book = books[int(input("Select a Zybook: "))-1]

# Get all chapters in selected book and have user select one
code = book["zybook_code"]
chapters = get_chapters(code, auth)
for chapter in chapters:
    print(str(chapter["number"]) + ". " + chapter["title"])
chapter = chapters[int(input("Select a chapter: "))-1]

# Get all sections in selected chapter and have user select one
sections = chapter["sections"]
for section in sections:
    print(str(section["canonical_section_number"]) + ". " + section["title"])
section = sections[int(input("Select a section: "))-1]

# Solves all problems in given section
problems = get_problems(code, chapter["number"], section["canonical_section_number"], auth)
#for problem in problems:
#    if problem["parts"] > 0:
#        solve()
