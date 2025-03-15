import asyncio
import logging
from scrape_nhs import scrape_jobs_playwright as scrape_nhs_jobs
from scrape_nhs_scot import scrape_jobs_playwright as scrape_nhs_scot_jobs
from scrape_healthjobsuk import scrape_jobs_playwright as scrape_healthjobsuk_jobs
from scrape_utils import medical_stop_words, medical_considerable
from playwright.async_api import async_playwright

# Set up logging
logging.basicConfig(level=logging.INFO)

# Increase concurrency to 3
sem = asyncio.Semaphore(3)

async def scrape_with_semaphore(
    url, scraper_function, job_search_engine, category, stop_words, considerable_words, browser
):
    """
    Small wrapper that ensures we only scrape `url` when the semaphore is available,
    thus limiting concurrency to sem's value.
    """
    async with sem:
        logging.info(f"Scraping {url} with concurrency limit (up to 3).")
        return await scraper_function(
            url,
            job_search_engine,
            category,
            stop_words,
            considerable_words,
            browser
        )

# Generic scraping function to handle different sources with error handling
async def run_scraper(scraper_function, urls, job_search_engine, category, stop_words, considerable_words, browser):
    """Runs a scraping task (for multiple URLs) with error handling."""
    try:
        logging.info(f"{job_search_engine} scraping started")
        return await scrape_and_process_jobs(
            urls, scraper_function, job_search_engine, category,
            stop_words, considerable_words, browser
        )
    except Exception as e:
        logging.error(f"Error scraping {job_search_engine}: {e}")
        return []

# Generic function to scrape and process jobs
async def scrape_and_process_jobs(urls, scraper_function, job_search_engine, category, stop_words, considerable_words, browser):
    """Scrapes and processes all job postings from the given URLs in parallel."""
    tasks = []
    for url in urls:
        # Create a separate task for each URL, limited by the semaphore
        tasks.append(asyncio.create_task(
            scrape_with_semaphore(
                url, scraper_function, job_search_engine, category,
                stop_words, considerable_words, browser
            )
        ))

    # Gather results in parallel. Each task returns the list of jobs for that URL.
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten any partial results, ignoring failed tasks
    all_jobs = []
    for item in results:
        # If a task raised an exception, item will be that exception object
        if isinstance(item, list):
            all_jobs.extend(item)
        elif isinstance(item, Exception):
            logging.error(f"Task raised exception: {item}")

    logging.info(f"Scraping from {job_search_engine} completed.")
    return all_jobs

# Main function to scrape jobs from multiple sources
async def main():
    nhs_urls = [
        "https://www.jobs.nhs.uk/candidate/search/results?staffGroup=MEDICAL_AND_DENTAL&payRange=40-50%2C50-60%2C60-70&searchFormType=sortBy&sort=publicationDateDesc&language=en"
    ]

    # "https://www.jobs.nhs.uk/candidate/search/results?keyword=FY2,%20CT1,%20CT2,%20ST1,%20ST2,%20ST3,%20LAS,%20Trust%20doctor,%20Trust%20grade&payBand=SPECIALTY_DOCTOR,FOUNDATION_DOCTOR,DOCTOR_OTHER&payRange=30-40,40-50&skipPhraseSuggester=true&searchFormType=sortBy&sort=publicationDateDesc&language=en",
    # "https://www.jobs.nhs.uk/candidate/search/results?keyword=Clinical%20fellow,%20SHO,%20Junior%20Clinical%20fellow,%20teaching%20fellow,%20Academic%20follow&payBand=SPECIALTY_DOCTOR,FOUNDATION_DOCTOR,DOCTOR_OTHER&payRange=30-40,40-50&skipPhraseSuggester=true&searchFormType=sortBy&sort=publicationDateDesc&language=en"
    
    # nhs_scot_urls = [
    #     "https://apply.jobs.scot.nhs.uk/Home/Job"
    # ]


    healthjobsuk_urls = [
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=447&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=&_srt=startdate&_sd=d",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=441&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=&_srt=startdate&_sd=d",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=540&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=&_srt=startdate&_sd=d",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=55&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=&_srt=startdate&_sd=d",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=255&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=&_srt=startdate&_sd=d",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=534&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=&_srt=startdate&_sd=d",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=84&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=&_srt=startdate&_sd=d",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=444&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=&_srt=startdate&_sd=d",
        "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=7033239&_srt=startdate&_sd=d"
    ]

    # Initialize Playwright and share the browser instance across all tasks
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        while True:
            logging.info("Starting scraping process...")

            # Option 1: Keep the two sources sequential if you wish:
            # -----------------------------------------------------
            # await run_scraper(scrape_nhs_jobs, nhs_urls, "NHS Jobs", "Medical", medical_stop_words, medical_considerable, browser)
            # await run_scraper(scrape_healthjobsuk_jobs, healthjobsuk_urls, "Health Jobs UK", "Medical", medical_stop_words, medical_considerable, browser)

            # OR

            # Option 2: Run both sources fully in parallel:
            # -----------------------------------------------------
            tasks = [
                asyncio.create_task(
                    run_scraper(
                        scrape_nhs_jobs, nhs_urls, "NHS Jobs", "Medical",
                        medical_stop_words, medical_considerable, browser
                    )
                ),
                asyncio.create_task(
                    run_scraper(
                        scrape_healthjobsuk_jobs, healthjobsuk_urls, "Health Jobs UK", "Medical",
                        medical_stop_words, medical_considerable, browser
                    )
                )
            ]
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
