import streamlit as st
import re
import json
from google.cloud import firestore
import pandas as pd

# Function to extract email addresses from text using regex
def extract_emails(text):
    return re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

# Function to check if job description contains visa sponsorship or relocation
def check_visa_relocation(text):
    text = text.lower()
    return 'Yes' if 'visa sponsorship' in text or 'relocation' in text else 'No'

# Initialize Firestore client
def initialize_firestore():
    secrets = st.secrets["firebase_config"]
    db = firestore.Client.from_service_account_info(secrets)
    return db


# Function to fetch job data from Firestore
def fetch_job_data(db):
    job_data = []
    collection_ref = db.collection("linkedinjobs")
    docs = collection_ref.stream()
    for doc in docs:
        doc_data = doc.to_dict()
        job_data.extend(doc_data.get("jobs", []))
    return job_data

# Function to filter DataFrame based on user input
def filter_dataframe(df, job_title, location, visa_relocation_filter):
    if job_title:
        df = df[df['job-title'].str.contains(job_title, case=False)]
    if location:
        df = df[df['location'].str.contains(location, case=False)]
    if visa_relocation_filter:
        df = df[df['Visa/Relocation?'] == 'Yes']
    return df

# Function to display rows as cards
def display_cards(df):
    num_cols = 4  # Number of cards per row
    num_rows = len(df) // num_cols + (len(df) % num_cols > 0)
    colors = ['#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#34495e', '#f1c40f', '#e67e22', '#e74c3c', '#95a5a6']

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

                    if df.loc[idx, 'Visa/Relocation?'] == 'Yes':
                        visa_relocation_style = f"background-color: #2ecc71; color: white; border-radius: 20px; padding: 5px 10px;"
                    else:
                        visa_relocation_style = ""

                    card_content = f"""
                        <div style="border: 2px solid #3498db; border-radius: 10px; padding: 20px; margin: 10px; background-color: #f4f6f7;">
                            <div style="background-color: {background_color}; border-radius: 10px 10px 0 0; padding: 10px;">
                                <h3 style="color: white;">{df.loc[idx, 'job-title']}</h3>
                            </div>
                            <p style="color: #7f8c8d;"><b>Company:</b> {df.loc[idx, 'company']}</p>
                            <p style="color: #7f8c8d;"><b>Location:</b> {df.loc[idx, 'location']}</p>
                            <p style="color: #7f8c8d;"><b>Date Posted:</b> {df.loc[idx, 'posted-time-ago']}</p>
                            <p style="color: #7f8c8d;"><b>Job Description:</b> {df.loc[idx, 'Job_txt'][:100]}...</p>
                            <p style="color: #7f8c8d;"><b>Contact:</b> {highlight_emails(contact_info)}</p>
                            <p style="color: #7f8c8d;"><b>Visa/Relocation:</b> <span style="{visa_relocation_style}">{df.loc[idx, 'Visa/Relocation?']}</span></p>
                            <div style="{ticker_style}">{posted_time_ago}</div>
                            <a href="{job_link}" target="_blank" style="text-decoration: none;">
                                <div style="padding: 10px; color: #3498db;"><b>Click here to view the job</b></div>
                            </a>
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
                <div style="border: 2px solid #8E44AD; border-radius: 10px; padding: 10px; margin-top: 10px;">
                    <h4 style="color: #6A0DAD;">Connect with me:</h4>
                    <p><a href="https://linkedin.com/in/sparimi" target="_blank" style="color: #6A0DAD; text-decoration: none;">Linkedin</a></p>
                    <p><a href="https://medium.com/@zerofloor" target="_blank" style="color: #6A0DAD; text-decoration: none;">Medium</a></p>
                    <p><a href="https://wa.me/+31616270233" target="_blank" style="color: #6A0DAD; text-decoration: none;">Whatsapp</a></p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Function to display insights card
def display_insights_card(total_jobs, visa_relocation_jobs):
    st.sidebar.markdown(
        f"""
        <div style="border: 2px solid #6A0DAD; border-radius: 10px; padding: 10px;">
            <h3 style="color: white; background-color: #6A0DAD; padding: 5px; border-top-left-radius: 10px; border-top-right-radius: 10px; text-align: center;">Insights</h3>
            <div style="padding: 10px;">
                <p style="color: black;"><b>Total Number of Jobs:</b> {total_jobs}</p>
                <p style="color: black;"><b>Total Number of Jobs with Visa/Relocation Support:</b> {visa_relocation_jobs}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


# Function to check if job was posted "x months ago"
def check_very_old(posted_time):
    if 'month' in posted_time:
        months_ago = int(posted_time.split()[0])
        if months_ago >= 1:
            return True
    return False

# Streamlit App main function
def main():
    # Initialize Firestore client
    db = initialize_firestore()

    st.set_page_config(page_title='Jobs in EU', page_icon="💼", layout='wide', initial_sidebar_state='auto')
    st.sidebar.header("Filter Jobs")
    job_title = st.sidebar.text_input("Enter Job Title", "").strip()
    location = st.sidebar.text_input("Enter Location", "").strip()
    visa_relocation_filter = st.sidebar.checkbox("Visa/Relocation", value=False)

    job_data = fetch_job_data(db)
    df = pd.DataFrame(job_data)

    # Drop rows with missing values and duplicates
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)

    # Extract email addresses and create 'contact' column
    df['contact'] = df['Job_txt'].apply(lambda x: ', '.join(extract_emails(x)))

    # Check for visa sponsorship or relocation
    df['Visa/Relocation?'] = df['Job_txt'].apply(check_visa_relocation)

    # Filter DataFrame based on user input
    df = filter_dataframe(df, job_title, location, visa_relocation_filter)

    # Rearrange columns and reset index
    df = df[['job-title', 'company', 'Visa/Relocation?', 'contact', 'Job_Link', 'location', 'Job_txt', 'posted-time-ago']]
    df.reset_index(drop=True, inplace=True)

    # Display the contact card in the sidebar
    display_contact_card()
    
    # Calculate insights
    total_jobs = len(df)
    visa_relocation_jobs = (df['Visa/Relocation?'] == 'Yes').sum()

    # Display insights card
    display_insights_card(total_jobs, visa_relocation_jobs)

    # Display the cards
    display_cards(df)

if __name__ == "__main__":
    main()
