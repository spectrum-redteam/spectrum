from flask import Flask, request, render_template_string, session, redirect, url_for
import sqlite3
import subprocess
import re
import html

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.before_first_request
def init_db():
    conn = get_db_connection()
    conn.execute('DROP TABLE IF EXISTS users')
    conn.execute('DROP TABLE IF EXISTS comments')
    conn.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute("INSERT INTO users (username, password, email) VALUES ('admin', 'adminpass', 'admin@example.com')")
    conn.execute("INSERT INTO users (username, password, email) VALUES ('testuser', 'testpass', 'test@example.com')")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return "Welcome to the Flask SAAS Dashboard!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # VULNERABLE: string concatenation in SQL query
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        conn = get_db_connection()
        cur = conn.execute(query)
        user = cur.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return f"Login successful! Welcome, {user['username']}."
        else:
            return "Invalid credentials."
    return render_template_string('''
        <form method="post">
            <input type="text" name="username" placeholder="Username"><br>
            <input type="password" name="password" placeholder="Password"><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/ping_exec')
def ping_exec():
    host = request.args.get('host', '')
    # VULNERABLE: shell=True with user input
    cmd = f"ping -c 2 {host}"
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        return f"<pre>{output.decode()}</pre>"
    except subprocess.CalledProcessError as e:
        return f"<pre>Error: {e.output.decode()}</pre>"
    except subprocess.TimeoutExpired:
        return "<pre>Error: Command timed out.</pre>"
    except Exception as e:
        return f"<pre>An unexpected error occurred: {e}</pre>"

@app.route('/webhook_fetch')
def webhook_fetch():
    url = request.args.get('url', '')
    # VULNERABLE: supports file:// protocol
    if url.startswith("file://"):
        path = url[7:]
        try:
            with open(path, 'r') as f:
                return f"<pre>{f.read()}</pre>"
        except FileNotFoundError:
            return "Error: File not found."
        except Exception as e:
            return f"Error reading file: {e}"
    else:
        return "Error: Only file:// protocol supported for this demo."

@app.route('/set_announcement', methods=['POST'])
def set_announcement():
    msg = request.form['message']
    # VULNERABLE: user input passed directly to render_template_string
    template = "<h2>Announcement:</h2>" + msg
    return render_template_string(template)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    # VULNERABLE: no access control check
    conn = get_db_connection()
    cur = conn.execute(f"SELECT * FROM users WHERE id={user_id}")
    user = cur.fetchone()
    conn.close()
    if user:
        comments_cur = conn.execute(f"SELECT * FROM comments WHERE user_id={user_id}")
        comments = comments_cur.fetchall()
        return render_template_string('''
            <h1>Profile for {{ user.username }}</h1>
            <p>Email: {{ user.email }}</p>
            <h2>Comments:</h2>
            {% for comment in comments %}
                <p>{{ comment.text }}</p>
            {% endfor %}
            <form method="post" action="/comment">
                <input type="hidden" name="user_id" value="{{ user.id }}">
                <textarea name="text" placeholder="Add a comment"></textarea><br>
                <input type="submit" value="Add Comment">
            </form>
        ''', user=user, comments=comments)
    return "User not found", 404

@app.route('/comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        return "Please log in to comment", 403
    user_id = request.form['user_id']
    text = request.form['text']
    # VULNERABLE: unsanitised input stored and rendered
    conn = get_db_connection()
    conn.execute(f"INSERT INTO comments (user_id, text) VALUES ({user_id}, '{text}')")
    conn.commit()
    conn.close()
    return redirect(url_for('profile', user_id=user_id))

@app.route('/users')
def user_list():
    search = request.args.get('search', '')
    conn = get_db_connection()
    # VULNERABLE: string interpolation in LIKE clause
    query = f"SELECT id, username, email FROM users WHERE username LIKE '%{search}%'"
    cur = conn.execute(query)
    users = cur.fetchall()
    conn.close()
    return render_template_string('''
        <h1>User List</h1>
        <form method="get">
            <input type="text" name="search" placeholder="Search users" value="{{ search }}">
            <input type="submit" value="Search">
        </form>
        <ul>
            {% for user in users %}
                <li><a href="/profile/{{ user.id }}">{{ user.username }} ({{ user.email }})</a></li>
            {% endfor %}
        </ul>
    ''', users=users, search=search)

if __name__ == '__main__':
    app.run(debug=True)
