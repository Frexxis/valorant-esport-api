import requests
import logging
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base URL
BASE_URL = "https://www.vlr.gg"

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

def get_player_details(player_id):
    """
    Scrapes detailed information for a specific player.
    
    Args:
        player_id (str): ID of the player to fetch
        
    Returns:
        dict: Player details with statistics
    """
    try:
        player_url = f"{BASE_URL}/player/{player_id}"
        soup = get_soup(player_url)
        
        if not soup or "Page not found" in soup.text:
            logger.warning(f"Player page not found: {player_id}")
            return None
        
        # Extract player name
        # Try different selectors for player name
        player_name_elem = soup.select_one('.player-header-name h2')
        
        if not player_name_elem:
            player_name_elem = soup.select_one('.wf-title')
        
        if not player_name_elem:
            player_name_elem = soup.select_one('h1.header-title')
        
        player_name = player_name_elem.text.strip() if player_name_elem else None
        
        # If still no name, try to extract from title
        if not player_name:
            title_elem = soup.select_one('title')
            if title_elem:
                title_text = title_elem.text.strip()
                if ':' in title_text:
                    player_name = title_text.split(':')[0].strip()
        
        if not player_name:
            logger.warning(f"Could not find player name for: {player_id}")
            return None
        
        # Extract player team
        team_id = None
        team_name = None
        team_elem = soup.select_one('.player-header-team a')
        
        if team_elem:
            team_name = team_elem.text.strip()
            team_link = team_elem.get('href')
            if team_link:
                team_id = team_link.split('/')[-1]
        
        # Extract player role
        role = None
        role_elem = soup.select_one('.player-role')
        if role_elem:
            role = role_elem.text.strip()
        
        # Extract player country
        country = None
        country_elem = soup.select_one('.player-country')
        if country_elem:
            country = country_elem.text.strip()
        
        # Extract player statistics
        stats = {}
        
        # Recent performance
        recent_stats_container = soup.select_one('.player-header-stats-container')
        if recent_stats_container:
            stat_items = recent_stats_container.select('.stat-item')
            for stat_item in stat_items:
                label_elem = stat_item.select_one('.stat-label')
                value_elem = stat_item.select_one('.stat-value')
                
                if label_elem and value_elem:
                    label = label_elem.text.strip().lower()
                    value = value_elem.text.strip()
                    stats[label] = value
        
        # Match history
        match_history = []
        match_rows = soup.select('.mod-table tbody tr')
        
        for match_row in match_rows[:10]:  # Limit to 10 most recent matches
            try:
                date_elem = match_row.select_one('.mod-date')
                event_elem = match_row.select_one('.mod-event')
                match_elem = match_row.select_one('.mod-match a')
                team1_elem = match_row.select_one('.mod-team-a')
                team2_elem = match_row.select_one('.mod-team-b')
                score_elem = match_row.select_one('.mod-score')
                
                if not match_elem:
                    continue
                
                match_url = match_elem.get('href')
                match_id = match_url.split('/')[-1] if match_url else None
                
                match_data = {
                    'date': date_elem.text.strip() if date_elem else None,
                    'event': event_elem.text.strip() if event_elem else None,
                    'match_id': match_id,
                    'team1': team1_elem.text.strip() if team1_elem else None,
                    'team2': team2_elem.text.strip() if team2_elem else None,
                    'score': score_elem.text.strip() if score_elem else None
                }
                
                match_history.append(match_data)
            except Exception as e:
                logger.error(f"Error parsing match: {str(e)}")
                continue
        
        # Add match history to stats
        stats['match_history'] = match_history
        
        # Create player object
        player_details = {
            'id': player_id,
            'name': player_name,
            'team_id': team_id,
            'team_name': team_name,
            'role': role,
            'country': country,
            'stats': stats
        }
        
        return player_details
    
    except Exception as e:
        logger.error(f"Error in get_player_details: {str(e)}")
        return None

def get_team_players(team_id):
    """
    Scrapes player information for all players in a team.
    
    Args:
        team_id (str): ID of the team to fetch players for
        
    Returns:
        list: List of player dictionaries
    """
    try:
        # Check if team_id is numeric or has a prefix
        if team_id.isdigit() or '/' in team_id:
            team_url = f"{BASE_URL}/team/{team_id}"
        else:
            # Try with a numeric ID '2' for Sentinels as a fallback
            team_url = f"{BASE_URL}/team/2/{team_id}"
        
        logger.info(f"Trying to fetch team from URL: {team_url}")
        soup = get_soup(team_url)
        
        if not soup or "Page not found" in soup.text:
            logger.warning(f"Team page not found: {team_id}")
            return []
        
        players = []
        
        # Find the roster section - there are different HTML structures on the site
        roster_container = None
        
        # First try to find the modern layout with wf-card
        roster_card = soup.select_one('.wf-card')
        if roster_card:
            # Some team pages have multiple cards, look for the one with "players" label
            player_labels = roster_card.select('.wf-module-label')
            for label in player_labels:
                if 'players' in label.text.lower():
                    # Found the players section
                    parent_div = label.find_parent('div')
                    if parent_div:
                        roster_container = parent_div
                        break
        
        # If not found yet, try other common container selectors
        if not roster_container:
            roster_container = soup.select_one('.wf-card.mod-roster')
        
        if not roster_container:
            roster_container = soup.select_one('.team-roster-container')
            
        if not roster_container:
            # Look for any div containing roster items
            roster_items = soup.select('.team-roster-item')
            if roster_items and len(roster_items) > 0:
                roster_container = roster_items[0].find_parent('div')
        
        if not roster_container:
            logger.warning(f"Could not find roster section for team: {team_id}")
            return []
        
        # Extract player cards - different sites use different class names
        player_cards = roster_container.select('.wf-module-item') or roster_container.select('.team-roster-item')
        
        # If still no player cards, try finding them directly in the entire document
        if not player_cards:
            player_cards = soup.select('.team-roster-item')
        
        logger.info(f"Found {len(player_cards)} player cards for team: {team_id}")
        
        for player_card in player_cards:
            try:
                player_link = player_card.select_one('a')
                if not player_link:
                    continue
                
                player_url = player_link.get('href')
                
                if not player_url:
                    continue
                    
                # Normalize the URL
                if isinstance(player_url, str) and not player_url.startswith('http'):
                    player_url = urljoin(BASE_URL, player_url)
                
                # Extract player ID from URL
                player_id = None
                if isinstance(player_url, str):
                    if '/player/' in player_url:
                        parts = player_url.split('/player/')
                        if len(parts) > 1:
                            id_parts = parts[1].split('/')
                            if len(id_parts) > 0:
                                player_id = id_parts[0]
                    else:
                        # Try to extract ID in another way
                        parts = player_url.split('/')
                        if len(parts) > 0:
                            player_id = parts[-1]
                
                if not player_id:
                    logger.warning(f"Could not extract player ID from URL: {player_url}")
                    continue
                
                # Extract player name
                name_elem = player_card.select_one('.mod-player') or player_card.select_one('.text-of')
                if not name_elem:
                    name_elem = player_card.select_one('.team-roster-item-name')
                
                player_name = name_elem.text.strip() if name_elem else None
                
                if not player_name:
                    continue
                
                # Extract player role
                role_elem = player_card.select_one('.mod-role') or player_card.select_one('.team-roster-item-role')
                role = role_elem.text.strip() if role_elem else None
                
                # Extract player country
                country_elem = player_card.select_one('.mod-flag') or player_card.select_one('.team-roster-item-country')
                country = country_elem.text.strip() if country_elem else None
                
                # Create player object
                player = {
                    'id': player_id,
                    'name': player_name,
                    'team_id': team_id,
                    'role': role,
                    'country': country,
                    'stats': {}  # Will be populated later
                }
                
                logger.info(f"Found player: {player_name} ({player_id})")
                players.append(player)
                
            except Exception as e:
                logger.error(f"Error parsing player card: {str(e)}")
                continue
        
        return players
    
    except Exception as e:
        logger.error(f"Error in get_team_players: {str(e)}")
        return []

def search_players(query, limit=10):
    """
    Searches for players matching the query.
    
    Args:
        query (str): Search term
        limit (int): Maximum number of results to return
        
    Returns:
        list: List of player dictionaries (limited information)
    """
    try:
        search_url = f"{BASE_URL}/search/?q={query}&type=players"
        soup = get_soup(search_url)
        
        if not soup:
            return []
        
        players = []
        player_items = soup.select('.search-item.search-item-player')
        
        for player_item in player_items[:limit]:
            try:
                player_link = player_item.select_one('a')
                if not player_link:
                    continue
                
                player_url = player_link.get('href')
                player_id = None
                if isinstance(player_url, str) and '/' in player_url:
                    parts = player_url.split('/')
                    if len(parts) > 0:
                        player_id = parts[-1]
                
                if not player_id:
                    continue
                
                # Extract player name
                name_elem = player_item.select_one('.search-item-title')
                player_name = name_elem.text.strip() if name_elem else None
                
                if not player_name:
                    continue
                
                # Extract team name
                team_elem = player_item.select_one('.search-item-subtitle')
                team_name = team_elem.text.strip() if team_elem else None
                
                # Create player object
                player = {
                    'id': player_id,
                    'name': player_name,
                    'team_name': team_name
                }
                
                players.append(player)
                
            except Exception as e:
                logger.error(f"Error parsing player item: {str(e)}")
                continue
        
        return players
    
    except Exception as e:
        logger.error(f"Error in search_players: {str(e)}")
        return []