# VULNERABLE APPLICATION SOURCE MAP (lab.py / lab_vuln.py)

## FILE OVERVIEW
The target application is a Flask SAAS dashboard with multiple critical vulnerabilities.
The file is named `lab.py` (or `lab_vuln.py`).
When patching, overwrite the SAME file – fix ONLY the exploited vulnerability, leave everything else identical.

---

## ENDPOINT 1: /login (SQL Injection)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # VULNERABLE: string concatenation in SQL query
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cur = db.execute(query)

**FIX** – parameterised query:
query = "SELECT * FROM users WHERE username=? AND password=?"
cur = db.execute(query, (username, password))

---

## ENDPOINT 2: /ping_exec (Command Injection)

@app.route('/ping_exec')
def ping_exec():
    host = request.args.get('host', '')
    # VULNERABLE: shell=True with user input
    cmd = f"ping -c 2 {host}"
    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)

**FIX** – remove shell=True and use a list:
cmd = ["ping", "-c", "2", host]
output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=5)

---

## ENDPOINT 3: /webhook_fetch (SSRF/LFI)

@app.route('/webhook_fetch')
def webhook_fetch():
    url = request.args.get('url', '')
    # VULNERABLE: supports file:// protocol
    if url.startswith("file://"):
        path = url[7:]
        with open(path, 'r') as f:
            return f"<pre>{f.read()}</pre>"

**FIX** – block dangerous protocols and internal IPs:
if url.startswith("file://") or url.startswith("file:"):
    return "Error: File protocol not allowed"
if re.match(r'https?://(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])|0\.0\.0\.0|localhost)', url):
    return "Error: Internal addresses not allowed"

---

## ENDPOINT 4: /set_announcement (SSTI)

@app.route('/set_announcement', methods=['POST'])
def set_announcement():
    msg = request.form['message']
    # VULNERABLE: user input passed directly to render_template_string
    template = "<h2>Announcement:</h2>" + msg
    return render_template_string(template)

**FIX** – sanitise template injection characters:
safe_msg = msg.replace('{{', '').replace('}}', '').replace('{%', '').replace('%}', '')
return f"<h2>Announcement:</h2>{safe_msg}"

---

## ENDPOINT 5: /profile/<id> and /comment (IDOR + Stored XSS)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    # VULNERABLE: no access control check
    cur = db.execute(f"SELECT * FROM users WHERE id={user_id}")

@app.route('/comment', methods=['POST'])
def add_comment():
    user_id = request.form['user_id']
    text = request.form['text']
    # VULNERABLE: unsanitised input stored and rendered
    db.execute(f"INSERT INTO comments (user_id, text) VALUES ({user_id}, '{text}')")

**FIX** – session check for IDOR, escape HTML for XSS:
# IDOR
if 'user_id' not in session or session['user_id'] != user_id:
    return "Access denied", 403

# XSS
import html
safe_text = html.escape(text)

---

## ENDPOINT 6: /users (SQLi in search)

@app.route('/users')
def user_list():
    search = request.args.get('search', '')
    # VULNERABLE: string interpolation in LIKE clause
    query = f"SELECT id, username, email FROM users WHERE username LIKE '%{search}%'"

**FIX** – parameterised query:
query = "SELECT id, username, email FROM users WHERE username LIKE ?"
cur = db.execute(query, (f'%{search}%',))

---

## RESTART COMMAND (after any patch)
kill -9 <PID> && rm -f server.log && nohup python3 lab.py > server.log 2>&1 &

Then get new PID:
lsof -i :<PORT> -t