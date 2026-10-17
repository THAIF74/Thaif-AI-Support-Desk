
import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Thaif AI Support Desk",
    page_icon="🎫",
    layout="wide",
)


def get_api_url():
    try:
        value = st.secrets.get("API_URL", "")
    except Exception:
        value = ""

    return (
        value
        or os.getenv("API_URL", "http://127.0.0.1:8000")
    ).rstrip("/")


API_URL = get_api_url()
TIMEOUT = 10


def api_request(method, path, **kwargs):
    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            timeout=TIMEOUT,
            **kwargs,
        )

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text

            st.error(f"API error ({response.status_code}): {detail}")
            return None

        return response.json()

    except requests.RequestException:
        st.error(
            "Cannot connect to the backend API. "
            "Start api.py locally or configure API_URL for deployment."
        )
        return None


st.title("🎫 Thaif AI Support Desk")
st.caption(
    "A ticket-management web app powered by Python, FastAPI, "
    "Streamlit, and SQLite."
)

with st.sidebar:
    st.subheader("Backend connection")
    st.code(API_URL)
    if st.button("Check backend"):
        health = api_request("GET", "/health")
        if health and health.get("status") == "healthy":
            st.success("Backend connected!")

create_tab, tickets_tab, about_tab = st.tabs(
    ["➕ Create Ticket", "📋 Ticket Dashboard", "ℹ️ About"]
)

with create_tab:
    st.subheader("Submit a support request")

    with st.form("create_ticket_form"):
        subject = st.text_input(
            "Subject",
            placeholder="Example: Refund Delay",
        )
        body = st.text_area(
            "Message",
            placeholder="Describe the customer's issue...",
            height=150,
        )
        submit = st.form_submit_button(
            "Classify and Create Ticket",
            type="primary",
        )

    if submit:
        if not subject.strip() or not body.strip():
            st.warning("Enter both a subject and message.")
        else:
            result = api_request(
                "POST",
                "/tickets",
                json={
                    "subject": subject,
                    "body": body,
                },
            )

            if result:
                st.success(f"Ticket #{result['id']} created!")
                col1, col2, col3 = st.columns(3)
                col1.metric("Category", result["category"])
                col2.metric("Priority", result["priority"])
                col3.metric("Assigned Team", result["team"])
                st.write("**Status:**", result["status"])
                st.write("**Created:**", result["created_at"])

with tickets_tab:
    st.subheader("Support ticket dashboard")

    if st.button("Refresh tickets"):
        st.rerun()

    tickets = api_request("GET", "/tickets")

    if tickets is not None:
        if tickets:
            df = pd.DataFrame(tickets)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tickets", len(df))
            col2.metric("Open Tickets", int((df["status"] == "Open").sum()))
            col3.metric(
                "High Priority",
                int((df["priority"] == "High").sum()),
            )

            status_filter = st.selectbox(
                "Filter by status",
                ["All", "Open", "In Progress", "Resolved"],
            )

            visible = df if status_filter == "All" else df[
                df["status"] == status_filter
            ]

            st.dataframe(
                visible,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "Download ticket report CSV",
                data=visible.to_csv(index=False).encode("utf-8-sig"),
                file_name="support_tickets.csv",
                mime="text/csv",
            )

            st.divider()
            st.subheader("Update ticket status")

            ticket_ids = [int(value) for value in df["id"].tolist()]
            selected_id = st.selectbox("Ticket ID", ticket_ids)
            new_status = st.selectbox(
                "New status",
                ["Open", "In Progress", "Resolved"],
            )

            if st.button("Save status"):
                updated = api_request(
                    "PATCH",
                    f"/tickets/{selected_id}/status",
                    json={"status": new_status},
                )

                if updated:
                    st.success(
                        f"Ticket #{selected_id} updated to "
                        f"{updated['status']}."
                    )
                    st.rerun()
        else:
            st.info("No tickets yet. Create your first ticket.")

with about_tab:
    st.subheader("About this project")

    st.markdown("""
    **Thaif AI Support Desk** demonstrates a web application with
    a frontend, REST API, and persistent local database.

    **Features**
    - Automatic keyword-based email classification
    - Priority and support-team assignment
    - Ticket creation and storage
    - Ticket dashboard and status updates
    - CSV report download
    - FastAPI Swagger documentation

    **Important:** Classification uses simple rules, not a trained AI model.
    The support routing is a demonstration and does not send emails.
    """)
