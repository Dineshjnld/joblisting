import streamlit as st
from auth import sign_in, sign_up, sign_out
from jobs import job_listings, post_job
from profile import user_profile
from db import users_collection
from passlib.hash import pbkdf2_sha256

# Check if admin user exists in the database, if not, create one
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = pbkdf2_sha256.hash("password")
admin_user = users_collection.find_one({"username": ADMIN_USERNAME})
if not admin_user:
    admin_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "role": "admin"
    }
    users_collection.insert_one(admin_data)

def main():
    st.title("JOBS LISTING PORTAL")
    st.sidebar.title("Navigation")

    if "user_id" in st.session_state and "role" in st.session_state:
        if st.session_state.role == "admin":
            page = st.sidebar.radio("Go to", ["Job Listings 💼", "Post Job 📝", "Profile 👤", "Sign Out ➡️"])
        else:
            page = st.sidebar.radio("Go to", ["Job Listings 💼", "Profile 👤", "Sign Out ➡️"])
    else:
        page = st.sidebar.radio("Go to", ["Job Listings 💼", "Sign Up 📝", "Sign In ➡️"])

    if page == "Sign In ➡️":
        sign_in()
    elif page == "Sign Up 📝":
        sign_up()
    elif page == "Sign Out ➡️":
        sign_out()

    if page == "Job Listings 💼":
        job_listings()
    elif page == "Post Job 📝":
        if "user_id" not in st.session_state:
            st.error("Please sign in to post job listings.")
        elif "role" not in st.session_state or st.session_state.role != "admin":
            st.error("You don't have permission to access this page.")
        else:
            post_job()
    elif page == "Profile 👤":
        user_profile()

if __name__ == "__main__":
    main()
