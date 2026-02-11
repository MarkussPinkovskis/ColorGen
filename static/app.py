from flask import Flask, render_template_string, request, redirect, session
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "atslega" 

DB_NAME = "colorgenlogin.db"

html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
<h1 class="text-center">Login Page</h1>
  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">

</head>
<body>
    
  <div class="container">
  <h2>Vertical (basic) form</h2>
  <form action="/action_page.php">
    <div class="form-group">
      <label for="email">Email:</label>
      <input type="email" class="form-control" id="email" placeholder="Enter email" name="email" >
    </div>
    <div class="form-group">
      <label for="pwd">Password:</label>
      <input type="password" class="form-control" id="pwd" placeholder="Enter password" name="pwd">
    </div>
    <div class="checkbox">
      <label><input type="checkbox" name="remember"> Remember me</label>
    </div>
    <button type="submit" class="btn btn-default">Submit</button>
  </form>
</div>


</body>
</html>
'''


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()

@app.route("/")
def home():
    if "user" in session:
        return f"Welcome {session['user']}! <br><a href='/logout'>Logout</a>"
    return redirect("login.html")


@app.route("register.html", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users (email, password, created_at) VALUES (?, ?, ?)",
                (email, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            conn.close()
            return "Username already exists!"

    return """
        <h2>Register</h2>
        <form method="POST">
            Email: <input name="email"><br>
            Password: <input name="password" type="password"><br>
            <button type="submit">Register</button>
        </form>
        <a href="/login">Login</a>
    """
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)

