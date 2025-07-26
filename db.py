import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")

client = MongoClient(MONGODB_CONNECTION_STRING)
db = client["job_portal"]
users_collection = db["users"]
jobs_collection = db["jobs"]
applications_collection = db["applications"]
resumes_collection = db["resumes"]
