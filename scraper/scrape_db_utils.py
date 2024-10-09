import os
import logging
import aiosqlite  # For async SQLite operations
from telegram_bot import send_telegram_message

# Centralized config for environment variables
class Config:
    DB_FILE = os.getenv("DB_FILE", "/app/db/jobs.db")

# JobPosting class to store job information
class JobPosting:
    def __init__(self, job_search_engine, category, title, location, salary, date_posted, closing_date, contract_type, working_pattern, job_link):
        self.reference_number = None
        self.job_search_engine = job_search_engine
        self.category = category
        self.title = title
        self.location = location
        self.working_pattern = working_pattern
        self.salary = salary
        self.date_posted = date_posted
        self.closing_date = closing_date
        self.contract_type = contract_type
        self.grade = None
        self.duration = None
        self.job_link = job_link
        self.job_summary = None
        self.main_duties = None
        self.job_description = None
        self.team_structure = None
        self.qualifications = None
        self.employer_name = None
        self.employer_contact = None
        self.employer_address = None
        self.disclosure_check = None
        self.certificate_of_sponsorship = None
        self.uk_registration = None
        self.pay_scheme = None

    def __repr__(self):
        return (
            f"Reference Number: {self.reference_number}\n\n"
            f"Job Search Engine: {self.job_search_engine}\n\n"
            f"Category: {self.category}\n\n"
            f"Job Title: {self.title}\n\n"
            f"Location: {self.location}\n\n"
            f"Working Pattern: {self.working_pattern}\n\n"
            f"Salary: {self.salary}\n\n"
            f"Date Posted: {self.date_posted}\n\n"
            f"Closing Date: {self.closing_date}\n\n"
            f"Contract Type: {self.contract_type}\n\n"
            f"Grade: {self.grade}\n\n"
            f"Duration: {self.duration}\n\n"
            f"Job Link: {self.job_link}\n\n"
            f"Job Summary: {self.job_summary}\n\n"
            f"Main Duties: {self.main_duties}\n\n"
            f"Job Description: {self.job_description}\n\n"
            f"Team Structure: {self.team_structure}\n\n"
            f"Qualifications: {self.qualifications}\n\n"
            f"Employer Name: {self.employer_name}\n\n"
            f"Employer Contact: {self.employer_contact}\n\n"
            f"Employer Address: {self.employer_address}\n\n"
            f"Disclosure Check: {self.disclosure_check}\n\n"
            f"Certificate of Sponsorship: {self.certificate_of_sponsorship}\n\n"
            f"UK Registration: {self.uk_registration}\n\n"
            f"Pay Scheme: {self.pay_scheme}\n\n"
        )

# Initialize the SQLite database and jobs table
async def init_db():
    async with aiosqlite.connect(Config.DB_FILE) as conn:
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_number TEXT UNIQUE,
            job_search_engine TEXT,
            category TEXT,
            title TEXT,
            location TEXT,
            working_pattern TEXT,
            salary TEXT,
            date_posted TEXT,
            closing_date TEXT,
            contract_type TEXT,
            grade TEXT,
            duration TEXT,
            job_link TEXT,
            job_summary TEXT,
            main_duties TEXT,
            job_description TEXT,
            team_structure TEXT,
            qualifications TEXT,
            employer_name TEXT,
            employer_contact TEXT,
            employer_address TEXT,
            disclosure_check TEXT,
            certificate_of_sponsorship TEXT,
            uk_registration TEXT,
            pay_scheme TEXT
        )
        ''')
        await conn.commit()

# Check if a job already exists in the database based on reference number
async def job_exists(reference_number):
    async with aiosqlite.connect(Config.DB_FILE) as conn:
        cursor = await conn.execute("SELECT 1 FROM jobs WHERE reference_number = ?", (reference_number,))
        return await cursor.fetchone() is not None

# Save a job posting to the database
async def save_job_to_db(job_posting):
    async with aiosqlite.connect(Config.DB_FILE) as conn:
        if not await job_exists(job_posting.reference_number):
            logging.info(f"Job Inserted - Reference Number: {job_posting.reference_number}")

            job_data = (
                job_posting.reference_number or 'N/A',
                job_posting.job_search_engine or 'N/A',
                job_posting.category or 'N/A',
                job_posting.title or 'N/A',
                job_posting.location or 'N/A',
                job_posting.working_pattern or 'N/A',
                job_posting.salary or 'N/A',
                job_posting.date_posted or 'N/A',
                job_posting.closing_date or 'N/A',
                job_posting.contract_type or 'N/A',
                job_posting.grade or 'N/A',
                job_posting.duration or 'N/A',
                job_posting.job_link or 'N/A',
                job_posting.job_summary or 'N/A',
                job_posting.main_duties or 'N/A',
                job_posting.job_description or 'N/A',
                job_posting.team_structure or 'N/A',
                job_posting.qualifications or 'N/A',
                job_posting.employer_name or 'N/A',
                job_posting.employer_contact or 'N/A',
                job_posting.employer_address or 'N/A',
                job_posting.disclosure_check or 'N/A',
                job_posting.certificate_of_sponsorship or 'N/A',
                job_posting.uk_registration or 'N/A',
                job_posting.pay_scheme or 'N/A'
            )

            await conn.execute('''
            INSERT INTO jobs (
                reference_number, job_search_engine, category, title, location, working_pattern, salary,
                date_posted, closing_date, contract_type, grade, duration, job_link, job_summary, main_duties,
                job_description, team_structure, qualifications, employer_name, employer_contact, employer_address,
                disclosure_check, certificate_of_sponsorship, uk_registration, pay_scheme
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', job_data)
            await conn.commit()
            
            await send_telegram_message(job_posting)
        else:
            logging.info(f"Job Existed - Reference Number: {job_posting.reference_number}")
