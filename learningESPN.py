# learningESPN.py
import datetime
import json
import os
import time
from typing import Dict, List

import openai
import pandas as pd
import requests
from dotenv import load_dotenv

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
SITE_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
CORE_API_BASE = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"

# Load environment variables
load_dotenv()

def _make_request(url: str, params: Dict[str, str] = None, retries: int = 3, backoff: float = 0.5):
    """
    Helper to perform HTTP GET requests with retries and a consistent User-Agent.
    Returns parsed JSON or raises an exception after exhausting retries.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=20,
            )
            if response.status_code == 200:
                return response.json()
            last_error = RuntimeError(f"HTTP {response.status_code} for {url} params={params}")
        except Exception as exc:
            last_error = exc
        time.sleep(backoff * attempt)
    raise last_error or RuntimeError(f"Failed to fetch {url}")


def _extract_stat(categories: List[Dict], category_name: str, stat_name: str, default: float = 0.0) -> float:
    """
    Convenience function to extract a stat from the nested ESPN category structure.
    """
    for category in categories:
        if category.get("name") == category_name:
            for stat in category.get("stats", []):
                if stat.get("name") == stat_name:
                    value = stat.get("value")
                    if value in (None, "", "null"):
                        return default
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        try:
                            return float(stat.get("displayValue", default).replace(",", ""))
                        except Exception:
                            return default
    return default


def _get_regular_season_year() -> int:
    """
    Determine the NFL season to query. Defaults to current year, but allows override via env.
    If we're in the offseason before August and no override is supplied, use previous year.
    """
    env_override = os.getenv("NFL_SEASON")
    if env_override and env_override.isdigit():
        return int(env_override)

    today = datetime.date.today()
    season_year = today.year
    # Before August the upcoming season may not have data; use previous season unless explicitly overridden.
    if today.month < 8:
        season_year -= 1
    return season_year


def _get_team_list() -> List[Dict[str, str]]:
    """
    Retrieve the list of NFL teams with IDs and abbreviations from ESPN.
    """
    teams_payload = _make_request(
        f"{SITE_API_BASE}/teams",
        params={"region": "us", "lang": "en", "limit": "50"},
    )
    teams = []
    for team_entry in teams_payload.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
        team = team_entry.get("team", {})
        if not team:
            continue
        teams.append(
            {
                "id": team.get("id"),
                "name": team.get("displayName"),
                "abbreviation": team.get("abbreviation"),
            }
        )
    return teams


def _get_points_allowed(team_id: str, season: int) -> float:
    """
    Fetch total points against for a team using the standings/record endpoint.
    """
    record_payload = _make_request(
        f"{CORE_API_BASE}/seasons/{season}/types/2/teams/{team_id}/record",
        params={"lang": "en", "region": "us"},
    )
    for item in record_payload.get("items", []):
        for stat in item.get("stats", []):
            if stat.get("name") == "pointsAgainst":
                return float(stat.get("value", 0.0))
    return 0.0


def _get_defensive_stats(team_id: str, season: int) -> Dict[str, float]:
    """
    Pull defensive categories for sacks, interceptions, and takeaways.
    """
    stats_payload = _make_request(
        f"{CORE_API_BASE}/seasons/{season}/types/2/teams/{team_id}/statistics",
        params={"lang": "en", "region": "us", "contentorigin": "espn"},
    )
    categories = stats_payload.get("splits", {}).get("categories", [])

    sacks = _extract_stat(categories, "defensive", "sacks", default=0.0)
    interceptions = _extract_stat(categories, "defensiveInterceptions", "interceptions", default=0.0)
    takeaways = _extract_stat(categories, "miscellaneous", "totalTakeaways", default=0.0)

    return {
        "Sacks": sacks,
        "Interceptions": interceptions,
        "Turnovers": takeaways,
    }


def _build_event_team_map(team_ids: List[str], season: int) -> Dict[str, List[str]]:
    """
    Build a mapping from event id to the participating team ids for the given season.
    """
    event_map: Dict[str, List[str]] = {}
    for idx, team_id in enumerate(team_ids, start=1):
        schedule_payload = _make_request(
            f"{SITE_API_BASE}/teams/{team_id}/schedule",
            params={"season": season, "seasontype": 2},
        )
        for event in schedule_payload.get("events", []):
            event_id = event.get("id")
            competitions = event.get("competitions", [])
            if not competitions:
                continue
            competitors = competitions[0].get("competitors", [])
            event_map[event_id] = [c.get("team", {}).get("id") for c in competitors if c.get("team")]

        if idx % 5 == 0:
            time.sleep(0.5)
    return event_map


def _compute_yards_allowed(team_ids: List[str], season: int) -> Dict[str, int]:
    """
    Aggregate total yards allowed per team by iterating through each game's boxscore.
    """
    yards_allowed = {team_id: 0 for team_id in team_ids}
    event_map = _build_event_team_map(team_ids, season)

    for processed_count, (event_id, participants) in enumerate(event_map.items(), start=1):
        if not participants or len(participants) != 2:
            continue

        summary_payload = _make_request(
            f"{SITE_API_BASE}/summary",
            params={"event": event_id},
        )
        teams = summary_payload.get("boxscore", {}).get("teams", [])
        if len(teams) != 2:
            continue

        team_totals = {}
        for team_entry in teams:
            team_info = team_entry.get("team", {})
            tid = team_info.get("id")
            yards_total = 0
            for stat in team_entry.get("statistics", []):
                if stat.get("name") == "totalYards":
                    raw_value = stat.get("displayValue") or stat.get("value")
                    try:
                        yards_total = int(str(raw_value).replace(",", ""))
                    except (ValueError, TypeError):
                        yards_total = 0
                    break
            if tid:
                team_totals[tid] = yards_total

        if len(team_totals) == 2:
            tid_a, tid_b = list(team_totals.keys())
            yards_allowed[tid_a] += team_totals[tid_b]
            yards_allowed[tid_b] += team_totals[tid_a]

        if processed_count % 25 == 0:
            time.sleep(0.5)

    return yards_allowed


def fetch_nfl_defensive_stats():
    """
    Fetches NFL defensive statistics from ESPN APIs.
    Returns a list of dictionaries with team defensive stats.
    """
    try:
        season = _get_regular_season_year()
        teams = _get_team_list()
        if not teams:
            raise RuntimeError("Unable to retrieve NFL teams from ESPN.")

        print(f"Using NFL season {season}. Found {len(teams)} teams. Fetching defensive stats...")

        team_ids = [team["id"] for team in teams]
        yards_allowed_map = _compute_yards_allowed(team_ids, season)

        teams_data = []
        for idx, team in enumerate(teams, start=1):
            team_id = team["id"]
            stats = _get_defensive_stats(team_id, season)
            points_allowed = _get_points_allowed(team_id, season)
            yards_allowed = yards_allowed_map.get(team_id, 0)

            teams_data.append(
                {
                    "Team": team["name"],
                    "Abbreviation": team["abbreviation"],
                    "Team_ID": team_id,
                    "Points_Allowed": int(points_allowed),
                    "Yards_Allowed": int(yards_allowed),
                    "Turnovers": int(stats.get("Turnovers", 0)),
                    "Sacks": int(stats.get("Sacks", 0)),
                    "Interceptions": int(stats.get("Interceptions", 0)),
                }
            )

            if idx % 5 == 0:
                time.sleep(0.5)

        return teams_data

    except Exception as e:
        print(f"Error fetching ESPN data: {e}")
        import traceback

        traceback.print_exc()
        # Return fallback template to keep downstream processing functional.
        return [
            {
                "Team": "Unknown Team",
                "Abbreviation": "UNK",
                "Team_ID": "0",
                "Points_Allowed": 0,
                "Yards_Allowed": 0,
                "Turnovers": 0,
                "Sacks": 0,
                "Interceptions": 0,
            }
        ]


def get_ai_defensive_summary(team_data):
    """
    Uses OpenAI to generate a defensive summary for a team.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Validate API key
    if not api_key or api_key.strip() == "" or api_key == "your_openai_api_key_here":
        return "AI summary not available - please set OPENAI_API_KEY in .env file"
    
    # Check if API key has correct format (should start with sk-)
    api_key = api_key.strip()
    if not api_key.startswith("sk-"):
        return f"AI summary error: Invalid API key format. API key should start with 'sk-'. Current key starts with: '{api_key[:5] if len(api_key) >= 5 else api_key}'"
    
    try:
        # Create a prompt for the AI
        points_allowed = team_data.get('Points_Allowed', 'N/A')
        yards_allowed = team_data.get('Yards_Allowed', 'N/A')
        turnovers = team_data.get('Turnovers', 'N/A')
        sacks = team_data.get('Sacks', 'N/A')
        interceptions = team_data.get('Interceptions', 'N/A')
        
        # Convert numeric values to strings for the prompt
        def format_stat(value):
            if value == 0 or value == 'N/A' or value is None:
                return 'N/A'
            try:
                return str(int(value))
            except:
                return str(value)
        
        prompt = f"""Analyze the following NFL team defensive statistics and provide a brief 2-3 sentence summary of their defensive performance this season.

Team: {team_data.get('Team', 'Unknown')}
Points Allowed: {format_stat(points_allowed)}
Yards Allowed: {format_stat(yards_allowed)}
Turnovers: {format_stat(turnovers)}
Sacks: {format_stat(sacks)}
Interceptions: {format_stat(interceptions)}
Players to watch: {team_data.get('Players to watch', 'N/A')}

Provide a concise defensive analysis:"""

        # Initialize OpenAI client with proper error handling
        # The OpenAI client validates the API key format on initialization
        try:
            # Remove any whitespace, newlines, or quotes that might have been accidentally included
            api_key_clean = api_key.strip().strip('"').strip("'")
            client = openai.OpenAI(api_key=api_key_clean)
        except ValueError as ve:
            # This catches format validation errors
            error_msg = str(ve)
            if "pattern" in error_msg.lower() or "match" in error_msg.lower():
                return f"AI API key format error: Your API key format is invalid. Please check your .env file. The key should start with 'sk-' and be about 51 characters long. Error: {error_msg}"
            return f"AI client initialization error: {error_msg}"
        except Exception as client_error:
            error_msg = str(client_error)
            if "pattern" in error_msg.lower() or "match" in error_msg.lower():
                return f"AI API key format error: Please check your OPENAI_API_KEY in .env file. It should start with 'sk-'. Error: {error_msg}"
            return f"AI client error: {error_msg}"
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an NFL defensive analyst providing concise team defensive summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7,
                timeout=30.0  # Add timeout to prevent hanging
            )
        except Exception as api_call_error:
            error_msg = str(api_call_error)
            if "pattern" in error_msg.lower() or "match" in error_msg.lower():
                return f"AI API error (key format): {error_msg}. Please verify your OPENAI_API_KEY in .env file."
            raise  # Re-raise if it's a different error
        
        if response and response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            return "AI summary error: Empty response from OpenAI"
    
    except openai.AuthenticationError as e:
        return f"AI authentication error: Invalid API key. Please check your OPENAI_API_KEY in .env file"
    except openai.APIError as e:
        return f"AI API error: {str(e)}"
    except Exception as e:
        error_msg = str(e)
        # Provide more helpful error messages
        if "string did not match" in error_msg.lower() or "pattern" in error_msg.lower():
            return f"AI API key format error: Please ensure your OPENAI_API_KEY in .env file is correct and starts with 'sk-'. Error: {error_msg}"
        return f"AI summary error: {error_msg}"


def fetch_and_save_nfl():
    """
    Main function: Fetches NFL defensive stats from ESPN, generates AI summaries,
    and saves everything to an Excel file.
    """
    try:
        print("Fetching NFL defensive stats from ESPN...")
        teams_data = fetch_nfl_defensive_stats()
        
        if not teams_data or len(teams_data) == 0:
            raise Exception("No team data retrieved from ESPN")
        
        print(f"Found {len(teams_data)} teams. Generating AI summaries...")
        
        # Check if OpenAI API key is configured
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "your_openai_api_key_here" or api_key == "":
            print("Warning: OPENAI_API_KEY not set. AI summaries will be placeholder text.")
            # Add placeholder summaries
            for team in teams_data:
                team['AI_Summary'] = "AI summary not available - please set OPENAI_API_KEY in .env file"
        else:
            # Add AI summaries to each team
            for idx, team in enumerate(teams_data):
                try:
                    print(f"Processing {team.get('Team', 'Unknown')} ({idx + 1}/{len(teams_data)})...")
                    team['AI_Summary'] = get_ai_defensive_summary(team)
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error processing {team.get('Team', 'Unknown')}: {str(e)}")
                    team['AI_Summary'] = f"Error generating summary: {str(e)}"
        
        # Create DataFrame
        df = pd.DataFrame(teams_data)
        
        # Save to Excel
        excel_filename = "nfl_ai_summary.xlsx"
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        
        print(f"Saved to {excel_filename}")
        return excel_filename
    
    except Exception as e:
        error_msg = f"Error in fetch_and_save_nflp: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        raise Exception(error_msg)


if __name__ == "__main__":
    fetch_and_save_nfl()

