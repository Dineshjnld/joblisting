import streamlit as st
from db import jobs_collection, users_collection, applications_collection
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def job_listings():
    st.title("Job Listings")
    search_title = st.text_input("Search by Job Title")
    search_location = st.text_input("Search by Location")
    search_company = st.text_input("Search by Company")

    query = {}
    if search_title:
        query["title"] = {"$regex": search_title, "$options": "i"}
    if search_location:
        query["location"] = {"$regex": search_location, "$options": "i"}
    if search_company:
        query["company"] = {"$regex": search_company, "$options": "i"}

    jobs_per_page = 10
    total_jobs = jobs_collection.count_documents(query)
    total_pages = (total_jobs + jobs_per_page - 1) // jobs_per_page

    page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1)

    skip = (page_number - 1) * jobs_per_page
    jobs = jobs_collection.find(query).sort("timestamp", -1).skip(skip).limit(jobs_per_page)

    job_data = []
    for job in jobs:
        job_data.append({
            "ID": job["_id"],
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
            if st.button("Apply", key=f"apply_button_{job['ID']}"):
                if "user_id" in st.session_state:
                    application_data = {
                        "user_id": st.session_state["user_id"],
                        "job_id": job["ID"],
                        "timestamp": datetime.utcnow()
                    }
                    applications_collection.insert_one(application_data)
                    st.success("You have successfully applied for this job.")
                else:
                    st.error("You must be logged in to apply for a job.")
        if "role" in st.session_state and st.session_state.role == "admin":
            remove_button_key = f"remove_button_{job['ID']}"
            if st.button("Remove Job", key=remove_button_key):
                jobs_collection.delete_one({"_id": job["ID"]})
                st.success("Job listing removed successfully.")
        st.write("---")

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

from celery_worker import send_email_task


def send_job_notification(title, company, location, description, apply_link):
    user_emails = [user["email"] for user in users_collection.find({"email": {"$exists": True}})]

    subject = f"New Job Posted: {title} at {company}"
    body = f\"\"\"
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
    \"\"\"

    for email in user_emails:
        send_email_task.delay(email, subject, body)
