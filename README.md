# Job Portal

This is a Streamlit web application for a job portal.

## Features

- User authentication (sign-up, sign-in, sign-out)
- Job listings with search and filtering
- Admin panel to post and remove jobs
- User profiles with resume upload
- Asynchronous email notifications for new jobs

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/job-portal.git
   cd job-portal
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your environment variables:**
   Create a `.env` file in the root directory and add the following variables:
   ```
   MONGODB_CONNECTION_STRING="your_mongodb_connection_string"
   SENDER_EMAIL="your_email@gmail.com"
   EMAIL_PASSWORD="your_email_password"
   ```

5. **Run the Redis server:**
   Make sure you have Redis installed and running on your local machine.

6. **Run the Celery worker:**
   ```bash
   celery -A celery_worker.celery_app worker --loglevel=info
   ```

7. **Run the Streamlit application:**
   ```bash
   streamlit run main.py
   ```
