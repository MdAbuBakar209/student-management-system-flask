import sqlite3
from flask import Flask, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "mysecretkey"


# =========================
# Initialize Database
# =========================

def init_db():

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    # Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            course TEXT,
            UNIQUE(name, age, course)
        )
    """)

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# Home Page
# =========================

@app.route("/")
def home():

    # Protect Route
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    query = request.args.get("q", "")

    # Search Student
    if query:

        cursor.execute(
            "SELECT * FROM students WHERE LOWER(name) LIKE ? ORDER BY id DESC",
            ('%' + query.lower() + '%',)
        )

    else:

        cursor.execute(
            "SELECT * FROM students ORDER BY id DESC"
        )

    students = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        students=students,
        query=query,
        count=len(students),
        user=session['user']
    )


# =========================
# Add Student
# =========================

@app.route("/add", methods=["GET", "POST"])
def add():

    # Protect Route
    if 'user' not in session:
        return redirect('/login')

    if request.method == "POST":

        name = request.form["name"].strip()
        age = request.form["age"]
        course = request.form["course"].strip()

        # Validation
        if not name or not age or not course:

            flash("All fields are required!", "danger")

            return redirect("/add")

        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()

        # Duplicate Check
        cursor.execute(
            """
            SELECT id FROM students
            WHERE LOWER(name)=LOWER(?)
            AND age=?
            AND LOWER(course)=LOWER(?)
            """,
            (name, age, course)
        )

        existing = cursor.fetchone()

        if existing:

            flash(
                f"Student already exists at ID: {existing[0]}",
                "warning"
            )

            conn.close()

            return redirect("/add")

        # Insert Student
        cursor.execute(
            """
            INSERT INTO students (name, age, course)
            VALUES (?, ?, ?)
            """,
            (name, age, course)
        )

        conn.commit()
        conn.close()

        flash("Student added successfully!", "success")

        return redirect("/")

    return render_template("add.html")

# =========================
# Edit Student
# =========================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    # Protect Route
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    if request.method == "POST":

        name = request.form["name"].strip()
        age = request.form["age"].strip()
        course = request.form["course"].strip()

        # Validation
        if not name or not age or not course:

            flash("All fields are required!", "danger")

            return redirect(f"/edit/{id}")

        if not age.isdigit():

            flash("Age must be a number!", "danger")

            return redirect(f"/edit/{id}")

        # Update Student
        cursor.execute(
            """
            UPDATE students
            SET name=?, age=?, course=?
            WHERE id=?
            """,
            (name, int(age), course, id)
        )

        conn.commit()
        conn.close()

        flash("Student updated successfully!", "info")

        return redirect("/")

    # Fetch Existing Student
    cursor.execute(
        "SELECT * FROM students WHERE id=?",
        (id,)
    )

    student = cursor.fetchone()

    conn.close()

    return render_template(
        "edit.html",
        student=student
    )


# =========================
# Delete Student
# =========================

@app.route("/delete/<int:id>")
def delete(id):

    # Protect Route
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Student deleted successfully!", "warning")

    return redirect("/")


# =========================
# Register
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        # Validation
        if not username or not email or not password:

            flash("All fields are required!", "danger")

            return redirect('/register')

        # Hash Password
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users(username, email, password)
                VALUES (?, ?, ?)
                """,
                (username, email, hashed_password)
            )

            conn.commit()

            flash(
                "Registration successful! Please login.",
                "success"
            )

            return redirect('/login')

        except:

            flash(
                "Username or Email already exists!",
                "warning"
            )

        conn.close()

    return render_template('register.html')


# =========================
# Login
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username'].strip()
        password = request.form['password']

        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        # Check Password
        if user and check_password_hash(user[3], password):

            session['user'] = username

            flash("Login successful!", "success")

            return redirect('/')

        else:

            flash(
                "Invalid username or password!",
                "danger"
            )

    return render_template('login.html')


# =========================
# Logout
# =========================

@app.route('/logout')
def logout():

    session.pop('user', None)

    flash("Logged out successfully!", "info")

    return redirect('/login')


# =========================
# Run App
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)