from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
from flask_mail import Mail, Message

# ================= FLASK APP =================
app = Flask(__name__)
app.secret_key = "ucms_secret"

# ================= MAIL CONFIG =================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

# YOUR GMAIL
app.config['MAIL_USERNAME'] = 'ucms@gmail.com'

# YOUR APP PASSWORD
app.config['MAIL_PASSWORD'] = 'pgyn dgcl gwpp dshx'

mail = Mail(app)

# ================= OPENAI =================
client = OpenAI(
    api_key="YOUR_OPENAI_API_KEY"
)

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
UPDATE users
SET email='yourgmail@gmail.com'
WHERE username='yourusername'
""")

conn.commit()
conn.close()

print("Email updated")



# ================= OPENAI CONFIG =================
client = OpenAI(
    api_key="api key"
)

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")


# ================= AI FUNCTION =================
def analyze_complaint(text):

    prompt = f"""
    You are an AI complaint classifier for a university complaint system.

    Analyze the complaint and return ONLY:

    Department: <department>
    Priority: <High/Medium/Low>

    Allowed Departments:
    - IT Department
    - Exam Department
    - Hostel Department
    - Accounts Department
    - Student Affairs
    - Security Department
    - General

    Complaint:
    {text}
    """

    try:

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You classify university complaints safely and professionally."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        result = response.choices[0].message.content.strip()

        print("AI RESULT:", result)

        department = "General"
        priority = "Medium"

        for line in result.split("\n"):

            if line.startswith("Department:"):
                department = line.replace(
                    "Department:",
                    ""
                ).strip()

            elif line.startswith("Priority:"):
                priority = line.replace(
                    "Priority:",
                    ""
                ).strip()

        return department, priority

    except Exception as e:

        print("OPENAI ERROR:", e)

        return "General", "Medium"


# ================= LOGIN =================
# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cur.fetchone()

        conn.close()

        # user[3] = password
        # user[4] = role

        if user and check_password_hash(user[3], password):

            session["user"] = user[1]
            session["role"] = user[4]

            if user[4] == "admin":
                return redirect("/admin")

            elif user[4] == "staff":
                return redirect("/staff")

            else:
                return redirect("/dashboard")

    return render_template("login.html")

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]

        password = generate_password_hash(
            request.form["password"]
        )

        role = request.form["role"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
    INSERT INTO users
    (username, email, password, role)

    VALUES (?, ?, ?, ?)
""", (
    username,
    email,
    password,
    role
))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ================= COMPLAINT =================
# ================= COMPLAINT =================
@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    username = session.get("user")

    if not username:
        return redirect("/login")

    if request.method == "POST":

        try:

            title = request.form["title"]
            description = request.form["description"]

            full_text = title + " " + description

            # AI ANALYSIS
            department, priority = analyze_complaint(
                full_text
            )

            category = "General"

            conn = sqlite3.connect("database.db")
            cur = conn.cursor()

            # INSERT COMPLAINT
            cur.execute("""
                INSERT INTO complaints
                (
                    username,
                    title,
                    description,
                    category,
                    priority,
                    department
                )

                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                username,
                title,
                description,
                category,
                priority,
                department
            ))

            conn.commit()

            # ================= ADMIN EMAIL =================

            cur.execute("""
                SELECT email
                FROM users
                WHERE role='admin'
            """)

            admins = cur.fetchall()

            admin_emails = []

            for admin in admins:
                admin_emails.append(admin[0])

            if admin_emails:

                admin_msg = Message(
                    "New Complaint Submitted - UCMS",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=admin_emails
                )

                admin_msg.body = f"""
A new complaint has been submitted.

Student:
{username}

Title:
{title}

Department:
{department}

Priority:
{priority}
"""

                mail.send(admin_msg)

            # ================= STUDENT EMAIL =================

            cur.execute(
                "SELECT email FROM users WHERE username=?",
                (username,)
            )

            data = cur.fetchone()

            if data:

                user_email = data[0]

                student_msg = Message(
                    "Complaint Submitted - UCMS",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[user_email]
                )

                student_msg.body = f"""
Your complaint has been submitted successfully.

Title:
{title}

Department:
{department}

Priority:
{priority}

Status:
Pending
"""

                mail.send(student_msg)

            conn.close()

            return redirect("/dashboard")

        except Exception as e:

            print("ERROR:", e)

            return "Internal Server Error"

    return render_template("complaint.html")






# ================= STUDENT DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    if session.get("role") != "student":
        return redirect("/login")

    username = session.get("user")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM complaints
        WHERE username=?
        ORDER BY id ASC
    """, (username,))

    complaints = cur.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        complaints=complaints
    )


# ================= ADMIN DASHBOARD =================
@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        return redirect("/login")

    search = request.args.get("search")
    status = request.args.get("status")
    priority = request.args.get("priority")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # STAFF USERS
    cur.execute("""
        SELECT username
        FROM users
        WHERE role='staff'
    """)

    staff_users = cur.fetchall()

    query = """
        SELECT
            id,
            username,
            title,
            department,
            priority,
            status,
            created_at,
            assigned_staff

        FROM complaints

        WHERE 1=1
    """

    params = []

    # SEARCH
    if search:

        query += """
            AND (
                title LIKE ?
                OR username LIKE ?
                OR department LIKE ?
            )
        """

        search_term = f"%{search}%"

        params.extend([
            search_term,
            search_term,
            search_term
        ])

    # STATUS FILTER
    if status:

        query += " AND status=? "

        params.append(status)

    # PRIORITY FILTER
    if priority:

        query += " AND priority=? "

        params.append(priority)

    query += " ORDER BY id ASC"

    cur.execute(query, params)

    complaints = cur.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        complaints=complaints,
        staff_users=staff_users
    )





# ================= ASSIGN STAFF =================
@app.route("/assign/<int:id>", methods=["POST"])
def assign_staff(id):

    if session.get("role") != "admin":
        return redirect("/login")

    staff = request.form["staff"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # UPDATE STAFF
    cur.execute("""
        UPDATE complaints
        SET assigned_staff=?
        WHERE id=?
    """, (staff, id))

    conn.commit()

    # ================= STAFF EMAIL =================

    cur.execute(
        "SELECT email FROM users WHERE username=?",
        (staff,)
    )

    data = cur.fetchone()

    if data:

        staff_email = data[0]

        msg = Message(
            "New Complaint Assigned - UCMS",
            sender=app.config['MAIL_USERNAME'],
            recipients=[staff_email]
        )

        msg.body = f"""
A new complaint has been assigned to you.

Complaint ID: {id}

Please login to UCMS dashboard.
"""

        mail.send(msg)

    conn.close()

    return redirect("/admin")


# ================= STAFF DASHBOARD =================
@app.route("/staff")
def staff():

    if session.get("role") != "staff":
        return redirect("/login")

    username = session.get("user")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            title,
            department,
            priority,
            status,
            assigned_staff

        FROM complaints

        WHERE assigned_staff=?

        ORDER BY id ASC
    """, (username,))

    complaints = cur.fetchall()

    conn.close()

    return render_template(
        "staff.html",
        complaints=complaints
    )


# ================= UPDATE STATUS =================
@app.route("/update_status/<int:cid>/<status>")
def update_status(cid, status):

    if session.get("role") not in ["admin", "staff"]:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # UPDATE STATUS
    cur.execute("""
        UPDATE complaints
        SET status=?
        WHERE id=?
    """, (status, cid))

    conn.commit()

    # ================= USER EMAIL =================

    cur.execute("""
        SELECT users.email, complaints.title
        FROM complaints
        JOIN users
        ON complaints.username = users.username
        WHERE complaints.id=?
    """, (cid,))

    data = cur.fetchone()

    if data:

        user_email = data[0]
        complaint_title = data[1]

        msg = Message(
            "Complaint Status Updated - UCMS",
            sender=app.config['MAIL_USERNAME'],
            recipients=[user_email]
        )

        msg.body = f"""
Your complaint status has been updated.

Complaint:
{complaint_title}

New Status:
{status}
"""

        mail.send(msg)

    conn.close()

    # RETURN BASED ON ROLE
    if session.get("role") == "staff":
        return redirect("/staff")

    return redirect("/admin")





# ================= VIEW COMPLAINT =================
@app.route("/view_complaint/<int:id>")
def view_complaint(id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            username,
            title,
            description,
            department,
            priority,
            status,
            assigned_staff,
            created_at
        FROM complaints
        WHERE id=?
    """, (id,))

    complaint = cur.fetchone()

    conn.close()

    return render_template(
        "view_complaint.html",
        complaint=complaint
    )





# ================= ANALYTICS =================
@app.route("/analytics")
def analytics():

    if session.get("role") != "admin":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # TOTAL
    cur.execute("SELECT COUNT(*) FROM complaints")
    total = cur.fetchone()[0]

    # STATUS COUNTS
    cur.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE status='Pending'
    """)
    pending = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE status='In Progress'
    """)
    in_progress = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE status='Resolved'
    """)
    resolved = cur.fetchone()[0]

    # PRIORITY COUNTS
    cur.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE priority='High'
    """)
    high = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE priority='Medium'
    """)
    medium = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE priority='Low'
    """)
    low = cur.fetchone()[0]

    conn.close()

    return render_template(
        "analytics.html",
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        high=high,
        medium=medium,
        low=low
    )


# ================= LOGOUT =================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ================= MAIN =================
if __name__ == "__main__":
    app.run(debug=True)
