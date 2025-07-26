import streamlit as st
from db import users_collection
from bson.objectid import ObjectId

from db import applications_collection, jobs_collection, resumes_collection
import gridfs
from db import db


def user_profile():
    st.title("User Profile")

    if "user_id" not in st.session_state:
        st.error("You must be logged in to view your profile.")
        return

    user_id = st.session_state["user_id"]
    user = users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        st.error("User not found.")
        return

    st.write(f"**Username:** {user['username']}")
    st.write(f"**Email:** {user['email']}")

    st.subheader("Update Your Information")
    new_email = st.text_input("New Email", value=user["email"])
    if st.button("Update Email"):
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"email": new_email}})
        st.success("Your email has been updated.")
        st.experimental_rerun()

    st.subheader("Upload Your Resume")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx"])
    if uploaded_file is not None:
        fs = gridfs.GridFS(db)
        fs.put(uploaded_file, filename=uploaded_file.name, user_id=user_id)
        st.success("Resume uploaded successfully.")

    st.subheader("Your Job Applications")
    applications = applications_collection.find({"user_id": user_id})
    for app in applications:
        job = jobs_collection.find_one({"_id": app["job_id"]})
        if job:
            st.write(f"**Title:** {job['title']}")
            st.write(f"**Company:** {job['company']}")
            st.write("---")
