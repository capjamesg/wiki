from flask import Blueprint, session, redirect
from flask.templating import render_template
from werkzeug.utils import secure_filename
from .main import is_signed_in
import markdown
import difflib
import sqlite3

revisions = Blueprint("revisions", __name__, static_folder="static", template_folder="templates")

@revisions.route("/<file>/revisions")
def revisions_page(file):
    file = secure_filename(file)

    user = is_signed_in(session, True)

    title = file + " Revision History"

    if user == False:
        return redirect("/login")

    database = sqlite3.connect("wiki.db")

    with database:
        cursor = database.cursor()

        revisions = cursor.execute("SELECT * FROM revisions WHERE slug = ?;", (file, )).fetchall()

        pages = cursor.execute("SELECT title, slug FROM entries WHERE slug != 'index';").fetchall()

    return render_template("revisions.html", file=file, revisions=revisions, title=title, pages=pages)

@revisions.route("/<file>/revisions/<revision>")
def see_individual_revision(file, revision):
    file = secure_filename(file)

    user = is_signed_in(session, True)

    if user == False:
        return redirect("/login")

    database = sqlite3.connect("wiki.db")

    with database:
        cursor = database.cursor()

        pages = cursor.execute("SELECT * FROM entries;").fetchall()

        revisions = cursor.execute("SELECT * FROM revisions;").fetchall()

        single_revision = cursor.execute("SELECT contents, id, changes_description FROM revisions WHERE slug = ? AND id = ?;", (file, revision,)).fetchone()

        current_version = cursor.execute("SELECT title, content FROM entries WHERE slug = ?;", (file,)).fetchone()

        diff = difflib.ndiff(
            current_version[1].splitlines(),
            single_revision[0].splitlines()
        )

        diff = list(diff)

        for i in range(len(diff)):
            if "+" in diff[i]:
                diff[i] = "<span class='added'>" + diff[i] + "</span>"
            elif "-" in diff[i]:
                diff[i] = "<span class='removed'>" + diff[i] + "</span>"

            diff[i] = diff[i].strip()

        diff = "<br>".join(diff)

        pages = cursor.execute("SELECT title, slug FROM entries WHERE slug != 'index';").fetchall()

    title = file + " (Revision #" + str(single_revision[1]) + ")"

    return render_template(
        "single_revision.html",
        content=markdown.markdown(single_revision[0]),
        title=title,
        pages=pages,
        diff=diff,
        revision_id=single_revision[1],
        revisions=revisions,
        is_wiki_entry=True,
        slug=file,
        changes_description=single_revision[2]
    )