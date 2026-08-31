# 🎫 IT Ticket Triage

An AI-powered IT helpdesk system that automatically classifies support tickets by category and urgency, with role-based dashboards for employees and IT staff.

**🔗 Live Demo:** [it-ticket-triage.onrender.com](https://it-ticket-triage.onrender.com)

> Note: hosted on a free tier, so the first load may take 30–50 seconds if the app has been idle.

---

## Overview

Manually triaging IT support tickets is slow and inconsistent — the same request can be tagged differently depending on who reads it. This project automates that step: when a ticket is submitted, an LLM reads the title and description, assigns a category and urgency level, and explains its reasoning — visible directly on the dashboard for transparency.

The app supports two roles:

- **Employees** — submit tickets and track only their own submissions
- **IT Staff** — view all tickets across the organization, sorted by urgency, and update ticket status (Open → In Progress → Resolved)

## Features

- 🤖 **AI-powered classification** — every ticket is automatically tagged with a category (Network, Hardware, Software, Account, Other) and urgency (Low, Medium, High), along with a one-sentence explanation of the AI's reasoning
- 🔐 **Role-based authentication** — separate views and permissions for employees vs. IT staff, with securely hashed passwords
- 📊 **Live dashboard** — ticket counts, urgency-based sorting, and color-coded priority badges
- 🗄️ **Persistent cloud database** — PostgreSQL (hosted on Neon), so data survives redeploys and server restarts
- ⚡ **Resilient AI integration** — if the AI call fails or times out, the app falls back to safe defaults instead of crashing

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| AI | Groq API (LLM inference) |
| Database | PostgreSQL (Neon), via `psycopg` |
| Auth | Flask sessions, Werkzeug password hashing |
| Deployment | Render (web service), Gunicorn (production server) |

## How It Works

1. A user submits a ticket with a title and description
2. The description is sent to an LLM with a structured prompt asking for a JSON response: category, urgency, and reasoning
3. The response is validated (invalid categories/urgency values are safely defaulted) and saved to the database alongside the ticket
4. Employees see their own tickets; IT staff see all tickets, sorted with highest urgency first
5. IT staff can update ticket status, which is reflected instantly on refresh

## Running Locally

```bash
# Clone the repo
git clone https://github.com/ilakkiyailakkiya966-a11y/it-ticket-triage.git
cd it-ticket-triage

# Install dependencies
pip install -r requirements.txt

# Create a .env file with:
# GROQ_API_KEY=your-groq-key
# DATABASE_URL=your-postgresql-connection-string

# Create your first IT Staff account
python create_staff_account.py

# Run the app
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

## Future Improvements

- Ticket search and filtering by category/status
- Email notifications when a ticket is resolved
- Analytics dashboard (average resolution time, ticket volume trends)
- Duplicate/similar ticket detection using embeddings
