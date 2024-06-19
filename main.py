import os
import streamlit as st
from pymongo import MongoClient
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import google.generativeai as genai
import PyPDF2 as pdf
import json
import plotly.express as px

# Load environment variables
# load_dotenv()

# MongoDB and Email configuration
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Google Generative AI
if not GOOGLE_API_KEY:
    st.error("Google API key not found. Please set the GOOGLE_API_KEY environment variable.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Connect to MongoDB
client = MongoClient(MONGODB_CONNECTION_STRING)
db = client["job_portal"]
users_collection = db["users"]
jobs_collection = db["jobs"]

# Define admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = pbkdf2_sha256.hash("password")

# Check if admin user exists in the database, if not, create one
admin_user = users_collection.find_one({"username": ADMIN_USERNAME})
if not admin_user:
    admin_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "role": "admin"
    }
    users_collection.insert_one(admin_data)
# import os

# Ensure the resumes directory exists
RESUME_DIR = "resumes"
if not os.path.exists(RESUME_DIR):
    os.makedirs(RESUME_DIR)
    

# Function to read text from PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += page.extract_text()
    return text

# Prompt template for Generative AI
input_prompt = """
Hey, act like a skilled or very experienced ATS (applicants tracking system) with a deep understanding of the tech field, software engineering, data science, data analyst, and big data engineer. Your task is to evaluate the resume based on the given job description. You must consider the job market is very competitive, and you should provide the best assistance for improving the resumes. Assign the percentage Matching based on the job description and the missing keyword with high accuracy.
resume:{text}
description: {jd}
I want the response in one single string having the structure {{"JD Match":"%", "Missing keywords":[], "profile summary":"" }}
"""

# Function to get response from Generative AI
def get_gemini_response(input_text):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input_text)
    return response.text

# Streamlit sign-in form
def sign_in():
    st.title("Sign In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        user = users_collection.find_one({"username": username})
        if user and pbkdf2_sha256.verify(password, user["password"]):
            st.success("You have successfully signed in!")
            st.session_state.user_id = user["_id"]
            st.session_state.username = user["username"]
            st.session_state.role = user["role"]
            st.experimental_rerun()
        else:
            st.error("Invalid username or password. Please try again.")

# Streamlit sign-up form
def sign_up():
    st.title("Sign Up")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Sign Up"):
        if password == confirm_password:
            hashed_password = pbkdf2_sha256.hash(password)
            user_data = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "role": "user"
            }
            users_collection.insert_one(user_data)
            st.success("You have successfully signed up! Please sign in.")
        else:
            st.error("Passwords do not match. Please try again.")

# Streamlit job listings
def job_listings():
    st.title("Job Listings")
    search_title = st.text_input("Search by Job Title")
    if search_title:
        jobs = jobs_collection.find({"title": {"$regex": search_title, "$options": "i"}}).sort("timestamp", -1)
    else:
        jobs = jobs_collection.find().sort("timestamp", -1)
    
    for job in jobs:
        st.write(f"**Title:** {job['title']}")
        st.write(f"**Company:** {job['company']}")
        st.write(f"**Location:** {job['location']}")
        st.write(f"**Description:** {job['description']}")
        if job.get('apply_link'):
            st.write(f"**Apply Link:** [{job['apply_link']}]({job['apply_link']})")
        if "role" in st.session_state and st.session_state.role == "admin":
            if st.button(f"Remove Job: {job['_id']}"):
                jobs_collection.delete_one({"_id": job["_id"]})
                st.success("Job listing removed successfully.")
        if "role" in st.session_state and st.session_state.role == "user":
            if st.button(f"Get Suggestions: {job['_id']}"):
                ats_match_analyzer(job['description'])
        st.write("---")

# Streamlit post job (admin only)
def post_job():
    st.title("Post Job Listing")
    title = st.text_input("Title")
    company = st.text_input("Company")
    location = st.text_input("Location")
    description = st.text_area("Description")
    apply_link = st.text_input("Apply Link")
    if st.button("Post Job"):
        job_data = {
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "apply_link": apply_link,
            "timestamp": datetime.utcnow()
        }
        jobs_collection.insert_one(job_data)
        st.success("Job listing posted successfully!")
        send_job_notification(title, company, location, description, apply_link)

# Function to send job notification email to all users
def send_job_notification(title, company, location, description, apply_link):
    user_emails = [user["email"] for user in users_collection.find({"email": {"$exists": True}})]

    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["Subject"] = f"New Job Posted: {title} at {company}"

    body = f"""
    Hello,

    A new job has been posted on our job portal:

    Title: {title}
    Company: {company}
    Location: {location}
    Description: {description}
    Apply Link: {apply_link}

    Check it out and apply if interested!

    Best regards,
    Truinfo.live,
    https://truinfo.live/
    """
    message.attach(MIMEText(body, "plain"))

    for email in user_emails:
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, message.as_string())
            server.quit()
            st.success(f"Notification email sent to {email}")
        except Exception as e:
            st.error(f"Failed to send email to {email}: {str(e)}")

# Function for ATS Match Analyzer
def ats_match_analyzer(job_description):
    st.title("ATS Match Analyzer")
    st.text("Improve your resume")
    user_id = st.session_state.user_id
    user = users_collection.find_one({"_id": user_id})
    
    if "resume" not in user:
        st.error("Please upload your resume in your profile page.")
        return
    
    resume_text = input_pdf_text(user["resume"])
    response = get_gemini_response(input_prompt.format(text=resume_text, jd=job_description))

    if response:
        try:
            response = response.strip()
            parsed_response = json.loads(response)
            jd_match = float(parsed_response["JD Match"].strip('%'))

            fig = px.pie(
                values=[jd_match, 100 - jd_match],
                names=['Match', 'Mismatch'],
                title="Matching Percentage",
                color_discrete_sequence=['lightgreen', 'lightcoral'],
                labels={'Match': f'{jd_match:.1f}%', 'Mismatch': f'{100 - jd_match:.1f}%'}
            )
            st.plotly_chart(fig)

            st.subheader("Missing Keywords")
            missing_keywords = parsed_response["Missing keywords"]
            if missing_keywords:
                st.markdown(f"<p style='color:red'>{', '.join(missing_keywords)}</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:green'>No missing keywords!</p>")

            st.subheader("Profile Summary")
            st.markdown(parsed_response["profile summary"])
        except json.JSONDecodeError as e:
            st.error(f"Failed to decode the response. The API response is not valid JSON. Error: {e}")
            st.text("Response received before JSON decoding error:")
            st.text(response)
    else:
        st.error("No response from Generative AI model.")

# User dashboard/profile page
def user_dashboard():
    st.title("User Dashboard")
    user_id = st.session_state.user_id
    user = users_collection.find_one({"_id": user_id})
    
    st.write(f"**Username:** {user['username']}")
    st.write(f"**Email:** {user['email']}")
    
    st.subheader("Upload Resume")
    uploaded_file = st.file_uploader("Upload your Resume (PDF only)", type="pdf")
    if uploaded_file is not None:
        resume_file_path = f"resumes/{user['username']}.pdf"
        with open(resume_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        users_collection.update_one({"_id": user_id}, {"$set": {"resume": resume_file_path}})
        st.success("Resume uploaded successfully!")

# Main function to handle routing and user session
def main():
    st.sidebar.title("Navigation")
    menu = ["Job Listings", "Sign In", "Sign Up"]
    if "username" in st.session_state:
        menu.append("Dashboard")
        if st.session_state.role == "admin":
            menu.append("Post Job")
        menu.append("Logout")

    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Job Listings":
        job_listings()
    elif choice == "Sign In":
        sign_in()
    elif choice == "Sign Up":
        sign_up()
    elif choice == "Dashboard":
        user_dashboard()
    elif choice == "Post Job":
        post_job()
    elif choice == "Logout":
        st.session_state.clear()
        st.experimental_rerun()

if __name__ == "__main__":
    main()
