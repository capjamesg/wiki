from flask import Flask, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from .config import SECRET_KEY
import sqlite3
import os

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # read config.py file
    app.config.from_pyfile(os.path.join(".", "config.py"), silent=False)

    db.init_app(app)

    app.secret_key = SECRET_KEY

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from .auth.auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    from .revisions import revisions as revisions_blueprint

    app.register_blueprint(revisions_blueprint)

    from .bot_interface import bot_interface as bot_interface_blueprint

    app.register_blueprint(bot_interface_blueprint)

    from .manage_entries import manage_entries as manage_entries_blueprint

    app.register_blueprint(manage_entries_blueprint)

    @app.route("/static/images/<filename>")
    def send_images(filename):
        return send_from_directory("static/images/", filename)

    @app.route("/styles.css")
    def styles():
        return send_from_directory(app.static_folder, "styles.css")

    @app.route("/robots.txt")
    def robots():
        return send_from_directory(app.static_folder, "robots.txt")

    @app.route("/search.xml")
    def opensearch_specification():
        return send_from_directory(app.static_folder, "search.xml")

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(app.static_folder, "favicon.ico")

    @app.errorhandler(403)
    def access_required(e):
        connection = sqlite3.connect("wiki.db")

        with connection:
            cursor = connection.cursor()

            entries = cursor.execute("SELECT title, slug FROM entries WHERE slug != 'index';").fetchall()

        return render_template("404.html", title="Access required", error=403, pages=entries), 403

    @app.errorhandler(404)
    def page_not_found(e):
        connection = sqlite3.connect("wiki.db")

        with connection:
            cursor = connection.cursor()

            entries = cursor.execute("SELECT title, slug  FROM entries;").fetchall()

        return render_template("404.html", title="Page not found", error=404, pages=entries), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        connection = sqlite3.connect("wiki.db")

        with connection:
            cursor = connection.cursor()

            entries = cursor.execute("SELECT title, slug  FROM entries;").fetchall()

        return render_template("404.html", title="Method not allowed", error=405, pages=entries), 405

    @app.errorhandler(500)
    def server_error(e):
        connection = sqlite3.connect("wiki.db")

        with connection:
            cursor = connection.cursor()

            entries = cursor.execute("SELECT title, slug  FROM entries;").fetchall()

        return render_template("404.html", title="Server error", error=500, pages=entries), 500

    return app

create_app()