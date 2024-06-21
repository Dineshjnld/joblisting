import os
import streamlit as st
from pymongo import MongoClient
from passlib.hash import pbkdf2_sha256
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# # Load environment variables from .env file
# load_dotenv()

# Get MongoDB connection string from environment variable
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")

# Email configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Connect to MongoDB cluster
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
            st.session_state.role = user["role"]  # Initialize role in session state
            st.experimental_rerun()  # Redirect to job listings page after sign-in
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
                "role": "user"  # Default role for new users
            }
            users_collection.insert_one(user_data)
            st.success("You have successfully signed up! Please sign in.")
            # st.button("Sign In", on_click=sign_in)  # Add sign-in button after successful sign-up
        else:
            st.error("Passwords do not match. Please try again.")

# Streamlit job listings
# Streamlit job listings
def job_listings():
    st.title("Job Listings")
    search_title = st.text_input("Search by Job Title")
    if search_title:
        jobs = jobs_collection.find({"title": {"$regex": search_title, "$options": "i"}}).sort("timestamp", -1)
    else:
        jobs = jobs_collection.find().sort("timestamp", -1)  # Sort in descending order
    
    
    job_data = []
    for job in jobs:
        job_data.append({
            "ID": job["_id"],  # Store ObjectId instead of converting to string
            "Title": job["title"],
            "Company": job["company"],
            "Location": job["location"],
            "Description": job["description"],
            "Apply Link": job.get("apply_link", ""),
        })

    for job in job_data:
        st.write(f"**Title:** {job['Title']}")
        st.write(f"**Company:** {job['Company']}")
        st.write(f"**Location:** {job['Location']}")
        st.write(f"**Description:** {job['Description']}")
        if job['Apply Link']:
            st.write(f"**Apply Link:** [{job['Apply Link']}]({job['Apply Link']})")
            st.markdown("<a href='" + job['Apply Link'] + "' target='_blank'>Apply</a>", unsafe_allow_html=True)
        if "role" in st.session_state and st.session_state.role == "admin":
            remove_button_key = f"remove_button_{job['ID']}"  # Use job ID directly
            if st.button("Remove Job", key=remove_button_key):
                jobs_collection.delete_one({"_id": job["ID"]})  # Use ObjectId directly
                st.success("Job listing removed successfully.")
        st.write("---")




# Streamlit post job (admin only)
def post_job():
    st.title("Post Job Listing")
    title = st.text_input("Title")
    company = st.text_input("Company")
    location = st.text_input("Location")
    description = st.text_area("Description")
    apply_link = st.text_input("Apply Link")  # Add input field for apply link
    if st.button("Post Job"):
        job_data = {
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "apply_link": apply_link,  # Include apply link in job data
            "timestamp": datetime.utcnow()  # Add timestamp
        }
        jobs_collection.insert_one(job_data)
        st.success("Job listing posted successfully!")
        send_job_notification(title, company, location, description, apply_link)  # Call email sending function

# Function to send job notification email to all users
def send_job_notification(title, company, location, description, apply_link):
    # Fetch user emails only for documents with an "email" field
    user_emails = [user["email"] for user in users_collection.find({"email": {"$exists": True}})]

    # Create message container
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["Subject"] = f"New Job Posted: {title} at {company}"

    # Add body to email
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

    # Send email to each user
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

# Function to sign out
def sign_out():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()  # Redirect to job listings page after sign-out

# Main function
def main():
    st.title("JOBS LISTING PORTAL")
    st.sidebar.title("Navigation")

    # Initialize role in session state after successful sign-in
    if "user_id" in st.session_state and "role" in st.session_state:
        if st.session_state.role == "admin":
            page = st.sidebar.radio("Go to", ["Job Listings", "Post Job", "Sign Out"])
        else:
            page = st.sidebar.radio("Go to", ["Job Listings", "Sign Out"])
    else:
        page = st.sidebar.radio("Go to", ["Job Listings", "Sign Up", "Sign In"])

    if page == "Sign In":
        sign_in()
    elif page == "Sign Up":
        sign_up()
    elif page == "Sign Out":
        sign_out()

    if page == "Job Listings":
        job_listings()
    elif page == "Post Job":
        if "user_id" not in st.session_state:
            st.error("Please sign in to post job listings.")
        elif "role" not in st.session_state or st.session_state.role != "admin":
            st.error("You don't have permission to access this page.")
        else:
            post_job()

if __name__ == "__main__":
    main()
