import streamlit as st
import re
import json
from google.cloud import firestore
import pandas as pd

# Set the page configuration
st.set_page_config(page_title='Jobs in EU', page_icon="💼", layout='wide', initial_sidebar_state='auto')
# Title of the page
st.title("Handpicked Jobs in Europe")

# Function to extract email addresses from text using regex
def extract_emails(text):
    return re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

# Initialize Firestore client
def initialize_firestore():
    # Load the secrets from the secrets.json file
    secrets = st.secrets["firebase_config"]
    # Initialize Firestore with the service account information
    db = firestore.Client.from_service_account_info(secrets)
    return db

# Function to fetch job data from Firestore
def fetch_job_data(db):
    job_data = []
    collection_ref = db.collection("emeajobs")
    docs = collection_ref.stream()
    for doc in docs:
        doc_data = doc.to_dict()
        job_data.extend(doc_data.get("jobs", []))
    return job_data

# Function to display rows as cards
def display_cards(df):
    num_cols = 4  # Number of cards per row
    num_rows = len(df) // num_cols + (len(df) % num_cols > 0)
    colors = ['#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#34495e', '#f1c40f', '#e67e22', '#e74c3c', '#95a5a6']

    card_style = """
        <style>
            .card {
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
                background-color: #f4f6f7;
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            .card h3 {
                color: white;
            }
            .card p {
                color: #7f8c8d;
            }
            .card .header {
                border-radius: 10px 10px 0 0;
                padding: 10px;
            }
            .card .footer {
                padding: 10px;
                color: #3498db;
            }
            .card a {
                color: #3498db;
                text-decoration: none;
            }
        </style>
    """
    st.markdown(card_style, unsafe_allow_html=True)

    for i in range(num_rows):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            idx = i * num_cols + j
            if idx < len(df):
                with cols[j]:
                    job_link = df.loc[idx, 'Job_Link']
                    contact_info = df.loc[idx, 'contact'] if df.loc[idx, 'contact'] else "No direct contact available"
                    background_color = colors[idx % len(colors)]
                    posted_time_ago = df.loc[idx, 'posted-time-ago']

                    if check_very_old(posted_time_ago):
                        ticker_style = "background-color: #ffcccc; color: #ff3333; border-radius: 20px; padding: 5px 10px;"
                        posted_time_ago = "Very Old"
                    else:
                        ticker_style = ""

                    card_content = f"""
                        <div class="card">
                            <div class="header" style="background-color: {background_color};">
                                <h3>{df.loc[idx, 'job-title']}</h3>
                            </div>
                            <p><b>Company:</b> {df.loc[idx, 'company']}</p>
                            <p><b>Location:</b> {df.loc[idx, 'location']}</p>
                            <p><b>Date Posted:</b> {df.loc[idx, 'posted-time-ago']}</p>
                            <p><b>Job Description:</b> {df.loc[idx, 'Job_txt'][:50]}...</p>
                            <p><b>Contact:</b> {highlight_emails(contact_info)}</p>
                            <div style="{ticker_style}">{posted_time_ago}</div>
                            <a href="{job_link}" target="_blank"><div class="footer"><b>Click here to view the job</b></div></a>
                        </div>
                    """

                    st.markdown(card_content, unsafe_allow_html=True)

# Function to highlight email addresses in the contact field
def highlight_emails(contact_info):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, contact_info)
    highlighted_contact = contact_info
    for email in emails:
        highlighted_contact = highlighted_contact.replace(email, f'<a href="mailto:{email}" style="color: blue;">{email}</a>')
    return highlighted_contact

# Function to display contact card
def display_contact_card():
    st.sidebar.markdown(
        """
        <div style="border: 2px solid #6A0DAD; border-radius: 10px; padding: 10px;">
            <h3 style="color: white; background-color: #6A0DAD; padding: 5px; border-top-left-radius: 10px; border-top-right-radius: 10px; text-align: center;">Contact</h3>
            <div style="padding: 10px;">
                <p style="color: black;"><b>Developer Name:</b> Suresh Parimi</p>
                <p style="color: black;"><b>✉️ E-Mail:</b>sparimi@sparimi.com</p>
                <div style="border: 2px solid #8E44AD; border-radius: 10px; padding: 10px; margin-top: 10px;">
                    <h4 style="color: #6A0DAD;">Connect with me:</h4>
                    <p><a href="https://linkedin.com/in/sparimi" target="_blank" style="color: #6A0DAD; text-decoration: none;">Linkedin</a></p>
                    <p><a href="https://medium.com/@zerofloor" target="_blank" style="color: #6A0DAD; text-decoration: none;">Medium</a></p>
                    <p><a href="https://wa.me/+31616270233" target="_blank" style="color: #6A0DAD; text-decoration: none;">Whatsapp</a></p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Function to check if job was posted "x months ago"
def check_very_old(posted_time):
    if 'month' in posted_time:
        months_ago = int(posted_time.split()[0])
        if months_ago >= 1:
            return
            True
    return False

# Streamlit App main function
def main():
    # Initialize Firestore client
    db = initialize_firestore()

    st.sidebar.header("Filter Jobs")
    job_title = st.sidebar.text_input("Enter Job Title", "").strip()
    location = st.sidebar.text_input("Enter Location", "").strip()
    show_recruiter_email = st.sidebar.checkbox("Show jobs with recruiter email address")

    job_data = fetch_job_data(db)
    df = pd.DataFrame(job_data)

    # Drop rows with missing values and duplicates
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)

    # Extract email addresses and create 'contact' column
    df['contact'] = df['Job_txt'].apply(lambda x: ', '.join(extract_emails(x)))

    # Filter based on recruiter email address
    if show_recruiter_email:
        df = df[df['contact'].apply(lambda x: bool(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', x)))]

    # Rearrange columns and reset index
    df = df[['job-title', 'company', 'contact', 'Job_Link', 'location', 'Job_txt', 'posted-time-ago']]
    df.reset_index(drop=True, inplace=True)

    # Display the contact card in the sidebar
    display_contact_card()
    
    # Display the cards
    display_cards(df)

if __name__ == "__main__":
    main()
