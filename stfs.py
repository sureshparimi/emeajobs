import streamlit as st
import re
import os
from google.cloud import firestore
import pandas as pd

# Initialize Firestore client
# db = firestore.Client.from_service_account_json("streamlit-db-f3c12-firebase-adminsdk-16b45-be4c4ab3af.json")
# Function to load secrets from environment variables
def load_secrets_from_env():
    secrets = {
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),  # Replace escape characters
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
    }
    return secrets

# Initialize Firestore client using GitHub secrets
secrets = load_secrets_from_env()
db = firestore.Client.from_service_account_info(secrets)

# Rest of the code remains unchanged

# Function to fetch job data from Firestore
def fetch_job_data():
    job_data = []
    collection_ref = db.collection("linkedinjobs")
    docs = collection_ref.stream()
    for doc in docs:
        doc_data = doc.to_dict()
        job_data.extend(doc_data.get("jobs", []))
    return job_data

# Extract email addresses from text using regex
def extract_emails(text):
    return re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

# Check if job description contains visa sponsorship or relocation
def check_visa_relocation(text):
    text = text.lower()
    if 'visa sponsorship' in text or 'relocation' in text:
        return 'Yes'
    else:
        return 'No'

# Streamlit App
def main():
    st.set_page_config( page_title='Jobs in EU', page_icon="heart", layout='wide', initial_sidebar_state='auto')
    # st.title("EUJOBS")
    st.sidebar.header("Filter Jobs")
    job_title = st.sidebar.text_input("Enter Job Title", "").strip()
    location = st.sidebar.text_input("Enter Location", "").strip()
    visa_relocation_filter = st.sidebar.checkbox("Visa/Relocation", value=False)

    job_data = fetch_job_data()
    df = pd.DataFrame(job_data)

    # Drop rows with missing values
    df.dropna(inplace=True)

    # Drop duplicate jobs
    df.drop_duplicates(inplace=True)

    # Filter DataFrame based on user input
    if job_title:
        df = df[df['job-title'].str.contains(job_title, case=False)]

    if location:
        df = df[df['location'].str.contains(location, case=False)]

    # Extract email addresses and create 'contact' column
    df['contact'] = df['Job_txt'].apply(lambda x: ', '.join(extract_emails(x)))

    # Check for visa sponsorship or relocation
    df['Visa/Relocation?'] = df['Job_txt'].apply(check_visa_relocation)

    # Filter DataFrame based on checkbox selection
    if visa_relocation_filter:
        df = df[df['Visa/Relocation?'] == 'Yes']

    # Remove rows where posted_time_ago contains months ago
    df = df[~df['posted-time-ago'].str.contains('months ago', na=False)]

    # Rearrange columns
    df = df[['job-title', 'company', 'Visa/Relocation?', 'contact', 'Job_Link', 'location'] + [col for col in df.columns if col not in ['job-title', 'company', 'Visa/Relocation?', 'contact', 'Job_Link', 'location']]]

    # Reset index to display sequential row numbers
    df.reset_index(drop=True, inplace=True)

    # Display container layout for number of jobs with Visa sponsorship/relocation
    num_jobs_visa_relocation = df['Visa/Relocation?'].value_counts().get('Yes', 0)
    visa_container = st.container()
    with visa_container:
        st.markdown(f"<h2 style='color:#3366ff;'>Number of Jobs with Visa Sponsorship/Relocation: {num_jobs_visa_relocation}</h2>", unsafe_allow_html=True)

    st.dataframe(df)

if __name__ == "__main__":
    main()
