import asyncio
import logging
from scrape_nhs import scrape_jobs_playwright as scrape_nhs_jobs
from scrape_nhs_scot import scrape_jobs_playwright as scrape_nhs_scot_jobs
from scrape_healthjobsuk import scrape_jobs_playwright as scrape_healthjobsuk_jobs
from scrape_utils import medical_stop_words, medical_considerable
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)

async def scrape_with_semaphore(
    url, scraper_function, job_search_engine, category, stop_words, considerable_words, browser, sem
):
    """
    Only scrape 'url' when the semaphore is available, ensuring 
    we don't exceed the concurrency limit.
    """
    async with sem:
        logging.info(f"Scraping {url} with concurrency limit.")
        return await scraper_function(
            url,
            job_search_engine,
            category,
            stop_words,
            considerable_words,
            browser
        )

async def run_scraper(scraper_function, urls, job_search_engine, category, 
                      stop_words, considerable_words, browser, sem):
    """Runs a scraping task (for multiple URLs) with error handling."""
    try:
        logging.info(f"{job_search_engine} scraping started.")
        return await scrape_and_process_jobs(
            urls, scraper_function, job_search_engine, category,
            stop_words, considerable_words, browser, sem
        )
    except Exception as e:
        logging.error(f"Error scraping {job_search_engine}: {e}")
        return []

async def scrape_and_process_jobs(urls, scraper_function, job_search_engine, 
                                  category, stop_words, considerable_words, 
                                  browser, sem):
    """Scrapes all job postings from the given URLs in parallel."""
    tasks = []
    for url in urls:
        tasks.append(
            asyncio.create_task(
                scrape_with_semaphore(
                    url, scraper_function, job_search_engine, category,
                    stop_words, considerable_words, browser, sem
                )
            )
        )

    # Gather results in parallel. Each task returns a list of jobs or an exception.
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten results, handle any exceptions
    all_jobs = []
    for item in results:
        if isinstance(item, list):
            all_jobs.extend(item)
        elif isinstance(item, Exception):
            logging.error(f"Task raised exception: {item}")

    logging.info(f"Scraping from {job_search_engine} completed.")
    return all_jobs

async def main():
    # Place the semaphore inside main so it's tied to this event loop
    sem = asyncio.Semaphore(9)

    nhs_urls = [
        "https://www.jobs.nhs.uk/candidate/search/results?staffGroup=MEDICAL_AND_DENTAL&payRange=40-50%2C50-60%2C60-70&searchFormType=sortBy&sort=publicationDateDesc&language=en"
    ]

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
    
    # Be sure that the following link works during the week. it should be the first Medical and Dental link to covid-19
    # "https://www.healthjobsuk.com/job_list?JobSearch_q=&JobSearch_d=&JobSearch_g=&JobSearch_re=_POST&JobSearch_re_0=1&JobSearch_re_1=1-_-_-&JobSearch_re_2=1-_-_--_-_-&JobSearch_Submit=Search&_tr=JobSearch&_ts=116013"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        logging.info("Starting scraping process...")

        # Example: Run both sources in parallel
        tasks = [
            asyncio.create_task(
                run_scraper(
                    scrape_nhs_jobs, nhs_urls, "NHS Jobs", "Medical",
                    medical_stop_words, medical_considerable, browser, sem
                )
            ),
            asyncio.create_task(
                run_scraper(
                    scrape_healthjobsuk_jobs, healthjobsuk_urls, "Health Jobs UK", "Medical",
                    medical_stop_words, medical_considerable, browser, sem
                )
            )
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Run the main function in a single event loop
    asyncio.run(main())
