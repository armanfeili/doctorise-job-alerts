import time
import asyncio
import logging
from scrape_db_utils import init_db
from scrape_nhs import scrape_jobs_playwright as scrape_nhs_jobs
from scrape_nhs_scot import scrape_jobs_playwright as scrape_nhs_scot_jobs
from scrape_healthjobsuk import scrape_jobs_playwright as scrape_healthjobsuk_jobs

# Set up logging
logging.basicConfig(level=logging.INFO)

# Generic scraping function to handle different sources
async def scrape_and_process_jobs(urls, scraper_function, job_search_engine, category):
    """Scrapes and processes job postings from given URLs."""
    await init_db()  # Ensure the database is initialized before scraping
    start_time = time.time()
    all_jobs = []
    
    for url in urls:
        try:
            logging.info(f"Scraping jobs from {url} ({job_search_engine})")
            jobs = await scraper_function(url, job_search_engine, category)
            all_jobs.extend(jobs)
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
    
    elapsed_time = time.time() - start_time
    logging.info(f"Scraping from {job_search_engine} completed in {elapsed_time:.2f} seconds")
    return all_jobs

# Main function to scrape jobs from multiple sources
async def main():
    nhs_urls = [
        "https://www.jobs.nhs.uk/candidate/search/results?keyword=FY2,%20CT1,%20CT2,%20ST1,%20ST2,%20ST3,%20LAS,%20Trust%20doctor,%20Trust%20grade&payBand=SPECIALTY_DOCTOR,FOUNDATION_DOCTOR,DOCTOR_OTHER&payRange=30-40,40-50&skipPhraseSuggester=true&searchFormType=sortBy&sort=publicationDateDesc&language=en",
        "https://www.jobs.nhs.uk/candidate/search/results?keyword=Clinical%20fellow,%20SHO,%20Junior%20Clinical%20fellow,%20teaching%20fellow,%20Academic%20follow&payBand=SPECIALTY_DOCTOR,FOUNDATION_DOCTOR,DOCTOR_OTHER&payRange=30-40,40-50&skipPhraseSuggester=true&searchFormType=sortBy&sort=publicationDateDesc&language=en"
    ]
    
    nhs_scot_urls = [
        "https://apply.jobs.scot.nhs.uk/Home/Job"
    ]

    healthjobsuk_urls = [
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=447&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=8949&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=441&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=43989&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=55&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=49392&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=534&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=72609&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=444&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=135577&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=540&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=143218&_srt=startdate&_sd=a"
    ]

    # Infinite loop for continuous scraping with delays
    while True:
        try:
            logging.info("NHS scraping started")
            await scrape_and_process_jobs(nhs_urls, scrape_nhs_jobs, "NHS", "Medical")
            await asyncio.sleep(75)

            logging.info("NHS Scotland scraping started")
            await scrape_and_process_jobs(nhs_scot_urls, scrape_nhs_scot_jobs, "NHS_Scotland", "Medical")
            await asyncio.sleep(75)

            logging.info("HealthJobsUK scraping started")
            await scrape_and_process_jobs(healthjobsuk_urls, scrape_healthjobsuk_jobs, "HealthJobsUK", "Medical")
            await asyncio.sleep(75)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            logging.info("Terminating scraping process. Restarting in 2 minutes...")
            await asyncio.sleep(120)  # Delay before restarting the loop

if __name__ == "__main__":
    asyncio.run(main())
