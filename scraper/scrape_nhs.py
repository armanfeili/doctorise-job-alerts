import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from scrape_db_utils import JobPosting, save_job_to_db
from scrape_utils import clean_text, clean_list, generate_unique_id

# Helper functions
def clean_text_with_strong_tags(text, tag):
    """Cleans text and adds bold formatting to specific tags."""
    soup = BeautifulSoup(text, 'html.parser')
    for strong_tag in soup.find_all(tag):
        strong_tag.string = f"**{strong_tag.text}**"
    return ' '.join(soup.stripped_strings)

def extract_tag_text(soup, tag_name, partial_string, next_tag_stop='h2', nested_tag='p'):
    """Extracts text under a specified tag and partial string match."""
    tag = soup.find(tag_name, string=lambda text: text and partial_string.lower() in text.lower())
    if tag:
        content = [
            clean_text_with_strong_tags(str(sibling), 'strong')
            for sibling in tag.find_next_siblings()
            if sibling.name == nested_tag and sibling.name != next_tag_stop
        ]
        return clean_text(' '.join(content)) if content else 'N/A'
    return 'N/A'

def extract_qualifications(soup, tag_name, partial_string, next_tag_stop='h2'):
    """Extracts qualifications listed under the given tag."""
    tag = soup.find(tag_name, string=lambda text: text and partial_string.lower() in text.lower())
    if tag:
        qualifications = [
            clean_text(li.text)
            for sibling in tag.find_next_siblings() if sibling.name == 'ul'
            for li in sibling.find_all('li') if sibling.name != next_tag_stop
        ]
        return ' '.join(qualifications) if qualifications else 'N/A'
    return 'N/A'

# Updated async function to extract detailed job information
async def extract_job_details(page, job_posting):
    """Extracts detailed job information from the NHS job detail page."""
    try:
        await page.goto(job_posting.job_link, wait_until='networkidle')
        await page.wait_for_selector('main.nhsuk-main-wrapper')
        job_detail_html = await page.content()
        detail_soup = BeautifulSoup(job_detail_html, 'html.parser')
        main_content = detail_soup.find('main', class_='nhsuk-main-wrapper')
        
        if main_content:
            job_posting.job_summary = clean_list(extract_tag_text(main_content, 'h3', 'summary'))
            job_posting.main_duties = clean_list(extract_tag_text(main_content, 'h3', 'duties'))
            job_posting.team_structure = clean_list(extract_tag_text(main_content, 'h3', 'about us'))
            job_posting.qualifications = clean_list(extract_qualifications(main_content, 'h2', 'specification'))
            job_posting.job_description = clean_list(extract_tag_text(main_content, 'h2', 'description'))
            job_posting.working_pattern = extract_tag_text(main_content, 'h3', 'working pattern')
            
            job_posting.employer_name = clean_text(main_content.find('p', id='employer_name_details').text) if main_content.find('p', id='employer_name_details') else 'N/A'

            address_fields = ['employer_address_line_1_a', 'employer_address_line_2_b', 'employer_town_c', 'employer_postcode_e']
            job_posting.employer_address = clean_text(' '.join([
                clean_text(main_content.find('p', id=field).text or '')
                for field in address_fields if main_content.find('p', id=field)
            ])) or 'N/A'
    
            employer_contact_tag = main_content.find('p', id='employer_website_url')
            if employer_contact_tag:
                employer_contact_link = employer_contact_tag.find('a', id='employer_website_url_link')
                job_posting.employer_contact = clean_text(employer_contact_link['href']) if employer_contact_link else 'N/A'
            else:
                job_posting.employer_contact = 'N/A'
    
            job_posting.disclosure_check = clean_text(main_content.find('div', id='dbs-container').text if main_content.find('div', id='dbs-container') else 'N/A')
            job_posting.certificate_of_sponsorship = clean_text(main_content.find('h3', id='tier-two-sponsorship').find_next('p').text if main_content.find('h3', id='tier-two-sponsorship') else 'N/A')
            job_posting.uk_registration = clean_text(main_content.find('h3', id='uk-registration').find_next('p').text if main_content.find('h3', id='uk-registration') else 'N/A')
            job_posting.pay_scheme = clean_text(main_content.find('p', id='payscheme-type').text if main_content.find('p', id='payscheme-type') else 'None')
            job_posting.grade = clean_text(main_content.find('p', id='payscheme-band').text if main_content.find('p', id='payscheme-band') else 'None')
            job_posting.duration = clean_text(main_content.find('p', id='contract_duration').text if main_content.find('p', id='contract_duration') else 'None')
            job_posting.reference_number = clean_text(main_content.find('p', id='trac-job-reference').text if main_content.find('p', id='trac-job-reference') else generate_unique_id(job_posting))

            # Save the job posting to the database
            await save_job_to_db(job_posting)
            
    except Exception as e:
        logging.error(f"Error extracting details for {job_posting.title}: {e}")

# Async function to scrape jobs from NHS
async def scrape_jobs_playwright(url, job_search_engine, category):
    """Scrapes job postings from NHS using Playwright and BeautifulSoup."""
    job_listings = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page_number = 1
        
        try:
            while True:
                await page.goto(url)
                await page.wait_for_selector('.nhsuk-list.search-results')
                soup = BeautifulSoup(await page.content(), 'html.parser')
                job_elements = soup.find_all('li', class_='nhsuk-list-panel')
                logging.info(f"Scraping Page {page_number} started.")

                for job in job_elements:
                    title_tag = job.find('a', {'data-test': 'search-result-job-title'})
                    title = clean_text(title_tag.text) if title_tag else 'N/A'
                    job_link = f"https://www.jobs.nhs.uk{title_tag['href']}" if title_tag else 'N/A'
                    location = clean_text(job.find('div', {'data-test': 'search-result-location'}).text or 'N/A')
                    salary = clean_text(job.find('li', {'data-test': 'search-result-salary'}).find('strong').text or 'N/A')
                    date_posted = clean_text(job.find('li', {'data-test': 'search-result-publicationDate'}).find('strong').text or 'N/A')
                    closing_date = clean_text(job.find('li', {'data-test': 'search-result-closingDate'}).find('strong').text or 'N/A')
                    contract_type = clean_text(job.find('li', {'data-test': 'search-result-jobType'}).find('strong').text or 'N/A')
                    working_pattern = clean_text(job.find('li', {'data-test': 'search-result-workingPattern'}).find('strong').text or 'N/A')

                    # Create JobPosting object
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

                    # Extract detailed information
                    await extract_job_details(page, job_posting)
                    job_listings.append(job_posting)

                logging.info(f"Page {page_number} scraped.")

                # Handle pagination
                next_page_tag = soup.find('li', class_='nhsuk-pagination-item--next')
                if next_page_tag:
                    next_page_link = next_page_tag.find('a', {'data-test': 'search-next-page'})
                    if next_page_link and 'href' in next_page_link.attrs:
                        url = f"https://www.jobs.nhs.uk{next_page_link['href']}"
                        page_number += 1
                    else:
                        break
                else:
                    break

        except Exception as e:
            logging.error(f"Error while scraping page {page_number}: {e}")
        finally:
            await browser.close()

    return job_listings
