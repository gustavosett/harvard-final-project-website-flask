from functools import wraps

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
import time


#config application
app = Flask(__name__)

# auto-reload
app.config["TEMPLATES_AUTO_RELOAD"] = True

#filesystem
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#database
db = SQL("sqlite:///users.db")

@app.after_request
def after_request(resp):
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Expires"] = 0
    resp.headers["Pragma"] = "no-cache"
    return resp


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out!")
    return render_template("login.html")


def my_apology(message, code=400):
    #thats my own apology
    def escape(s):
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("my_apology.html", top=code, bottom=escape(message)), code


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("login.html")

        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("login.html")

        rows = db.execute("SELECT * FROM users WHERE name = ?", request.form.get("username"))

        if len(rows) != 1 or rows[0]["password"] != request.form.get("password"):
            flash("Invalid username and/or password")
            return render_template("login.html")

        session["user_id"] = rows[0]["id"]
        flash("Logged!")

        return redirect("/")
    return render_template("login.html")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    id = session["user_id"]
    if request.method == "POST":
        pomodoro = db.execute("SELECT * FROM settings WHERE users_id = ?", id)
        tasks = db.execute("SELECT task, id FROM tasks WHERE users_id = ?", id)
        last_task = db.execute("SELECT task FROM last_task WHERE users_id = ?", id)
        try:
            task = request.form.get("new_task")
        except:
            task = ""
        if task != "":
            if task != last_task[0]["task"]:
                    db.execute("INSERT INTO tasks (task, users_id) VALUES (?, ?)", task, id)
                    db.execute("UPDATE last_task SET task = ? WHERE users_id = ?", task, id)
                    task = ""
            elif task != "":
                flash("Your last task registered has the same name.")
        elif task == "":
            flash("Must provide task")
            return redirect("/")
        tasks = db.execute("SELECT task, id FROM tasks WHERE users_id = ?", id)
        return redirect("/")
    else:
        pomodoro = db.execute("SELECT * FROM settings WHERE users_id = ?", id)
        tasks = db.execute("SELECT task, id FROM tasks WHERE users_id = ?", id)
        return render_template("index.html", pomodoro_brk=pomodoro[0]["time"], short_brk=pomodoro[0]["short"], long_brk=pomodoro[0]["long"], tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("register.html")
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("register.html")
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Wrong password")
            return render_template("register.html")

        rows = db.execute("SELECT * FROM users WHERE name = ?", request.form.get("username"))

        if len(rows) != 0:
            flash("Username already used")
            return render_template("register.html")

        user = db.execute("INSERT INTO users (name, password) VALUES (?, ?)", request.form.get("username"), request.form.get("password"))

        # user = db.execute("SELECT id FROM users where username = ?", request.form.get("username"))

        session["user_id"] = user

        db.execute("INSERT INTO settings (users_id) values (?)", session["user_id"])
        db.execute("INSERT INTO last_task (task, users_id) values ('', ?)", session["user_id"])
        flash("Registered!")

        return redirect("/")
    return render_template("register.html")

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    pomodoro = db.execute("SELECT * FROM settings WHERE users_id = ?", session["user_id"])
    if request.method == "POST":
        try:
            time = int(request.form.get("pomodoro"))
            short = int(request.form.get("short"))
            long = int(request.form.get("long"))
        except:
            flash("invalid values")
            return redirect("/settings")

        time_db = pomodoro[0]["time"]
        short_db = pomodoro[0]["short"]
        long_db = pomodoro[0]["long"]

        if time == time_db and short == short_db and long ==  long_db:
            flash("same settings")
            return redirect("/")

        if time <= 0 or short <= 0 or long <= 0:
            flash("invalid value")
            return redirect("/settings")

        db.execute("UPDATE settings SET time = ?, short = ?, long = ? WHERE users_id = ?", time, short, long, session["user_id"])

        flash("settings updated!")

        return redirect("/")
    return render_template("settings.html", time=pomodoro[0]["time"], short=pomodoro[0]["short"], long=pomodoro[0]["long"])

def slow():
    time.sleep(6)

@app.route('/getmethod/<id>')
def get_javascript_data(id):
    db.execute("DELETE FROM tasks WHERE id = ? AND users_id = ?", int(id), session["user_id"])
    flash("deleted")
    return id
