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


def get_matches(limit=20):
    """
    Scrapes upcoming and recent matches from VLR.gg
    
    Args:
        limit (int): Maximum number of matches to fetch
        
    Returns:
        list: List of match dictionaries
    """
    try:
        matches_url = f"{BASE_URL}/matches"
        soup = get_soup(matches_url)
        
        if not soup:
            return []
        
        matches = []
        # Get all match items - these are now wrapped in <a> tags with class "wf-module-item match-item"
        match_items = soup.select('a.wf-module-item.match-item')
        
        for match_item in match_items[:limit]:
            try:
                # Extract match ID and URL directly from the <a> tag
                match_url = urljoin(BASE_URL, match_item['href'])
                match_id = match_url.split('/')[-2]
                
                # Extract teams
                teams = match_item.select('.match-item-vs-team')
                if len(teams) < 2:
                    continue
                
                # Get the text content within the team name divs
                team1_name_elem = teams[0].select_one('.match-item-vs-team-name .text-of')
                team2_name_elem = teams[1].select_one('.match-item-vs-team-name .text-of')
                
                if not team1_name_elem or not team2_name_elem:
                    continue
                
                team1_name = team1_name_elem.text.strip()
                team2_name = team2_name_elem.text.strip()
                
                # Extract match time/date
                date_elem = match_item.select_one('.match-item-time')
                date_str = date_elem.text.strip() if date_elem else ""
                
                # Extract event name
                event_elem = match_item.select_one('.match-item-event')
                event_name = event_elem.text.strip() if event_elem else ""
                
                # Extract score
                score_elem = match_item.select_one('.match-item-vs-team-score')
                score = score_elem.text.strip() if score_elem else "TBD"
                
                # Determine status (upcoming, live, completed)
                status = "upcoming"
                if "LIVE" in date_str:
                    status = "live"
                elif score and score != "TBD" and any(char.isdigit() for char in score):
                    status = "completed"
                
                # Create match object
                match = {
                    'id': match_id,
                    'team1_name': team1_name,
                    'team2_name': team2_name,
                    'date_str': date_str,
                    'event_name': event_name,
                    'score': score,
                    'status': status,
                    'match_url': match_url
                }
                
                matches.append(match)
                
            except Exception as e:
                logger.error(f"Error parsing match: {str(e)}")
                continue
        
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
        match_url = f"{BASE_URL}/{match_id}"
        soup = get_soup(match_url)
        
        if not soup:
            return None
        
        # Find match header
        match_header = soup.select_one('.match-header')
        if not match_header:
            logger.error(f"Could not find match header for match {match_id}")
            return None
        
        # Extract teams - using match-header-link elements
        team_links = match_header.select('.match-header-link')
        if len(team_links) < 2:
            logger.error(f"Could not find team links for match {match_id}")
            return None
        
        # Extract team names
        team1_name_elem = team_links[0].select_one('.wf-title-med')
        team2_name_elem = team_links[1].select_one('.wf-title-med')
        
        if not team1_name_elem or not team2_name_elem:
            logger.error(f"Could not find team names for match {match_id}")
            return None
            
        team1_name = team1_name_elem.text.strip()
        team2_name = team2_name_elem.text.strip()
        
        # Extract team IDs from href attribute
        team1_id = ""
        team2_id = ""
        team1_link = team_links[0].get('href')
        team2_link = team_links[1].get('href')
        
        if team1_link and isinstance(team1_link, str):
            team1_id = team1_link.split('/')[-1]
        
        if team2_link and isinstance(team2_link, str):
            team2_id = team2_link.split('/')[-1]
        
        # If team IDs are not available, generate them from team names
        if not team1_id:
            team1_id = re.sub(r'[^a-z0-9]', '-', team1_name.lower())
        if not team2_id:
            team2_id = re.sub(r'[^a-z0-9]', '-', team2_name.lower())
        
        # Extract match date from data attribute
        date_container = soup.select_one('.match-header-date .moment-tz-convert')
        date_str = ""
        match_date = None
        
        if date_container and date_container.has_attr('data-utc-ts'):
            date_str = date_container['data-utc-ts']
            logger.info(f"Found date string: {date_str} for match {match_id}")
            
            # Try to parse the date from the UTC timestamp
            try:
                match_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                logger.info(f"Successfully parsed date for match {match_id}: {match_date}")
            except Exception as e:
                logger.error(f"Error parsing date {date_str}: {str(e)}")
        else:
            # Fallback to getting the text display date
            date_elem = soup.select_one('.match-header-date')
            if date_elem:
                date_str = date_elem.text.strip()
                logger.info(f"Using fallback date text: {date_str}")
                
                # Try to parse the date
                try:
                    date_formats = [
                        "%B %d, %Y",
                        "%b %d, %Y",
                        "%Y-%m-%d"
                    ]
                    
                    for date_format in date_formats:
                        try:
                            match_date = datetime.strptime(date_str, date_format)
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    logger.error(f"Error parsing fallback date {date_str}: {str(e)}")
        
        # Extract event name
        event_elem = soup.select_one('.match-header-event')
        event_name = event_elem.text.strip() if event_elem else ""
        
        # Extract score - the score is inside a js-spoiler div with spans
        score_container = soup.select_one('.match-header-vs-score .js-spoiler')
        score = "TBD"
        
        if score_container:
            # Get all spans with scores and the colon
            score_parts = score_container.select('span')
            if len(score_parts) >= 3:  # Should have team1 score, colon, team2 score
                try:
                    team1_score = score_parts[0].text.strip()
                    team2_score = score_parts[2].text.strip()
                    score = f"{team1_score}-{team2_score}"
                except:
                    logger.error(f"Error parsing score for match {match_id}")
        
        logger.info(f"Extracted score: {score} for match {match_id}")
        
        # Determine status
        status = "upcoming"
        if "LIVE" in date_str:
            status = "live"
        elif score and score != "TBD" and any(char.isdigit() for char in score):
            status = "completed"
        
        # Extract maps
        maps = []
        map_elems = soup.select('.vm-stats-game')
        
        for map_elem in map_elems:
            try:
                map_name_elem = map_elem.select_one('.map-name')
                map_name = map_name_elem.text.strip() if map_name_elem else "Unknown"
                
                scores = map_elem.select('.score')
                if len(scores) >= 2:
                    team1_score = int(scores[0].text.strip()) if scores[0].text.strip().isdigit() else 0
                    team2_score = int(scores[1].text.strip()) if scores[1].text.strip().isdigit() else 0
                else:
                    team1_score = 0
                    team2_score = 0
                
                # Extract half scores (Attack/Defense)
                half_scores = map_elem.select('.mod-half')
                
                team1_attack = None
                team1_defense = None
                team2_attack = None
                team2_defense = None
                
                if len(half_scores) >= 4:
                    team1_attack = int(half_scores[0].text.strip()) if half_scores[0].text.strip().isdigit() else None
                    team1_defense = int(half_scores[1].text.strip()) if half_scores[1].text.strip().isdigit() else None
                    team2_attack = int(half_scores[2].text.strip()) if half_scores[2].text.strip().isdigit() else None
                    team2_defense = int(half_scores[3].text.strip()) if half_scores[3].text.strip().isdigit() else None
                
                # Get player stats for this map
                player_stats = {}
                stat_tables = map_elem.select('.vm-stats-container')
                
                for stat_table in stat_tables:
                    player_rows = stat_table.select('.st-stats')
                    
                    for player_row in player_rows:
                        player_name_elem = player_row.select_one('.mod-player')
                        player_name = player_name_elem.text.strip() if player_name_elem else "Unknown"
                        
                        # Extract agent
                        agent_img = player_row.select_one('.mod-agent img')
                        agent = agent_img['title'] if agent_img and 'title' in agent_img.attrs else "Unknown"
                        
                        # Extract KDA
                        kda_elem = player_row.select_one('.mod-kda')
                        kda = kda_elem.text.strip() if kda_elem else "0/0/0"
                        
                        # Parse KDA
                        kills, deaths, assists = 0, 0, 0
                        if kda and '/' in kda:
                            kda_parts = kda.split('/')
                            if len(kda_parts) >= 3:
                                kills = int(kda_parts[0]) if kda_parts[0].isdigit() else 0
                                deaths = int(kda_parts[1]) if kda_parts[1].isdigit() else 0
                                assists = int(kda_parts[2]) if kda_parts[2].isdigit() else 0
                        
                        # Extract ACS
                        acs_elem = player_row.select_one('.mod-acs')
                        acs = int(acs_elem.text.strip()) if acs_elem and acs_elem.text.strip().isdigit() else 0
                        
                        # Determine team
                        team_name = "Unknown"
                        team_elem = player_row.select_one('.mod-team')
                        if team_elem:
                            team_text = team_elem.text.strip()
                            team_name = team1_name if team_text in team1_name else team2_name
                        
                        player_stats[player_name] = {
                            'agent': agent,
                            'kills': kills,
                            'deaths': deaths,
                            'assists': assists,
                            'acs': acs,
                            'team': team_name
                        }
                
                map_data = {
                    'map_name': map_name,
                    'team1_score': team1_score,
                    'team2_score': team2_score,
                    'team1_attack': team1_attack,
                    'team1_defense': team1_defense,
                    'team2_attack': team2_attack,
                    'team2_defense': team2_defense,
                    'player_stats': player_stats
                }
                
                maps.append(map_data)
                
            except Exception as e:
                logger.error(f"Error parsing map: {str(e)}")
                continue
        
        # Create complete match object
        match_details = {
            'id': match_id,
            'team1_id': team1_id,
            'team2_id': team2_id,
            'team1_name': team1_name,
            'team2_name': team2_name,
            'date': match_date,
            'date_str': date_str,
            'event_name': event_name,
            'score': score,
            'status': status,
            'match_url': match_url,
            'maps': maps
        }
        
        return match_details
    
    except Exception as e:
        logger.error(f"Error in get_match_details: {str(e)}")
        return None


def get_team_details(team_id):
    """
    Scrapes team information and roster from VLR.gg
    
    Args:
        team_id (str): ID of the team to fetch
        
    Returns:
        dict: Team details with player roster
    """
    try:
        # Try direct approach with team ID
        team_url = f"{BASE_URL}/team/{team_id}"
        soup = get_soup(team_url)
        
        # If that fails, try searching for the team
        if not soup or "Page not found" in soup.text:
            logger.info(f"Team page not found directly. Trying to search for team: {team_id}")
            teams_found = search_teams(team_id.replace('-', ' '), limit=5)
            
            if not teams_found:
                logger.warning(f"No teams found when searching for: {team_id}")
                # Create a minimal team object with available information
                team_details = {
                    'id': team_id,
                    'name': team_id.replace('-', ' ').title(),
                    'region': None,
                    'logo_url': None,
                    'stats': {},
                    'players': []
                }
                return team_details
            
            # Use the first search result
            team_url = teams_found[0].get('team_url')
            if not team_url:
                logger.warning(f"No team URL found in search results for: {team_id}")
                return None
            
            soup = get_soup(team_url)
            if not soup:
                logger.warning(f"Failed to get team page from search result: {team_url}")
                return None
        
        # Extract team name
        name_elem = soup.select_one('.team-header-name')
        name = name_elem.text.strip() if name_elem else team_id.replace('-', ' ').title()
        
        # Extract team region
        region_elem = soup.select_one('.team-header-country')
        region = region_elem.text.strip() if region_elem else None
        
        # Extract team logo
        logo_elem = soup.select_one('.team-header-logo img')
        logo_url = None
        if logo_elem and 'src' in logo_elem.attrs:
            logo_url = logo_elem['src'] 
            if logo_url and isinstance(logo_url, str) and not logo_url.startswith(('http://', 'https://')):
                logo_url = urljoin(BASE_URL, logo_url)
        
        # Extract team statistics
        stats = {}
        stats_elem = soup.select_one('.team-summary-container-stats')
        if stats_elem:
            stat_items = stats_elem.select('.stat-item')
            for stat_item in stat_items:
                label_elem = stat_item.select_one('.label')
                value_elem = stat_item.select_one('.value')
                
                if label_elem and value_elem:
                    label = label_elem.text.strip().lower().replace(' ', '_')
                    value = value_elem.text.strip()
                    stats[label] = value
        
        # Extract players/roster
        players = []
        roster_elems = soup.select('.player-card')
        
        for player_elem in roster_elems:
            try:
                # Extract player info
                player_name_elem = player_elem.select_one('.player-name')
                player_name = player_name_elem.text.strip() if player_name_elem else "Unknown"
                
                # Extract player ID from the URL
                player_link = player_elem.select_one('a')
                player_id = None
                if player_link and 'href' in player_link.attrs:
                    player_url = player_link['href']
                    if isinstance(player_url, str):
                        player_id = player_url.split('/')[-1]
                
                # Default player ID if not found
                if not player_id:
                    player_id = re.sub(r'[^a-z0-9]', '-', player_name.lower())
                
                # Extract player role
                role_elem = player_elem.select_one('.player-role')
                role = role_elem.text.strip() if role_elem else "Unknown"
                
                # Extract player country
                country_elem = player_elem.select_one('.player-country')
                country = country_elem.text.strip() if country_elem else "Unknown"
                
                # Find player image
                player_img = player_elem.select_one('.player-thumbnail img')
                player_img_url = None
                if player_img and 'src' in player_img.attrs:
                    player_img_url = player_img['src']
                    if player_img_url and isinstance(player_img_url, str) and not player_img_url.startswith(('http://', 'https://')):
                        player_img_url = urljoin(BASE_URL, player_img_url)
                
                player_data = {
                    'id': player_id,
                    'name': player_name,
                    'role': role,
                    'country': country,
                    'team_id': team_id,
                    'image_url': player_img_url
                }
                
                players.append(player_data)
                logger.info(f"Found player {player_name} for team {name}")
                
            except Exception as e:
                logger.error(f"Error parsing player: {str(e)}")
                continue
        
        # Create complete team object
        team_details = {
            'id': team_id,
            'name': name,
            'region': region,
            'logo_url': logo_url,
            'stats': stats,
            'players': players
        }
        
        return team_details
    
    except Exception as e:
        logger.error(f"Error in get_team_details: {str(e)}")
        return None


def search_teams(query, limit=10):
    """
    Searches for teams matching the query
    
    Args:
        query (str): Search term
        limit (int): Maximum number of results to return
        
    Returns:
        list: List of team dictionaries (limited information)
    """
    try:
        search_url = f"{BASE_URL}/search?q={query}"
        soup = get_soup(search_url)
        
        if not soup:
            return []
        
        teams = []
        team_elems = soup.select('.search-item.team')
        
        for team_elem in team_elems[:limit]:
            try:
                # Extract team info
                team_link = team_elem.select_one('a')
                if not team_link or 'href' not in team_link.attrs:
                    continue
                
                team_url = team_link['href']
                team_id = team_url.split('/')[-1]
                
                team_name_elem = team_elem.select_one('.search-item-text')
                team_name = team_name_elem.text.strip() if team_name_elem else "Unknown"
                
                team_data = {
                    'id': team_id,
                    'name': team_name,
                    'team_url': urljoin(BASE_URL, team_url)
                }
                
                teams.append(team_data)
                
            except Exception as e:
                logger.error(f"Error parsing team search result: {str(e)}")
                continue
        
        return teams
    
    except Exception as e:
        logger.error(f"Error in search_teams: {str(e)}")
        return []


def get_events(limit=10):
    """
    Gets upcoming and ongoing events
    
    Args:
        limit (int): Maximum number of events to fetch
        
    Returns:
        list: List of event dictionaries
    """
    try:
        events_url = f"{BASE_URL}/events"
        soup = get_soup(events_url)
        
        if not soup:
            return []
        
        events = []
        event_elems = soup.select('.event-item')
        
        for event_elem in event_elems[:limit]:
            try:
                event_link = event_elem.select_one('a')
                if not event_link or 'href' not in event_link.attrs:
                    continue
                
                event_url = event_link['href']
                event_id = event_url.split('/')[-1]
                
                event_name_elem = event_elem.select_one('.event-item-title')
                event_name = event_name_elem.text.strip() if event_name_elem else "Unknown"
                
                event_date_elem = event_elem.select_one('.event-item-desc-item.mod-dates')
                event_date = event_date_elem.text.strip() if event_date_elem else ""
                
                event_region_elem = event_elem.select_one('.event-item-desc-item.mod-location')
                event_region = event_region_elem.text.strip() if event_region_elem else "Unknown"
                
                # Parse event dates
                start_date = None
                end_date = None
                if event_date:
                    try:
                        # Format may be "Apr 15 - Apr 30, 2025"
                        date_parts = event_date.split(' - ')
                        if len(date_parts) == 2:
                            # Try to parse end date with year
                            end_date_str = date_parts[1]
                            if ',' in end_date_str:
                                end_date_parts = end_date_str.split(', ')
                                year = end_date_parts[1].strip() if len(end_date_parts) > 1 else "2025"
                                
                                # Now parse start and end dates
                                start_date_str = f"{date_parts[0].strip()}, {year}"
                                try:
                                    start_date = datetime.strptime(start_date_str, "%b %d, %Y")
                                except:
                                    start_date = None
                                
                                try:
                                    end_date = datetime.strptime(end_date_str, "%b %d, %Y")
                                except:
                                    end_date = None
                    except:
                        logger.error(f"Error parsing event date: {event_date}")
                
                # Determine status based on dates
                status = "upcoming"
                current_date = datetime.now()
                if start_date and end_date:
                    if current_date < start_date:
                        status = "upcoming"
                    elif current_date > end_date:
                        status = "completed"
                    else:
                        status = "ongoing"
                
                # Extract logo URL if available
                logo_elem = event_elem.select_one('.event-item-thumb img')
                logo_url = None
                if logo_elem and 'src' in logo_elem.attrs:
                    logo_url = logo_elem['src']
                    if logo_url.startswith('//'):
                        logo_url = f"https:{logo_url}"
                    elif not logo_url.startswith(('http://', 'https://')):
                        logo_url = urljoin(BASE_URL, logo_url)
                
                event_data = {
                    'id': event_id,
                    'name': event_name,
                    'date': event_date,
                    'region': event_region,
                    'start_date': start_date,
                    'end_date': end_date,
                    'status': status,
                    'logo_url': logo_url,
                    'event_url': urljoin(BASE_URL, event_url)
                }
                
                events.append(event_data)
                
            except Exception as e:
                logger.error(f"Error parsing event: {str(e)}")
                continue
        
        return events
    
    except Exception as e:
        logger.error(f"Error in get_events: {str(e)}")
        return []


def get_event_details(event_id):
    """
    Gets detailed information for a specific event
    
    Args:
        event_id (str): ID of the event to fetch
        
    Returns:
        dict: Event details
    """
    try:
        event_url = f"{BASE_URL}/event/{event_id}"
        soup = get_soup(event_url)
        
        if not soup or "Page not found" in soup.text:
            logger.error(f"Event page not found: {event_id}")
            return None
        
        # Extract event name
        event_name_elem = soup.select_one('.wf-title')
        event_name = event_name_elem.text.strip() if event_name_elem else "Unknown Event"
        
        # Extract event dates
        event_date_elem = soup.select_one('.event-desc-item-value.mod-dates')
        event_date = event_date_elem.text.strip() if event_date_elem else ""
        
        # Parse event dates
        start_date = None
        end_date = None
        if event_date:
            try:
                # Format may be "Apr 15 - Apr 30, 2025"
                date_parts = event_date.split(' - ')
                if len(date_parts) == 2:
                    # Try to parse end date with year
                    end_date_str = date_parts[1]
                    if ',' in end_date_str:
                        end_date_parts = end_date_str.split(', ')
                        year = end_date_parts[1].strip() if len(end_date_parts) > 1 else "2025"
                        
                        # Now parse start and end dates
                        start_date_str = f"{date_parts[0].strip()}, {year}"
                        try:
                            start_date = datetime.strptime(start_date_str, "%b %d, %Y")
                        except:
                            start_date = None
                        
                        try:
                            end_date = datetime.strptime(end_date_str, "%b %d, %Y")
                        except:
                            end_date = None
            except:
                logger.error(f"Error parsing event date: {event_date}")
        
        # Extract event location/region
        region_elem = soup.select_one('.event-desc-item-value.mod-location')
        region = region_elem.text.strip() if region_elem else "Unknown"
        
        # Extract prize pool if available
        prize_pool_elem = soup.select_one('.event-desc-item-value.mod-prize')
        prize_pool = prize_pool_elem.text.strip() if prize_pool_elem else "Unknown"
        
        # Determine status based on dates
        status = "upcoming"
        current_date = datetime.now()
        if start_date and end_date:
            if current_date < start_date:
                status = "upcoming"
            elif current_date > end_date:
                status = "completed"
            else:
                status = "ongoing"
        
        # Extract logo URL if available
        logo_elem = soup.select_one('.event-header-thumb img')
        logo_url = None
        if logo_elem and 'src' in logo_elem.attrs:
            logo_url = logo_elem['src']
            if logo_url.startswith('//'):
                logo_url = f"https:{logo_url}"
            elif not logo_url.startswith(('http://', 'https://')):
                logo_url = urljoin(BASE_URL, logo_url)
        
        # Get matches for this event
        matches = []
        match_elems = soup.select('.wf-card.event-group-container')
        for match_elem in match_elems[:20]:  # Limit to avoid too many requests
            try:
                match_link = match_elem.select_one('a.match-item')
                if match_link and 'href' in match_link.attrs:
                    match_url = match_link['href']
                    match_id = match_url.split('/')[-2]  # Format: /123/team1-vs-team2
                    matches.append(match_id)
            except Exception as e:
                logger.error(f"Error parsing match in event: {str(e)}")
        
        event_data = {
            'id': event_id,
            'name': event_name,
            'region': region,
            'start_date': start_date,
            'end_date': end_date,
            'prize_pool': prize_pool,
            'status': status,
            'logo_url': logo_url,
            'event_url': event_url,
            'matches': matches
        }
        
        return event_data
    
    except Exception as e:
        logger.error(f"Error in get_event_details: {str(e)}")
        return None
