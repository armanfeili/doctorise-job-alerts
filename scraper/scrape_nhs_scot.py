import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from scrape_db_utils import JobPosting, save_job_to_db
from scrape_utils import clean_text, generate_unique_id

# Updated async function to extract detailed job information from the job detail page
async def extract_job_details(page, job_posting):
    try:
        await page.goto(job_posting.job_link, wait_until='networkidle')
        
        # Wait for job details to load
        await page.wait_for_selector('.col-md-12.mt-2')

        job_detail_html = await page.content()
        detail_soup = BeautifulSoup(job_detail_html, 'html.parser')

        # Extract details
        job_posting.job_description = clean_text(detail_soup.find('div', class_='JT-container').text) if detail_soup.find('div', class_='JT-container') else 'N/A'
        job_posting.contract_type = clean_text(detail_soup.find('strong', class_='closing-date', string='Employment type:').find_next('span').text) if detail_soup.find('strong', class_='closing-date', string='Employment type:') else 'N/A'
        job_posting.qualifications = ' | '.join([clean_text(li.text) for li in detail_soup.find('h3', text="What we'll need you to bring").find_next('ul').find_all('li')]) if detail_soup.find('h3', text="What we'll need you to bring") else 'N/A'
        job_posting.working_pattern = clean_text(detail_soup.find('h3', text='Location and Working Pattern').find_next('p').text) if detail_soup.find('h3', text='Location and Working Pattern') else 'N/A'
        job_posting.employer_contact = clean_text(detail_soup.find('strong', text='Please contact').find_next('p').text) if detail_soup.find('strong', text='Please contact') else 'N/A'

        # Save job to database
        await save_job_to_db(job_posting)

    except Exception as e:
        logging.error(f"Error extracting details for {job_posting.title}: {e}")

# Async function to scrape jobs from NHS Scotland
async def scrape_jobs_playwright(url, job_search_engine, category):
    job_listings = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page_number = 1

        try:
            while True:
                await page.goto(url)
                await page.wait_for_selector('.job-search__results-items')
                soup = BeautifulSoup(await page.content(), 'html.parser')
                job_elements = soup.find_all('div', class_='job-card')

                logging.info(f"Scraping Page {page_number} started.")

                for job in job_elements:
                    title_tag = job.find('a')
                    title = clean_text(title_tag.text) if title_tag else 'N/A'
                    job_link = f"https://apply.jobs.scot.nhs.uk{title_tag['href']}" if title_tag else 'N/A'

                    # Extract details
                    details_section = job.find('div', class_='job-card__description')
                    reference = clean_text(details_section.find('p', class_='jobreference').text.replace('Job reference:', '').strip()) if details_section.find('p', class_='jobreference') else generate_unique_id(title)
                    salary = clean_text(details_section.find('p', class_='salary').text.replace('Salary:', '').strip()) if details_section.find('p', class_='salary') else 'N/A'
                    closing_date = clean_text(details_section.find('p', class_='closingdate').text.replace('Closing date:', '').strip()) if details_section.find('p', class_='closingdate') else 'N/A'
                    location = clean_text(details_section.find('p', class_='location').text.replace('Location:', '').strip()) if details_section.find('p', class_='location') else 'N/A'
                    employment_type = clean_text(details_section.find('p', class_='employmenttype').text.replace('Employment type:', '').strip()) if details_section.find('p', class_='employmenttype') else 'N/A'
                    hours_per_week = clean_text(details_section.find('p', class_='hours').text.replace('Hours per week:', '').strip()) if details_section.find('p', class_='hours') else 'N/A'
                    live_date = clean_text(details_section.find('p', class_='livedate').text.replace('Live date:', '').strip()) if details_section.find('p', class_='livedate') else 'N/A'
                    employer = clean_text(details_section.find('p', class_='school').text.replace('Employer (NHS Board):', '').strip()) if details_section.find('p', class_='school') else 'N/A'

                    # Create JobPosting object
                    job_posting = JobPosting(
                        job_search_engine=job_search_engine,
                        category=category,
                        title=title,
                        location=location,
                        salary=salary,
                        date_posted=live_date,
                        closing_date=closing_date,
                        contract_type=employment_type,
                        working_pattern=hours_per_week,
                        job_link=job_link
                    )

                    job_posting.reference_number = reference
                    job_posting.employer_name = employer

                    # Extract more details from job detail page
                    await extract_job_details(page, job_posting)
                    job_listings.append(job_posting)

                logging.info(f"Page {page_number} scraped.")

                # Handle pagination
                next_page_tag = soup.find('a', class_='next-page')
                if next_page_tag:
                    url = f"https://apply.jobs.scot.nhs.uk{next_page_tag['href']}"
                    page_number += 1
                else:
                    break

        except Exception as e:
            logging.error(f"Error while scraping page {page_number}: {e}")
        finally:
            await browser.close()

    return job_listings
