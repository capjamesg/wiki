from flask import Blueprint, request
from .config import API_KEY, WEBHOOK_URL, WEBHOOK_API_KEY
import datetime
import requests
import sqlite3

bot_interface = Blueprint("bot_interface", __name__, static_folder="static", template_folder="templates")

@bot_interface.route("/ping", methods=["POST"])
def add_entry_to_wiki():
    authorization_header = request.headers.get("Authorization")

    if not authorization_header:
        return "", 401

    if authorization_header != API_KEY:
        return "", 401

    description = request.form.get("description")
    full_description = request.form.get("description")

    word = description.split(" is ")
 
    if word:
        word = word
    else:
        word = description.split(" are ")

    word = word[0].lower().strip()

    if "<<" in full_description:
        word = word.split("<<")[0]
        description = description.split("<<")[1]
    elif "<" in full_description:
        word = word.split("<")[0]
        description = description.split("<")[1]
    elif "is" in full_description:
        description = "".join(description.split("is")[1:])
    elif "are" in full_description:
        description = "".join(description.split("are")[1:])

    for w in description.split(" "):
        if w.startswith("http://") or w.startswith("https://"):
            description = description.replace(w, "[{}]({})".format(w, w))

    headers = {
        "Authorization": "Bearer {}".format(WEBHOOK_API_KEY)
    }

    # check for entry

    connection = sqlite3.connect("wiki.db")

    word = word.strip()

    new_description = ""

    for w in description.split(" "):
        if w.startswith("http://") or w.startswith("https://"):
            new_description += "<a href=\"" + w + "\">" + w + "</a> "
        else:
            new_description += w + " "

    description = new_description

    with connection:
        cursor = connection.cursor()

        entry_exists = cursor.execute("SELECT content FROM entries WHERE slug = ?", (word,)).fetchone()

        if word.startswith("/"):
            body = {
                "message": "{} now redirects to https://wiki.jamesg.blog/{}".format(word, word)
            }

            r = requests.post(WEBHOOK_URL, data=body, headers=headers)

            if r.status_code == 200:
                return "", 200
            else:
                return "", 400

        elif entry_exists:
            entry_content = entry_exists[0] + "\n\n" + description

            cursor.execute("UPDATE entries SET content = ? WHERE slug = ?", (entry_content, word))

            cursor.close()

            body = {
                "message": "Your wiki entry has been made to https://wiki.jamesg.blog/{}".format(word)
            }

            r = requests.post(WEBHOOK_URL, data=body, headers=headers)

            if r.status_code == 200:
                return "", 200
            else:
                return "", 400

        with open("templates/stub.html", "r") as stub:
            stub = stub.read()

        full_description = stub + "\n\n" + full_description
        
        cursor.execute("INSERT INTO entries (title, slug, content, folder, is_private, last_modified) VALUES (?, ?, ?, ?, ?, ?)", (word.title(), word, full_description, "", False, datetime.datetime.now().timestamp()))

        body = {
            "message": "Your wiki entry has been made to https://wiki.jamesg.blog/{}".format(word)
        }

        r = requests.post(WEBHOOK_URL, data=body, headers=headers)

        if r.status_code == 200:
            return "", 200
        else:
            return "", 400