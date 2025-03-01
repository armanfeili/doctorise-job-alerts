import os
import logging
import random
import asyncio
from bs4 import BeautifulSoup

from scrape_db_utils import JobPosting, save_job_to_db
from scrape_utils import (
    clean_text,
    clean_list,
    generate_unique_id,
    contains_word,
    convert_to_standard_date
)

# ----------------------------------------------------------------------
#                          CONFIG & HELPERS
# ----------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

async def safe_page_goto(page, url, wait_until='domcontentloaded', max_retries=3):
    """
    Attempts to navigate to `url` with retries.
    Randomizes User-Agent and adds a small delay to reduce blocking.
    """
    for attempt in range(1, max_retries + 1):
        try:
            # Set a random User-Agent
            await page.set_extra_http_headers({"User-Agent": random.choice(USER_AGENTS)})
            # Random delay before each request
            await asyncio.sleep(random.uniform(0.5, 1))

            await page.goto(url, wait_until=wait_until, timeout=30000)
            return
        except Exception as e:
            logging.error(f"[safe_page_goto] Attempt {attempt} failed for {url}: {e}")
            if attempt == max_retries:
                raise  # Give up after max_retries

def clean_text_with_strong_tags(text, tag):
    """Cleans text and adds bold formatting to specific tags."""
    soup = BeautifulSoup(text, 'html.parser')
    for strong_tag in soup.find_all(tag):
        strong_tag.string = f"**{strong_tag.text}**"
    return ' '.join(soup.stripped_strings)

def extract_tag_text(soup, tag_name, partial_string, next_tag_stop='h2', nested_tag='p'):
    """Extracts text under a specified tag and partial string match."""
    tag = soup.find(tag_name, string=lambda txt: txt and partial_string.lower() in txt.lower())
    if tag:
        content = []
        for sibling in tag.find_next_siblings():
            if sibling.name == nested_tag and sibling.name != next_tag_stop:
                snippet = clean_text_with_strong_tags(str(sibling), 'strong')
                content.append(snippet)
        return clean_text(' '.join(content)) if content else 'N/A'
    return 'N/A'

def extract_qualifications(soup, tag_name, partial_string, next_tag_stop='h2'):
    """Extracts qualifications listed under the given tag."""
    tag = soup.find(tag_name, string=lambda txt: txt and partial_string.lower() in txt.lower())
    if tag:
        qualifications = []
        for sibling in tag.find_next_siblings():
            if sibling.name == 'ul' and sibling.name != next_tag_stop:
                for li in sibling.find_all('li'):
                    qualifications.append(clean_text(li.text))
        return ' '.join(qualifications) if qualifications else 'N/A'
    return 'N/A'

# ----------------------------------------------------------------------
#                  EXTRACT JOB DETAILS (Returns the Posting)
# ----------------------------------------------------------------------
async def extract_job_details(page, job_posting):
    """
    Extracts detailed job information from the NHS job detail page.
    Returns the updated JobPosting object (does NOT save to DB here).
    """
    try:
        # Navigate to job details
        await safe_page_goto(page, job_posting.job_link, wait_until='domcontentloaded')
        await page.wait_for_selector('main.nhsuk-main-wrapper')

        job_detail_html = await page.content()
        detail_soup = BeautifulSoup(job_detail_html, 'html.parser')
        main_content = detail_soup.find('main', class_='nhsuk-main-wrapper')
        
        if main_content:
            job_posting.job_summary = clean_list(
                extract_tag_text(main_content, 'h3', 'summary')
            )
            job_posting.main_duties = clean_list(
                extract_tag_text(main_content, 'h3', 'duties')
            )
            job_posting.team_structure = clean_list(
                extract_tag_text(main_content, 'h3', 'about us')
            )
            job_posting.qualifications = clean_list(
                extract_qualifications(main_content, 'h2', 'specification')
            )
            job_posting.job_description = clean_list(
                extract_tag_text(main_content, 'h2', 'description')
            )
            job_posting.working_pattern = extract_tag_text(
                main_content, 'h3', 'working pattern'
            )

            name_details = main_content.find('p', id='employer_name_details')
            job_posting.employer_name = clean_text(name_details.text) if name_details else 'N/A'

            address_fields = [
                'employer_address_line_1_a',
                'employer_address_line_2_b',
                'employer_town_c',
                'employer_postcode_e'
            ]
            address_list = []
            for field in address_fields:
                el = main_content.find('p', id=field)
                if el:
                    address_list.append(clean_text(el.text))
            job_posting.employer_address = clean_text(' '.join(address_list)) or 'N/A'
    
            employer_contact_tag = main_content.find('p', id='employer_website_url')
            if employer_contact_tag:
                employer_contact_link = employer_contact_tag.find('a', id='employer_website_url_link')
                job_posting.employer_contact = (
                    clean_text(employer_contact_link['href']) if employer_contact_link else 'N/A'
                )
            else:
                job_posting.employer_contact = 'N/A'
    
            dbs_container = main_content.find('div', id='dbs-container')
            job_posting.disclosure_check = clean_text(dbs_container.text) if dbs_container else 'N/A'
            
            sponsorship_tag = main_content.find('h3', id='tier-two-sponsorship')
            if sponsorship_tag:
                sponsorship_p = sponsorship_tag.find_next('p')
                job_posting.certificate_of_sponsorship = clean_text(sponsorship_p.text) if sponsorship_p else 'N/A'
            else:
                job_posting.certificate_of_sponsorship = 'N/A'

            uk_reg_tag = main_content.find('h3', id='uk-registration')
            if uk_reg_tag:
                uk_reg_p = uk_reg_tag.find_next('p')
                job_posting.uk_registration = clean_text(uk_reg_p.text) if uk_reg_p else 'N/A'
            else:
                job_posting.uk_registration = 'N/A'

            pay_scheme = main_content.find('p', id='payscheme-type')
            job_posting.pay_scheme = clean_text(pay_scheme.text) if pay_scheme else 'None'

            grade = main_content.find('p', id='payscheme-band')
            job_posting.grade = clean_text(grade.text) if grade else 'None'

            duration = main_content.find('p', id='contract_duration')
            job_posting.duration = clean_text(duration.text) if duration else 'None'

            reference_el = main_content.find('p', id='trac-job-reference')
            if reference_el:
                job_posting.reference_number = clean_text(reference_el.text)
            else:
                # Fallback to a generated unique ID
                job_posting.reference_number = generate_unique_id(job_posting)

    except Exception as e:
        logging.error(f"Error extracting details for {job_posting.title}: {e}")

    return job_posting

# ----------------------------------------------------------------------
#               SCRAPE NHS - Only 2 Pages + Single Inserts
# ----------------------------------------------------------------------
async def scrape_jobs_playwright(url, job_search_engine, category, stop_words, considerable_words, browser):
    """
    Scrapes job postings from NHS using Playwright and BeautifulSoup,
    filtering by stop words, limiting to 2 pages, saving each job individually.
    """
    MAX_PAGES = 3
    page_number = 1

    page = await browser.new_page()
    all_job_listings = []  # Keep track of all found jobs if needed

    try:
        while True:
            # 1) Navigate to the page (with retry & domcontentloaded)
            await safe_page_goto(page, url, wait_until='domcontentloaded')
            await page.wait_for_selector('.nhsuk-list.search-results')
            
            logging.info(f"Scraping Page {page_number}...")

            # 2) Parse the listings on this page
            soup = BeautifulSoup(await page.content(), 'html.parser')
            job_elements = soup.find_all('li', class_='nhsuk-list-panel')

            for job in job_elements:
                title_tag = job.find('a', {'data-test': 'search-result-job-title'})
                title = clean_text(title_tag.text) if title_tag else 'N/A'

                # Skip job if it contains a stop word
                if contains_word(title, stop_words):
                    logging.info(f"Skipped job '{title}' (contains stop word)")
                    continue

                # Skip job if no "considerable" words are found
                if not contains_word(title, considerable_words):
                    logging.info(f"Skipped job '{title}' (no considerable words)")
                    continue

                job_link = f"https://www.jobs.nhs.uk{title_tag['href']}" if title_tag else 'N/A'

                location_tag = job.find('div', {'data-test': 'search-result-location'})
                salary_tag = job.find('li', {'data-test': 'search-result-salary'})
                date_posted_tag = job.find('li', {'data-test': 'search-result-publicationDate'})
                closing_date_tag = job.find('li', {'data-test': 'search-result-closingDate'})
                contract_type_tag = job.find('li', {'data-test': 'search-result-jobType'})
                working_pattern_tag = job.find('li', {'data-test': 'search-result-workingPattern'})

                location = clean_text(location_tag.text) if location_tag else 'N/A'
                salary = clean_text(
                    salary_tag.find('strong').text
                ) if salary_tag and salary_tag.find('strong') else 'N/A'
                date_posted = clean_text(
                    date_posted_tag.find('strong').text
                ) if date_posted_tag and date_posted_tag.find('strong') else 'N/A'

                closing_date_raw = clean_text(
                    closing_date_tag.find('strong').text
                ) if closing_date_tag and closing_date_tag.find('strong') else 'N/A'
                closing_date = convert_to_standard_date(closing_date_raw)

                contract_type = clean_text(
                    contract_type_tag.find('strong').text
                ) if contract_type_tag and contract_type_tag.find('strong') else 'N/A'

                working_pattern = clean_text(
                    working_pattern_tag.find('strong').text
                ) if working_pattern_tag and working_pattern_tag.find('strong') else 'N/A'

                # Create the basic JobPosting
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

                # 2a) Extract detailed info
                detailed_job_posting = await extract_job_details(page, job_posting)

                # 2b) Insert each job posting individually
                await save_job_to_db(detailed_job_posting)
                all_job_listings.append(detailed_job_posting)

            logging.info(f"Page {page_number} scraped. Jobs processed: {len(all_job_listings)}")

            # 3) Stop if we reached the max pages
            if page_number >= MAX_PAGES:
                logging.info(f"Reached maximum of {MAX_PAGES} pages. Stopping.")
                break

            # 4) Check if there is a "next page" link
            next_page_tag = soup.find('li', class_='nhsuk-pagination-item--next')
            if next_page_tag:
                next_page_link = next_page_tag.find('a', {'data-test': 'search-next-page'})
                if next_page_link and 'href' in next_page_link.attrs:
                    url = f"https://www.jobs.nhs.uk{next_page_link['href']}"
                    page_number += 1
                else:
                    # No valid next page link
                    break
            else:
                # No pagination item found
                break

    except Exception as e:
        logging.error(f"Error while scraping page {page_number}: {e}")
    finally:
        await page.close()

    return all_job_listings
