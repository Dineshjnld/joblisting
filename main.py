import os
import streamlit as st
from pymongo import MongoClient
from passlib.hash import pbkdf2_sha256

# Get MongoDB connection string from environment variable
MONGODB_CONNECTION_STRING = os.environ.get("MONGODB_CONNECTION_STRING")

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

# Streamlit sign-in page
def sign_in_page():
    st.title("Sign In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        user = users_collection.find_one({"username": username})
        if user and pbkdf2_sha256.verify(password, user["password"]):
            st.success("You have successfully signed in!")
            st.session_state.user_id = user["_id"]
            st.session_state.role = user["role"]
            return True
        else:
            st.error("Invalid username or password. Please try again.")
            return False

# Streamlit sign-up page
def sign_up_page():
    st.title("Sign Up")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Sign Up"):
        if password == confirm_password:
            hashed_password = pbkdf2_sha256.hash(password)
            user_data = {
                "username": username,
                "password": hashed_password,
                "role": "user"  # Default role for new users
            }
            users_collection.insert_one(user_data)
            st.success("You have successfully signed up! Please sign in.")
        else:
            st.error("Passwords do not match. Please try again.")

# Streamlit user page
def user_page():
    st.title("User Page")
    st.write("Welcome, User!")
    # Add user functionalities here

# Streamlit admin page
def admin_page():
    st.title("Admin Page")
    st.write("Welcome, Admin!")
    # Add admin functionalities here

# Main function to handle navigation
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Sign In", "Sign Up", "User", "Admin"])

    if page == "Sign In":
        if sign_in_page():
            st.experimental_rerun()
    elif page == "Sign Up":
        sign_up_page()
    elif page == "User":
        if "user_id" not in st.session_state:
            st.error("Please sign in to access user page.")
        else:
            user_page()
    elif page == "Admin":
        if "user_id" not in st.session_state:
            st.error("Please sign in to access admin page.")
        elif st.session_state.role != "admin":
            st.error("You don't have permission to access this page.")
        else:
            admin_page()

if __name__ == "__main__":
    main()
