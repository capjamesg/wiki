from flask import Blueprint, session, redirect, abort, request, flash
from flask.templating import render_template
from werkzeug.utils import secure_filename
from .config import OWNER
import markdown
import datetime
import sqlite3

main = Blueprint("main", __name__, static_folder="static", template_folder="templates")

def is_signed_in(session, needs_owner=False):
    if not session.get("me"):
        return False

    if needs_owner == True and session.get("me") != OWNER:
        return False

    return True

@main.route("/theme")
def set_theme():
    if session.get("theme") == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"
    
    return redirect("/")

@main.route("/")
def index():
    title = "capjamesg's Personal Wiki"

    database = sqlite3.connect("wiki.db")

    user = is_signed_in(session, True)

    if user == False:
        return redirect("/login")
    
    with database:
        cursor = database.cursor()

        file_content = cursor.execute("SELECT content, last_modified FROM entries WHERE slug = ?", ("index",)).fetchone()

        pages = cursor.execute("SELECT title, slug FROM entries WHERE slug != 'index';").fetchall()

        last_modified = datetime.datetime.fromtimestamp(file_content[1]).strftime("%b %d, %Y (%H:%M:%S)")

    return render_template("entry.html", title=title, contents=markdown.markdown(file_content[0]), is_wiki_entry=True, slug="/", pages=pages, last_modified=last_modified)

@main.route("/<file>")
def serve_file(file):
    file = secure_filename(file).lower()

    title = "capjamesg's Personal Wiki"

    database = sqlite3.connect("wiki.db")
    
    with database:
        cursor = database.cursor()

        file_content = cursor.execute("SELECT title, content, last_modified, is_private FROM entries WHERE slug = ?", (file,)).fetchone()

        if not file_content:
            abort(404)

        # require sign in to access some wiki pages
        if file_content[3] == 1:
            if not is_signed_in(session):
                abort(403)

        title = file_content[0]

        pages = cursor.execute("SELECT title, slug FROM entries WHERE slug != 'index';").fetchall()

        last_modified = datetime.datetime.fromtimestamp(file_content[2]).strftime("%b %d, %Y (%H:%M:%S)")

    if file_content is None:
        abort(404)

    return render_template("entry.html", title=title, contents=markdown.markdown(file_content[1], output_format="html"), is_wiki_entry=True, slug=file, pages=pages, last_modified=last_modified)

@main.route("/wiki/search", methods=["GET", "POST"])
def search():
    search_term = request.query.get("query")

    database = sqlite3.connect("wiki.db")

    with database:
        cursor = database.cursor()
        pages = cursor.execute("SELECT title, slug FROM entries WHERE slug != 'index';").fetchall()

        if request.method == "POST" or search_term:
            results = cursor.execute("SELECT slug, title FROM entries WHERE title LIKE ?", ("%" + search_term + "%",)).fetchall()

            return render_template("search.html", results=results, pages=pages, title="Search Wiki")

    user = is_signed_in(session, True)

    if user == False:
        return redirect("/login")
        
    return render_template("search.html", pages=pages, title="Search Wiki")

@main.route("/wiki/entries", methods=["GET", "POST"])
def show_all_entries():
    database = sqlite3.connect("wiki.db")

    user = is_signed_in(session, True)

    if user == False:
        return redirect("/login")

    with database:
        cursor = database.cursor()

        results = cursor.execute("SELECT slug, title FROM entries ORDER BY last_modified DESC;").fetchall()

        pages = cursor.execute("SELECT title, slug FROM entries WHERE slug != 'index';").fetchall()

    return render_template("entries.html", entries=results, pages=pages, title="View All Wiki Entries")

@main.route("/wiki/random")
def go_to_random_entry():
    database = sqlite3.connect("wiki.db")

    with database:
        cursor = database.cursor()

        results = cursor.execute("SELECT slug, title FROM entries ORDER BY RANDOM() LIMIT 1;").fetchone()

    return redirect("/" + results[0])