from flask import Blueprint, session, redirect, abort, request, flash
from flask.templating import render_template
from werkzeug.utils import secure_filename
from .main import is_signed_in
import datetime
import sqlite3

manage_entries = Blueprint("manage_entries", __name__, static_folder="static", template_folder="templates")

@manage_entries.route("/wiki/create", methods=["GET", "POST"])
def create_entry():
    title = "Create a Page"

    user = is_signed_in(session, True)

    if user == False:
        return redirect("/login")

    if request.method == "POST":
        database = sqlite3.connect("wiki.db")
        
        with database:
            cursor = database.cursor()

            with open("templates/stub.html", "r") as stub:
                stub = stub.read()

            stub_with_content = stub + "\n\n" + request.form["content"]

            content = ""

            for w in stub_with_content.split(" "):
                if w.startswith("http://") or w.startswith("https://"):
                    content += "<a href=\"" + w + "\">" + w + "</a> "
                else:
                    content += w + " "

            # by default, all entries are private
            cursor.execute("""
                INSERT INTO entries (
                    title,
                    slug,
                    content,
                    folder,
                    is_private,
                    last_modified
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                request.form["title"],
                request.form["slug"],
                content,
                request.form["folder"],
                1,
                datetime.datetime.now().timestamp()
            ))

        flash("/{} was created successfully.".format(request.form["slug"]))

        return redirect("/" + request.form["slug"])

    database = sqlite3.connect("wiki.db")

    with database:
        cursor = database.cursor()

        pages = cursor.execute("SELECT title, slug FROM entries WHERE slug != 'index';").fetchall()

    return render_template("create.html", title=title, slug="/wiki/create", pages=pages)

@manage_entries.route("/<file>/edit", methods=["GET", "POST"])
def edit_entry(file):
    file = secure_filename(file)

    user = is_signed_in(session, True)

    title = "Edit: " + file

    if user == False:
        return redirect("/login")

    database = sqlite3.connect("wiki.db")

    with database:
        cursor = database.cursor()

        entry = cursor.execute("SELECT title, content, folder, slug FROM entries WHERE slug = ?", (file,)).fetchone()

        if entry == None:
            return abort(404)

        pages = cursor.execute("SELECT title, slug FROM entries WHERE slug != 'index';").fetchall()

    if request.method == "POST":
        database = sqlite3.connect("wiki.db")
        
        with database:
            cursor = database.cursor()

            if not request.form["title"] or not request.form["content"] or not request.form["folder"] \
                    or not request.form["slug"] or not request.form["changes_description"]:
                flash("Please fill out all fields.")
                return redirect("/" + file + "/edit")

            content = ""

            for w in request.form["content"].split(" "):
                if w.startswith("http://") or w.startswith("https://"):
                    content += "<a href=\"" + w + "\">" + w + "</a> "
                else:
                    content += w + " "

            cursor.execute("UPDATE entries SET title = ?, content = ?, folder = ?, last_modified = ? WHERE slug = ?", (
                request.form["title"],
                request.form["content"],
                request.form["folder"],
                datetime.datetime.now().timestamp(),
                file
            ))

            last_revision = cursor.execute("SELECT MAX(id) FROM revisions;").fetchone()[0]

            if last_revision == None:
                last_revision = 0

            cursor.execute("INSERT INTO revisions (id, modified_date, modified_by, slug, contents, changes_description) VALUES (?, ?, ?, ?, ?, ?);", (last_revision + 1, datetime.datetime.now().timestamp(), session.get("me"), file, request.form["content"], request.form["changes_description"]))

        flash("/{} was edited successfully.".format(file))

        return redirect("/" + file)

    return render_template("edit.html", file=file, entry=entry, title=title, slug=file, pages=pages)

@manage_entries.route("/<file>/delete", methods=["GET"])
def delete_entry(file):
    file = secure_filename(file)

    user = is_signed_in(session, True)

    if user == False:
        return redirect("/login")

    database = sqlite3.connect("wiki.db")

    with database:
        cursor = database.cursor()

        entry = cursor.execute("SELECT * FROM entries WHERE slug = ?", (file,)).fetchone()

        if entry == None:
            return abort(404)

        cursor.execute("DELETE FROM entries WHERE slug = ?", (file,))

        flash("/{} was deleted successfully.".format(file))

        return redirect("/")