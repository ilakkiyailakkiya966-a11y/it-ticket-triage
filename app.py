from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database import (
    init_db, add_ticket, get_all_tickets, get_stats,
    update_ticket_status, create_user, get_user_by_username
)
from ai_classifier import classify_ticket

app = Flask(__name__)
app.secret_key = "change-this-to-something-random-later"  # needed for sessions to work securely

# Make sure the database and tables exist before the app starts
init_db()


# ---------- Helper: protect pages that need login ----------
def login_required(f):
    """Blocks access to a page unless the user is logged in."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def staff_required(f):
    """Blocks access unless the logged-in user is IT staff."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "it_staff":
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return wrapper


# ---------- Auth routes ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    """Employee self-signup. IT staff accounts are created separately (not public)."""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        password_hash = generate_password_hash(password)
        success = create_user(username, password_hash, role="employee")

        if success:
            flash("Account created! Please log in.")
            return redirect(url_for("login"))
        else:
            flash("That username is already taken.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = get_user_by_username(username)

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- Main app routes ----------
@app.route("/")
@login_required
def home():
    """
    Employees see only their own tickets.
    IT staff see everyone's tickets.
    Supports optional ?search=&category=&status= query params for filtering.
    """
    search = request.args.get("search", "").strip() or None
    category = request.args.get("category", "").strip() or None
    status = request.args.get("status", "").strip() or None

    if session["role"] == "it_staff":
        tickets = get_all_tickets(search=search, category=category, status=status)
        stats = get_stats()
    else:
        tickets = get_all_tickets(user_id=session["user_id"], search=search, category=category, status=status)
        stats = get_stats(user_id=session["user_id"])

    return render_template(
        "index.html", tickets=tickets, stats=stats,
        search=search or "", category=category or "", status=status or ""
    )


@app.route("/new", methods=["GET", "POST"])
@login_required
def new_ticket():
    """Shows the form (GET) or saves the ticket (POST)."""
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        result = classify_ticket(title, description)

        add_ticket(
            title, description,
            submitted_by=session["user_id"],
            category=result["category"],
            urgency=result["urgency"],
            reasoning=result["reasoning"]
        )

        return redirect(url_for("home"))

    return render_template("new_ticket.html")


@app.route("/update-status/<int:ticket_id>", methods=["POST"])
@login_required
@staff_required
def update_status(ticket_id):
    """Only IT staff can change a ticket's status."""
    new_status = request.form["status"]
    update_ticket_status(ticket_id, new_status)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
