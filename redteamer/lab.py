from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import sqlite3
import os
import re
import subprocess
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.secret_key = "super_secret_key_123"  # Weak secret

# ========== ENABLE REQUEST LOGGING ==========
handler = RotatingFileHandler('server.log', maxBytes=100000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
app.logger.addHandler(console_handler)

@app.before_request
def log_request():
    app.logger.info(f"{request.method} {request.path} from {request.remote_addr} - Params: {dict(request.args)} - Form: {dict(request.form)}")

# ========== DATABASE SETUP (in-memory for demo) ==========
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT, role TEXT)")
    c.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin@saas.local', 'admin')")
    c.execute("INSERT INTO users VALUES (2, 'john', 'password', 'john@example.com', 'user')")
    c.execute("INSERT INTO users VALUES (3, 'alice', 'alice!!', 'alice@example.com', 'user')")
    c.execute("CREATE TABLE comments (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT)")
    c.execute("INSERT INTO comments VALUES (1, 2, 'Hello world!')")
    c.execute("CREATE TABLE flag (secret TEXT)")
    c.execute("INSERT INTO flag VALUES ('FLAG{SQLi_Is_Alive_And_Well}')")
    conn.commit()
    return conn

db = init_db()

# ========== VULNERABLE ENDPOINTS ==========

@app.route('/')
def index():
    banner = request.args.get('banner', 'Welcome to SAAS Platform')
    return render_template_string("<h1>{{ banner }}</h1><p>Your one-stop dashboard.</p>", banner=banner)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Vulnerable SQL query (string concatenation)
        query = "SELECT * FROM users WHERE username=? AND password=?"
        cur = db.execute(query, (username, password))
        user = cur.fetchone()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/dashboard')
        else:
            return "Login failed. <a href='/login'>Back</a>"
    return '''
        <form method="POST">
            Username: <input name="username"><br>
            Password: <input name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return f"<h2>Welcome, {session['username']}</h2>" \
           f"<p><a href='/profile/{session['user_id']}'>My Profile</a></p>" \
           f"<p><a href='/users'>User List</a></p>" \
           f"<p><a href='/ping'>Network Tools</a></p>" \
           f"<p><a href='/webhook'>Webhook Tester</a></p>" \
           f"<p><a href='/announcement'>Set Announcement</a></p>"

@app.route('/profile/<int:user_id>')
def profile(user_id):
    cur = db.execute(f"SELECT * FROM users WHERE id={user_id}")
    user = cur.fetchone()
    if not user:
        return "User not found"
    return f"<h1>Profile of {user[1]}</h1>" \
           f"<p>Email: {user[3]}</p>" \
           f"<p>Role: {user[4]}</p>" \
           f"<p>Comments about {user[1]}:</p>" \
           f"<div>{get_comments_html(user_id)}</div>" \
           + "<h3>Add a comment</h3><form method='POST' action='/comment'>" \
             "<input type='hidden' name='user_id' value='{user_id}'>" \
             "<textarea name='text'></textarea><br>" \
             "<input type='submit' value='Post'>" \
             "</form>"

def get_comments_html(user_id):
    cur = db.execute(f"SELECT text FROM comments WHERE user_id={user_id}")
    comments = cur.fetchall()
    html = ""
    for c in comments:
        html += f"<p>{c[0]}</p>"
    return html

@app.route('/comment', methods=['POST'])
def add_comment():
    user_id = request.form['user_id']
    text = request.form['text']
    db.execute(f"INSERT INTO comments (user_id, text) VALUES ({user_id}, '{text}')")
    db.commit()
    return redirect(f'/profile/{user_id}')

@app.route('/users')
def user_list():
    search = request.args.get('search', '')
    if search:
        query = "SELECT id, username, email FROM users WHERE username LIKE ?"
    else:
        query = "SELECT id, username, email FROM users"
    cur = db.execute(query, (username, password))
    users = cur.fetchall()
    out = "<h1>User Directory</h1><form>Search: <input name='search'><input type='submit'></form><ul>"
    for u in users:
        out += f"<li><a href='/profile/{u[0]}'>{u[1]}</a> - {u[2]}</li>"
    out += "</ul>"
    return out

@app.route('/ping')
def ping_form():
    return '''
        <h1>Ping Utility</h1>
        <form action="/ping_exec">
            IP/Host: <input name="host"><br>
            <input type="submit" value="Ping">
        </form>
    '''

@app.route('/ping_exec')
def ping_exec():
    host = request.args.get('host', '')
    if not host:
        return "No host provided"
    cmd = f"ping -c 2 {host}"
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        return f"<pre>{output.decode()}</pre>"
    except Exception as e:
        return f"<pre>Error: {e}</pre>"

@app.route('/webhook')
def webhook_form():
    return '''
        <h1>Webhook Tester</h1>
        <form action="/webhook_fetch">
            URL: <input name="url" size="50"><br>
            <input type="submit" value="Fetch">
        </form>
    '''

@app.route('/webhook_fetch')
def webhook_fetch():
    url = request.args.get('url', '')
    if not url:
        return "No URL"
    if url.startswith("file://"):
        try:
            path = url[7:]
            with open(path, 'r') as f:
                return f"<pre>{f.read()}</pre>"
        except Exception as e:
            return f"Error: {e}"
    else:
        import requests
        try:
            r = requests.get(url, timeout=3)
            return f"<pre>Status: {r.status_code}\n{r.text}</pre>"
        except Exception as e:
            return f"Error: {e}"

@app.route('/announcement')
def announcement_form():
    return '''
        <h1>Set Public Announcement</h1>
        <form method="POST" action="/set_announcement">
            Message: <input name="message"><br>
            <input type="submit" value="Set">
        </form>
    '''

@app.route('/set_announcement', methods=['POST'])
def set_announcement():
    msg = request.form['message']
    template = "<h2>Announcement:</h2>" + msg
    return render_template_string(template)

@app.route('/debug')
def debug_info():
    env = dict(os.environ)
    source_files = {}
    for root, dirs, files in os.walk('.'):
        for f in files:
            if f.endswith('.py'):
                try:
                    source_files[f] = open(os.path.join(root, f)).read()
                except:
                    pass
    return jsonify({"env": str(env), "source": source_files})

if __name__ == '__main__':
    print("[!] HIGHLY VULNERABLE SAAS LAB running on http://127.0.0.1:4999")
    app.run(port=4999, debug=False)