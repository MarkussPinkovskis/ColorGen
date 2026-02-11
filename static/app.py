from flask import Flask, request, redirect, session, render_template_string
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "atslega" 

DB_NAME = "colorgenlogin.db"
render_template = 'login.html'





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
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
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

