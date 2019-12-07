from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from flask_mysqldb import MySQL
from functools import wraps
from datetime import date
import requests

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'da_assignment'
mysql = MySQL(app)


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-re-validate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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
    return redirect("/")


@app.route('/')
def index():
    return render_template("home.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    cur = mysql.connection.cursor()
    l = request.form.get("login")
    id = request.form.get("id")
    p = request.form.get("pass")
    if l == 's':
        cur.execute("SELECT pass, name FROM student WHERE usn = %s", (id,))
    elif l == 't':
        cur.execute("SELECT pass, name FROM teacher WHERE tid = %s", (id,))
    rs = cur.fetchall()
    cur.close()
    if len(rs) == 0 or rs[0][0] != p:
        flash("Invalid Credentials")
        return render_template("error.html")
    flash(rs[0][1])
    if l == 's':
        return render_template("student.html")
    return render_template("teacher.html")


@app.route('/redirect_create')
def redirect_create():
    return render_template("create.html")


@app.route('/create', methods=['GET', 'POST'])
def create():
    cur = mysql.connection.cursor()
    aid = request.form.get("aid")
    tid = request.form.get("tid")
    ques = request.form.get("ques")
    sin = request.form.get("sin")
    sout = request.form.get("sout")
    date = request.form.get("date")
    cur.execute("INSERT INTO question VALUES (%s, %s, %s, %s, %s, %s)", (aid, tid, ques, sin, sout, date))
    mysql.connection.commit()
    cur.close()
    return message("Question added and is available for the students to solve")


@app.route('/aslist')
def aslist():
    cur = mysql.connection.cursor()
    cur.execute("SELECT aid, ques, sin, sout, date FROM question")
    data = cur.fetchall()
    return render_template("assign.html", data=data)


@app.route('/solve_ques')
def solve_ques():
    return render_template("solve.html")


@app.route('/code', methods=['GET', 'POST'])
def code():
    cur = mysql.connection.cursor();
    aid = request.form.get("aid")
    sid = request.form.get("sid")
    code = request.form.get("code")
    d = date.today()
    cur.execute("INSERT INTO solution VALUES (%s, %s, %s, %s)", (aid, sid, code, d))
    mysql.connection.commit()
    cur.close()
    return message("Submitted Successfully")


@app.route('/evaluate')
def evaluate():
    cur = mysql.connection.cursor()
    cur.execute("SELECT aid, usn, code FROM solution")
    data = cur.fetchall()
    for row in data:
        aid = row[0]
        usn = row[1]
        code = row[2]
        lang = 'python'
        cur.execute("SELECT sin, sout FROM question WHERE aid=%s", (aid, ))
        sample = cur.fetchall()
        sin = sample[0][0]
        sout = int(sample[0][1])
        m = 0
        url = "https://ide.geeksforgeeks.org/main.php"
        data1 = {
            'lang': lang,
            'code': code,
            'input': sin,
            'save': True
        }
        r = requests.post(url, data=data1)
        s = r.json()
        print(code)
        print(s)
        print(s['output'])
        if sout == int(s['output']):
            m = 10
        cur.execute("SELECT total FROM student WHERE usn = %s", (usn, ))
        t = cur.fetchall()
        total = int(t[0][0])
        total = total + m
        cur.execute("UPDATE student SET marks = %s, total = %s WHERE usn = %s", (str(m), str(total), usn, ))
    cur.execute("SELECT usn, marks, total FROM student")
    data = cur.fetchall()
    cur.close()
    return render_template("marks.html", data=data)


@app.route('/classmarks')
def classmarks():
    cur = mysql.connection.cursor()
    cur.execute("SELECT usn, marks, total FROM student")
    data = cur.fetchall()
    cur.close()
    return render_template("marks.html", data=data)


@app.route('/marks')
def marks():
    cur = mysql.connection.cursor()
    cur.execute("SELECT usn, marks, total FROM student")
    data = cur.fetchall()
    cur.close()
    return render_template("marks.html", data=data)


def message(msg):
    flash(msg)
    return render_template("message.html")


if __name__ == '__main__':
    app.run()
