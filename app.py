from flask import Flask, request, redirect, session, render_template, jsonify
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from openai import OpenAI
import os
from dotenv import load_dotenv
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = "atslega"

DB_NAME = "colorgenlogin.db"


def get_db():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


init_db()


@app.route("/")
def home():
    if "user" in session:
        return render_template("home.html", user=session['user'])
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user"] = email
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    email = request.form["email"]
    password = request.form["password"]

    hashed_password = generate_password_hash(password)

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (email, password, created_at) VALUES (?, ?, ?)",
                (email, hashed_password, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
        return render_template("login.html", success="Registration successful! Please login.")
    except sqlite3.IntegrityError:
        return render_template("login.html", error="Email already exists!")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")



@app.route("/color-recomend", methods=["POST"])
def getColorRecomend():
    import json

    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body received"}), 400

    color = data.get("color", "").strip()
    if not color:
        return jsonify({"error": "No color provided"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a color expert. When given a hex color, return exactly 5 colors that pair well with it. "
                        "Respond ONLY with a raw JSON array — no markdown, no explanation. "
                        "Each object must have 'hex' (e.g. '#FF5733') and 'name' (e.g. 'Sunset Orange') fields."
                    )
                },
                {
                    "role": "user",
                    "content": f"Give me 5 colors that pair well with {color}"
                }
            ]
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        colors = json.loads(raw)
        return jsonify({"colors": colors})

    except Exception as e:
        print(f"OpenAI error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)