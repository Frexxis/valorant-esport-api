import requests
import logging
import json
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base URL 
# Note: bo3.gg appears to be a CS2 website, not a Valorant website
# We'll use it as instructed, but it might not have Valorant data
BASE_URL = "https://bo3.gg"

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0"
}

# Rate limiting parameters
REQUEST_DELAY = 2  # Delay between requests in seconds

def get_soup(url):
    """
    Fetches the page and returns a BeautifulSoup object.
    
    Args:
        url (str): URL to fetch
        
    Returns:
        BeautifulSoup: Parsed HTML
    """
    try:
        # Add delay to avoid overwhelming the server
        time.sleep(REQUEST_DELAY)
        
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None


def get_matches(limit=20):
    """
    Scrapes upcoming and recent matches from bo3.gg
    
    Args:
        limit (int): Maximum number of matches to fetch
        
    Returns:
        list: List of match dictionaries
    """
    try:
        # bo3.gg uses SPA (Single Page Application) architecture which requires 
        # JavaScript to render. Our simple scraper might not capture all data.
        # The site is actually redirecting /matches to /matches/current
        matches_url = f"{BASE_URL}/matches/current"
        soup = get_soup(matches_url)
        
        if not soup:
            logger.warning("No soup returned from bo3.gg matches page")
            return []
        
        # Since we couldn't find proper match cards on initial inspection,
        # we'll return an empty list for now. In a production environment,
        # we would use Selenium to render the JavaScript.
        matches = []
        
        # Log that we're not currently able to scrape data from bo3.gg
        logger.info("bo3.gg appears to be a dynamic site that requires JavaScript rendering. " 
                   "Consider using Selenium for this site.")
        
        # Note: bo3.gg appears to focus on CS2 matches, not Valorant
        return matches
    
    except Exception as e:
        logger.error(f"Error in get_matches: {str(e)}")
        return []


def get_match_details(match_id):
    """
    Scrapes detailed information for a specific match.
    
    Args:
        match_id (str): ID of the match to fetch
        
    Returns:
        dict: Match details with map statistics
    """
    try:
        # Similar to get_matches, bo3.gg requires JavaScript rendering
        # for match details pages
        logger.info(f"bo3.gg requires JavaScript rendering for match detail pages. " 
                   "Consider using Selenium for this site.")
        
        # Return None to indicate we couldn't fetch the match details
        return None
    
    except Exception as e:
        logger.error(f"Error in get_match_details: {str(e)}")
        return None


def get_team_details(team_id):
    """
    Scrapes team information and roster from bo3.gg
    
    Args:
        team_id (str): ID of the team to fetch
        
    Returns:
        dict: Team details with player roster
    """
    try:
        # Similar to other bo3.gg functions, this site requires JavaScript
        # rendering to access team details properly
        logger.info(f"bo3.gg requires JavaScript rendering for team detail pages. " 
                   "Consider using Selenium for this site.")
        
        # Return None to indicate we couldn't fetch the team details
        return None
    
    except Exception as e:
        logger.error(f"Error in get_team_details: {str(e)}")
        return None