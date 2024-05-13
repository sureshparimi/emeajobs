import streamlit as st
import re
from google.cloud import firestore
import pandas as pd

st.markdown(
   """
<style>
   .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
   .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
   .viewerBadge_text__1JaDK {
       display: none;
   }
</style>
   """,
   unsafe_allow_html=
True
)

# Function to extract email addresses from text using regex
def extract_emails(text):
    return re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

# Function to check if job description contains visa sponsorship or relocation
def check_visa_relocation(text):
    text = text.lower()
    if 'visa sponsorship' in text or 'relocation' in text:
        return 'Yes'
    else:
        return 'No'

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

# Streamlit App
def main():
    # Initialize Firestore client using Streamlit secrets
    db = initialize_firestore()

    st.set_page_config( page_title='Jobs in EU', page_icon="heart", layout='wide', initial_sidebar_state='auto')
    st.sidebar.header("Filter Jobs")
    job_title = st.sidebar.text_input("Enter Job Title", "").strip()
    location = st.sidebar.text_input("Enter Location", "").strip()
    visa_relocation_filter = st.sidebar.checkbox("Visa/Relocation", value=False)
    # Add a link to join WhatsApp community in the sidebar
    st.sidebar.markdown("[Join our WhatsApp community](https://chat.whatsapp.com/BcUJsbRxWX8C8ipOweUso5)")
   # Developer details box
    st.sidebar.header("Developer details")
    st.sidebar.markdown("""
    <div style="border-radius: 15px; background-color: #f0f0f0; padding: 10px; margin-bottom: 10px;">
        <h3>Developer Name: Suresh Parimi</h3>
        <p><a href="https://linkedin.com/in/sparimi" target="_blank">Linkedin</a></p>
        <p>Location: Amsterdam, Netherlands</p>
    </div>
    """, unsafe_allow_html=True)
    job_data = fetch_job_data(db)
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

    # Remove rows where posted_time_ago contains 'months ago'
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
