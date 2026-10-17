
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = Path(os.getenv("TICKET_DB_PATH", "tickets.db"))

CATEGORIES = {
    "Urgent / Angry": ("High", "Priority Support"),
    "Account Issue": ("Medium", "Account Support"),
    "Standard Query": ("Normal", "General Support"),
}


def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                team TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_db()
    yield


app = FastAPI(
    title="Thaif AI Support Desk API",
    description="API for classifying and managing support tickets.",
    version="1.0.0",
    lifespan=lifespan,
)


class TicketInput(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)


class StatusInput(BaseModel):
    status: str


def classify(subject: str, body: str):
    text = f"{subject} {body}".lower()

    urgent_words = [
        "furious", "angry", "unacceptable", "complaint",
        "urgent", "immediately", "terrible", "frustrated",
        "delayed", "scam", "disappointed", "not working",
    ]
    account_words = [
        "password", "login", "log in", "account",
        "locked", "reset", "sign in", "verification",
        "username", "access denied",
    ]

    if any(word in text for word in urgent_words):
        category = "Urgent / Angry"
        reason = "Urgency or dissatisfaction keywords were detected."
    elif any(word in text for word in account_words):
        category = "Account Issue"
        reason = "Account access or account-management keywords were detected."
    else:
        category = "Standard Query"
        reason = "No urgency or account keywords were detected."

    priority, team = CATEGORIES[category]

    return {
        "category": category,
        "priority": priority,
        "team": team,
        "reason": reason,
    }


def ticket_dict(row):
    return dict(row)


@app.get("/")
def root():
    return {
        "name": "Thaif AI Support Desk API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/tickets", status_code=201)
def create_ticket(ticket: TicketInput):
    subject = ticket.subject.strip()
    body = ticket.body.strip()

    if not subject or not body:
        raise HTTPException(
            status_code=422,
            detail="Subject and body cannot be blank.",
        )

    result = classify(subject, body)

    with connect_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tickets
                (subject, body, category, priority, team)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                subject,
                body,
                result["category"],
                result["priority"],
                result["team"],
            ),
        )
        row = conn.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return {**ticket_dict(row), "reason": result["reason"]}


@app.get("/tickets")
def list_tickets():
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY id DESC"
        ).fetchall()

    return [ticket_dict(row) for row in rows]


@app.patch("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: int, update: StatusInput):
    allowed = {"Open", "In Progress", "Resolved"}

    if update.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {', '.join(sorted(allowed))}",
        )

    with connect_db() as conn:
        cursor = conn.execute(
            "UPDATE tickets SET status = ? WHERE id = ?",
            (update.status, ticket_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ticket not found.")

        row = conn.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

    return ticket_dict(row)
