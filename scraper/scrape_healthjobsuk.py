import os
import logging
import random
import asyncio
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from scrape_db_utils import JobPosting, save_job_to_db
from scrape_utils import (
    clean_text,
    generate_unique_id,
    contains_word,
    convert_to_standard_date
)

# ----------------------------------------------------------------------
#                            HELPERS
# ----------------------------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

async def safe_page_goto(page, url, wait_until='domcontentloaded', max_retries=3):
    """
    Navigate to `url` using Playwright with retries.
    Sets a random User-Agent and random delay to reduce blocking.
    """
    for attempt in range(1, max_retries + 1):
        try:
            # Random User-Agent
            await page.set_extra_http_headers({
                "User-Agent": random.choice(USER_AGENTS)
            })
            # Omit making delay, because the server itself is slow enough
            # Random delay before each request
            # await asyncio.sleep(random.uniform(0.5, 1))

            await page.goto(url, wait_until=wait_until, timeout=30000)
            return
        except Exception as e:
            logging.error(f"[safe_page_goto] Attempt {attempt} failed for {url}: {e}")
            if attempt == max_retries:
                raise

# ----------------------------------------------------------------------
#                  EXTRACT JOB DETAILS
# ----------------------------------------------------------------------
async def extract_job_details(page, job_posting):
    """
    Extracts detailed job information from a HealthJobsUK job detail page.
    Saves each job posting individually (no batch insert).
    """
    try:
        await safe_page_goto(page, job_posting.job_link, wait_until='domcontentloaded')
        await page.wait_for_selector('main#hj-main')

        job_detail_html = await page.content()
        detail_soup = BeautifulSoup(job_detail_html, 'html.parser')

        job_posting.job_summary = clean_text(
            detail_soup.find('section', id='hj-job-advert').text
        ) if detail_soup.find('section', id='hj-job-advert') else 'N/A'

        job_posting.qualifications = clean_text(
            detail_soup.find('section', id='hj-job-role-requirement').text
        ) if detail_soup.find('section', id='hj-job-role-requirement') else 'N/A'

        job_posting.team_structure = clean_text(
            detail_soup.find('section', id='hj-employer-header').text
        ) if detail_soup.find('section', id='hj-employer-header') else 'N/A'

        job_posting.job_description = clean_text(
            detail_soup.find('section', id='hj-job-advert').text
        ) if detail_soup.find('section', id='hj-job-advert') else 'N/A'

        job_posting.working_pattern = clean_text(
            detail_soup.find('dt', string='Hours').find_next('dd').text
        ) if detail_soup.find('dt', string='Hours') else 'N/A'

        job_posting.salary = clean_text(
            detail_soup.find('dt', string='Salary').find_next('dd').text
        ) if detail_soup.find('dt', string='Salary') else 'N/A'

        closing_raw = clean_text(
            detail_soup.find('dt', string='Closing').find_next('dd').text
        ) if detail_soup.find('dt', string='Closing') else 'N/A'
        job_posting.closing_date = convert_to_standard_date(closing_raw)

        job_posting.contract_type = clean_text(
            detail_soup.find('dt', string='Contract').find_next('dd').text
        ) if detail_soup.find('dt', string='Contract') else 'N/A'

        ref_tag = detail_soup.find('dt', string='Job ref')
        if ref_tag:
            job_posting.reference_number = clean_text(ref_tag.find_next('dd').text)
        else:
            job_posting.reference_number = generate_unique_id(job_posting)

        # Save the job posting to the database
        await save_job_to_db(job_posting)

    except Exception as e:
        logging.error(f"Error extracting details for {job_posting.title}: {e}")

# ----------------------------------------------------------------------
#               HELPER: SCRAPE CURRENT PAGE (One pass)
# ----------------------------------------------------------------------
async def scrape_current_page(
    page, 
    all_jobs, 
    stop_words, 
    considerable_words,
    job_search_engine, 
    category
):
    """
    Reads the job cards from the current loaded page,
    extracts details, saves to DB, and appends to `all_jobs`.
    """
    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')

    job_elements = soup.find_all('li', class_='hj-job')
    logging.info(f"Found {len(job_elements)} jobs on this page.")

    for job in job_elements:
        title_tag = job.find('div', class_='hj-jobtitle')
        title = clean_text(title_tag.text) if title_tag else 'N/A'

        # Skip jobs with stop words
        if contains_word(title, stop_words):
            logging.info(f"Skipped job '{title}' (contains stop word)")
            continue

        # Skip if missing "considerable" words
        if not contains_word(title, considerable_words):
            logging.info(f"Skipped job '{title}' (no considerable words)")
            continue

        # Extract job link
        link_tag = job.find('a', href=True)
        job_link = f"https://www.healthjobsuk.com{link_tag['href']}" if link_tag else 'N/A'

        # Basic fields
        location_tag = job.find('div', class_='hj-locationtown')
        salary_tag = job.find('div', class_='hj-salary')
        contract_tag = job.find('div', class_='hj-contract')
        hours_tag = job.find('div', class_='hj-hours')
        date_posted_tag = job.find('div', class_='hj-dateposted')
        closing_date_tag = job.find('div', class_='hj-closingdate')

        location = clean_text(location_tag.text) if location_tag else 'N/A'
        salary = clean_text(salary_tag.text) if salary_tag else 'N/A'
        contract_type = clean_text(contract_tag.text) if contract_tag else 'N/A'
        working_pattern = clean_text(hours_tag.text) if hours_tag else 'N/A'
        date_posted = clean_text(date_posted_tag.text) if date_posted_tag else 'N/A'
        closing_date = convert_to_standard_date(clean_text(closing_date_tag.text) if closing_date_tag else 'N/A')

        # Create the JobPosting
        job_posting = JobPosting(
            job_search_engine=job_search_engine,
            category=category,
            title=title,
            location=location,
            salary=salary,
            date_posted=date_posted,
            closing_date=closing_date,
            contract_type=contract_type,
            working_pattern=working_pattern,
            job_link=job_link
        )

        # Extract & save job details (single insert)
        await extract_job_details(page, job_posting)
        all_jobs.append(job_posting)

    logging.info(f"Scraped {len(job_elements)} job(s) on this page, {len(all_jobs)} total so far.")

# ----------------------------------------------------------------------
#                   SCRAPE HEALTHJOBSUK (Steps as requested)
# ----------------------------------------------------------------------

async def scrape_jobs_playwright(
    url,
    job_search_engine,
    category,
    stop_words,
    considerable_words,
    browser
):
    """
    Steps:
      1. Go to the main URL.
      2. Handle the cookie consent button (Accept All), if present.
      3. Scrape the first page.
    """
    all_jobs = []
    page = await browser.new_page()

    try:
        # (1) Go to main URL
        logging.info("[HealthJobsUK] Loading main URL.")
        await page.goto(url, wait_until='domcontentloaded')

        # (2) Handle cookie consent if present
        try:
            await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=3000)
            await page.click('#onetrust-accept-btn-handler')
            logging.info("[HealthJobsUK] Clicked 'Accept All' cookies button.")
        except Exception:
            logging.info("[HealthJobsUK] Cookie accept button not found; continuing.")
            
        # (3) Scrape the first page
        logging.info("[HealthJobsUK] Scraping the first page.")
        logging.info(f"[HealthJobsUK] Current URL: {page.url}")
        await scrape_current_page(
            page, all_jobs, stop_words, considerable_words,
            job_search_engine, category
        )

    except Exception as e:
        logging.error(f"Error during HealthJobsUK scrape: {e}")
    finally:
        await page.close()

    return all_jobs