
# Thaif AI Support Desk 🎫

A support ticket web application built with Streamlit, FastAPI, and SQLite.

## Features

- Classifies customer messages into three categories
- Assigns priority and support teams
- Creates and stores support tickets
- Displays a ticket dashboard
- Updates ticket status
- Exports ticket reports as CSV
- Provides REST API documentation through Swagger UI

## Technology Stack

- Python
- Streamlit
- FastAPI
- SQLite
- Pandas
- Requests

## Run Locally

Install dependencies:

`pip install -r requirements.txt`

In one terminal, start the backend:

`pip install -r requirements-api.txt`

`uvicorn api:app --reload`

In a second terminal, start the frontend:

`python -m streamlit run app.py`

Open the Streamlit URL shown in the terminal.

## API Endpoints

- `GET /health` — health check
- `POST /tickets` — create a ticket
- `GET /tickets` — list tickets
- `PATCH /tickets/{ticket_id}/status` — update ticket status

Open `/docs` on the backend URL to explore the API.

## Limitations

Classification is keyword-based. The local SQLite database is intended for demonstration; persistent storage must be configured for production deployment.

## Security

Do not commit API keys, environment secrets, or database files.

## Project Status

Local demonstration application with separate frontend and backend.
