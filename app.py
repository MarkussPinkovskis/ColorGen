from flask import Flask, request, redirect, session, render_template, jsonify
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = "atslega"

DB_NAME = "colorgenlogin.db"

IS_POSTGRES = bool(DATABASE_URL)


def get_db():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn


def db_execute(conn, sql, params=()):
    """Unified execute that handles both sqlite3 and psycopg2."""
    if IS_POSTGRES:
        sql = sql.replace("?", "%s")
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        return cur
    else:
        return conn.execute(sql, params)


def init_db():
    if IS_POSTGRES:
        create_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """
    else:
        create_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """
    conn = get_db()
    cur = db_execute(conn, create_sql)
    conn.commit()
    conn.close()


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

        conn = get_db()
        cur = db_execute(conn, "SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

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
        conn = get_db()
        db_execute(
            conn,
            "INSERT INTO users (email, password, created_at) VALUES (?, ?, ?)",
            (email, hashed_password, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return render_template("login.html", success="Registration successful! Please login.")
    except (sqlite3.IntegrityError, psycopg2.errors.UniqueViolation):
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
                        "You are a color expert. When given a hex color, return exactly 4 colors that pair well with it. "
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
    
@app.route("/color-random", methods=["POST"])
def getColorrandom():
    import json

    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a color expert. Return a random color and 4 colors that pair well with it. "
                        "Respond ONLY with a raw JSON object — no markdown, no explanation. "
                        "The object must have 'primary' (with 'hex' and 'name') and 'colors' (array of 4 objects each with 'hex' and 'name')."
                    )
                },
                {
                    "role": "user",
                    "content": "Give me a random color (it can be any unique color also) with 4 colors that pair well with it"
                }
            ]
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
        return jsonify({"primary": result["primary"], "colors": result["colors"]})

    except Exception as e:
        print(f"OpenAI error: {e}")
        return jsonify({"error": str(e)}), 500
    

if __name__ == "__main__":
    app.run(debug=True)