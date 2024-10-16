import os
import logging
from bs4 import BeautifulSoup
from scrape_db_utils import JobPosting, save_job_to_db
from scrape_utils import clean_text, generate_unique_id, contains_word, convert_to_standard_date

# Async function to extract detailed job information
async def extract_job_details(page, job_posting):
    try:
        await page.goto(job_posting.job_link, wait_until='networkidle', timeout=60000)
        await page.wait_for_selector('main#hj-main')
        job_detail_html = await page.content()
        detail_soup = BeautifulSoup(job_detail_html, 'html.parser')

        job_posting.job_summary = clean_text(detail_soup.find('section', id='hj-job-advert').text if detail_soup.find('section', id='hj-job-advert') else 'N/A')
        job_posting.qualifications = clean_text(detail_soup.find('section', id='hj-job-role-requirement').text if detail_soup.find('section', id='hj-job-role-requirement') else 'N/A')
        job_posting.team_structure = clean_text(detail_soup.find('section', id='hj-employer-header').text if detail_soup.find('section', id='hj-employer-header') else 'N/A')
        job_posting.job_description = clean_text(detail_soup.find('section', id='hj-job-advert').text if detail_soup.find('section', id='hj-job-advert') else 'N/A')
        job_posting.working_pattern = clean_text(detail_soup.find('dt', string='Hours').find_next('dd').text if detail_soup.find('dt', string='Hours') else 'N/A')
        job_posting.salary = clean_text(detail_soup.find('dt', string='Salary').find_next('dd').text if detail_soup.find('dt', string='Salary') else 'N/A')
        job_posting.closing_date = convert_to_standard_date(clean_text(detail_soup.find('dt', string='Closing').find_next('dd').text if detail_soup.find('dt', string='Closing') else 'N/A'))
        job_posting.contract_type = clean_text(detail_soup.find('dt', string='Contract').find_next('dd').text if detail_soup.find('dt', string='Contract') else 'N/A')
        job_posting.reference_number = clean_text(detail_soup.find('dt', string='Job ref').find_next('dd').text if detail_soup.find('dt', string='Job ref') else generate_unique_id(job_posting))

        await save_job_to_db(job_posting)

    except Exception as e:
        logging.error(f"Error extracting details for {job_posting.title}: {e}")

# Async function to scrape jobs from HealthJobsUK
async def scrape_jobs_playwright(url, job_search_engine, category, stop_words, considerable_words, browser):
    # Check if jobs.db exists
    db_exists = os.path.exists('/app/db/jobs.db')
    max_pages = 2 if db_exists else None  # Set to 2 if db exists, otherwise scrape all pages
    page_number = 1
    
    job_listings = []
    page = await browser.new_page()  # Use the shared browser to create a new page within the correct loop
        
    try:
        while True:
            # Handle pagination and stop after 2 pages if db exists
            if max_pages and page_number > max_pages:
                logging.info(f"Max pages limit '({max_pages})' reached for {job_search_engine} website, stopping pagination.")
                break
            
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('main#hj-main')
            soup = BeautifulSoup(await page.content(), 'html.parser')

            logging.info(f"Scraping Page {page_number} started.")

            job_elements = soup.find_all('li', class_='hj-job')
            for job in job_elements:
                title = clean_text(job.find('div', class_='hj-jobtitle').text) if job.find('div', class_='hj-jobtitle') else 'N/A'

                # Skip jobs with stop words
                if contains_word(title, stop_words):
                    logging.info(f"Skipped job with title: {title} (contains stop word)")
                    continue
                
                # Process jobs with considerable words
                if not contains_word(title, considerable_words):
                    logging.info(f"Skipped job with title: {title} (does not contain any considerable word)")
                    continue  # Skip this job if it doesn't contain any considerable words

                job_link = f"https://www.healthjobsuk.com{job.find('a')['href']}" if job.find('a', href=True) else 'N/A'
                location = clean_text(job.find('div', class_='hj-locationtown').text) if job.find('div', class_='hj-locationtown') else 'N/A'
                salary = clean_text(job.find('div', class_='hj-salary').text) if job.find('div', class_='hj-salary') else 'N/A'
                contract_type = clean_text(job.find('div', class_='hj-contract').text) if job.find('div', class_='hj-contract') else 'N/A'
                working_pattern = clean_text(job.find('div', class_='hj-hours').text) if job.find('div', class_='hj-hours') else 'N/A'
                
                # Extract date_posted and closing_date
                date_posted = clean_text(job.find('div', class_='hj-dateposted').text) if job.find('div', class_='hj-dateposted') else 'N/A'
                closing_date = convert_to_standard_date(clean_text(job.find('div', class_='hj-closingdate').text) if job.find('div', class_='hj-closingdate') else 'N/A')

                # Create job posting object with all required fields
                job_posting = JobPosting(
                    job_search_engine=job_search_engine,
                    category=category,
                    title=title,
                    location=location,
                    salary=salary,
                    date_posted=date_posted,  # Make sure to include this
                    closing_date=closing_date,  # Make sure to include this
                    contract_type=contract_type,
                    working_pattern=working_pattern,
                    job_link=job_link
                )

                # Extract more details
                await extract_job_details(page, job_posting)
                job_listings.append(job_posting)

            logging.info(f"Page {page_number} scraped.")

            # Handle pagination
            next_page_tag = soup.find('a', class_='page-link', href=True, title='Next page')
            if next_page_tag:
                url = f"https://www.healthjobsuk.com{next_page_tag['href']}"
                page_number += 1
            else:
                break

    except Exception as e:
        logging.error(f"Error while scraping page {page_number}: {e}")
    finally:
        await page.close()  # Close the page after scraping

    return job_listings
