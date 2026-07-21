import urllib.robotparser
import time
import random
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from logger import get_logger

logger = get_logger("custom_scraper")


class EthicalScraper:
    def __init__(self):
        self.rp = urllib.robotparser.RobotFileParser()
        self.parsed_robots = set()
        
        # Setup headless Selenium for JS-heavy sites
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=JobMatch-Bot/1.0 (+https://jobsmatch.streamlit.app)")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=chrome_options
        )

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if robots.txt allows scraping this URL."""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        if base_url not in self.parsed_robots:
            robots_url = f"{base_url}/robots.txt"
            self.rp.set_url(robots_url)
            try:
                self.rp.read()
            except Exception as e:
                logger.warning(f"Could not read robots.txt from {base_url}: {e}")
            self.parsed_robots.add(base_url)
            
        return self.rp.can_fetch(user_agent, url)

    def random_delay(self, min_seconds: float = 3.0, max_seconds: float = 7.0):
        """Pause to avoid overwhelming the server."""
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Ethical scraping delay: sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    def fetch_soup(self, url: str) -> BeautifulSoup:
        """Fetches a page using Selenium and parses with BeautifulSoup."""
        if not self.can_fetch(url):
            logger.error(f"Scraping denied by robots.txt for URL: {url}")
            return None
            
        self.random_delay()
        logger.info(f"Fetching URL via Selenium: {url}")
        
        try:
            self.driver.get(url)
            # Wait for basic JS rendering if necessary
            time.sleep(2)
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            return soup
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return None

    def close(self):
        """Close the Selenium browser."""
        if self.driver:
            self.driver.quit()


# Example Usage (Can be integrated with daily_fetch.py later)
if __name__ == "__main__":
    scraper = EthicalScraper()
    test_url = "https://www.example.com"
    soup = scraper.fetch_soup(test_url)
    if soup:
        print("Page title:", soup.title.string if soup.title else "No title")
    scraper.close()
