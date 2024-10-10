import time
import asyncio
import logging
from scrape_db_utils import init_db
from scrape_nhs import scrape_jobs_playwright as scrape_nhs_jobs
from scrape_nhs_scot import scrape_jobs_playwright as scrape_nhs_scot_jobs
from scrape_healthjobsuk import scrape_jobs_playwright as scrape_healthjobsuk_jobs

# Import the stop words from scrape_utils
from scrape_utils import medical_stop_words, medical_considerable

# Set up logging
logging.basicConfig(level=logging.INFO)

# Generic scraping function to handle different sources with interval
async def run_scraper(scraper_function, urls, job_search_engine, category, interval, stop_words, considarable_words):
    """Runs a scraping task every 'interval' seconds, with error handling and stop words filtering."""
    while True:
        try:
            logging.info(f"{job_search_engine} scraping started")
            await scrape_and_process_jobs(urls, scraper_function, job_search_engine, category, stop_words, considarable_words)
        except Exception as e:
            logging.error(f"Error scraping {job_search_engine}: {e}")
        finally:
            logging.info(f"{job_search_engine} scraping finished. Waiting {interval} seconds for the next run.")
            await asyncio.sleep(interval)

# Generic function to scrape and process jobs
async def scrape_and_process_jobs(urls, scraper_function, job_search_engine, category, stop_words, considarable_words):
    """Scrapes and processes job postings from given URLs."""
    await init_db()  # Ensure the database is initialized before scraping
    start_time = time.time()
    all_jobs = []
    
    for url in urls:
        try:
            logging.info(f"Scraping jobs from {url} ({job_search_engine})")
            jobs = await scraper_function(url, job_search_engine, category, stop_words, considarable_words)
            all_jobs.extend(jobs)
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
    
    elapsed_time = time.time() - start_time
    logging.info(f"Scraping from {job_search_engine} completed in {elapsed_time:.2f} seconds")
    return all_jobs

# Main function to scrape jobs from multiple sources independently
async def main():
    nhs_urls = [
        "https://www.jobs.nhs.uk/candidate/search/results?keyword=FY2,%20CT1,%20CT2,%20ST1,%20ST2,%20ST3,%20LAS,%20Trust%20doctor,%20Trust%20grade&payBand=SPECIALTY_DOCTOR,FOUNDATION_DOCTOR,DOCTOR_OTHER&payRange=30-40,40-50&skipPhraseSuggester=true&searchFormType=sortBy&sort=publicationDateDesc&language=en",
        "https://www.jobs.nhs.uk/candidate/search/results?keyword=Clinical%20fellow,%20SHO,%20Junior%20Clinical%20fellow,%20teaching%20fellow,%20Academic%20follow&payBand=SPECIALTY_DOCTOR,FOUNDATION_DOCTOR,DOCTOR_OTHER&payRange=30-40,40-50&skipPhraseSuggester=true&searchFormType=sortBy&sort=publicationDateDesc&language=en"
    ]
    
    nhs_scot_urls = [
        "https://apply.jobs.scot.nhs.uk/Home/Job"
    ]

    healthjobsuk_urls = [
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=447&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=17512&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=441&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=24047&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=540&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=27829&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=55&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=30273&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=255&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=32987&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=534&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=41095&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=84&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=44801&_srt=startdate&_sd=a",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=444&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=47883&_srt=startdate&_sd=a"
    ]
    
    # Run all scraping tasks independently with a 5-minute (300 seconds) interval
    # add await before run_scraper to make them running sequentially, not concurrently.
    nhs_task = run_scraper(scrape_nhs_jobs, nhs_urls, "NHS Jobs", "Medical", 300, medical_stop_words, medical_considerable)
    nhs_scot_task = run_scraper(scrape_nhs_scot_jobs, nhs_scot_urls, "NHS Scotland", "Medical", 300, medical_stop_words, medical_considerable)
    healthjobsuk_task = run_scraper(scrape_healthjobsuk_jobs, healthjobsuk_urls, "Health Jobs UK", "Medical", 300, medical_stop_words, medical_considerable)

    # Run all tasks concurrently
    await asyncio.gather(nhs_task, nhs_scot_task, healthjobsuk_task)

if __name__ == "__main__":
    asyncio.run(main())
