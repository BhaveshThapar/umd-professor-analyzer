import sys
import os
import praw
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

load_dotenv()

DB_CONFIG = dict(
    dbname=os.getenv("POSTGRES_DB", "umdprof"),
    user=os.getenv("POSTGRES_USER", "umdprof"),
    password=os.getenv("POSTGRES_PASSWORD", "umdprof"),
    host=os.getenv("POSTGRES_HOST", "db"),
    port=int(os.getenv("POSTGRES_PORT", 5432))
)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")


def get_professor_id(cur, name, department="CMSC"):
    cur.execute("""
        INSERT INTO professor (name, department, avg_planetterp_gpa, avg_rating)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (name) DO NOTHING;
    """, (name, department, 2.85, 3.5))
    cur.execute("SELECT id FROM professor WHERE name = %s", (name,))
    return cur.fetchone()[0]

def store_review(cur, professor_id, source, text, semester):
    cur.execute("""
        INSERT INTO review (professor_id, source, raw_text, semester, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """, (professor_id, source, text, semester, datetime.now()))

def is_likely_review(submission):
    """
    Determine if a Reddit submission is likely a review (vs question/comparison/mention)
    
    This filtering logic is compatible with any deployment platform including Vercel.
    It runs during scraping, not at request time.
    """
    title = submission.title.lower()
    body = submission.selftext.lower()
    
    # Filter out questions
    if '?' in title:
        return False
    
    # Filter out comparison posts (check both title and body)
    comparison_keywords = ['vs', ' or ', 'between']
    combined_text_lower = title + ' ' + body
    if any(keyword in combined_text_lower for keyword in comparison_keywords):
        return False
    
    # Filter out posts about incidents/policies
    incident_keywords = ['cheating', 'academic integrity', 'violation', 'caught']
    if any(keyword in title for keyword in incident_keywords):
        return False
    
    # Require minimum content length (filter out very short posts)
    combined_text = title + ' ' + body
    if len(combined_text) < 50:  # Minimum 50 characters
        return False
    
    # Look for review indicators in the body
    # If the body contains feedback-like content, it's more likely a review
    review_indicators = ['class', 'professor', 'exam', 'grade', 'homework', 
                        'easy', 'hard', 'difficult', 'helpful', 'lecture',
                        'assignment', 'project', 'test', 'quiz', 'fair']
    indicator_count = sum(1 for keyword in review_indicators if keyword in body)
    
    # If body is substantial and contains review keywords, likely a review
    if len(body) > 100 and indicator_count >= 2:
        return True
    
    # Default: reject unless it passes basic checks
    return False

def scrape_reddit(prof_name):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        user_agent=REDDIT_USER_AGENT
    )
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    professor_id = get_professor_id(cur, prof_name)
    
    review_count = 0
    searched_count = 0
    
    # Increase limit to 20 since we'll be filtering many out
    for submission in reddit.subreddit("UMD").search(prof_name, sort="new", limit=20):
        searched_count += 1
        if is_likely_review(submission):
            text = submission.title + "\n" + submission.selftext
            semester = "Unknown"
            store_review(cur, professor_id, "reddit", text, semester)
            review_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Searched {searched_count} Reddit posts, stored {review_count} reviews for {prof_name}")

def scrape_coursicle(prof_name):
    slug = prof_name.lower().replace(" ", "-")
    url = f"https://www.coursicle.com/umd/professor/{slug}/"
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Coursicle page not found for {prof_name}")
        return
    soup = BeautifulSoup(resp.text, "html.parser")
    reviews = [r.get_text(strip=True) for r in soup.select('.review-text')]
    if not reviews:
        print(f"No Coursicle reviews found for {prof_name}")
        return
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    professor_id = get_professor_id(cur, prof_name)
    for text in reviews:
        store_review(cur, professor_id, "coursicle", text, "Unknown")
    conn.commit()
    cur.close()
    conn.close()
    print(f"Fetched and stored {len(reviews)} Coursicle reviews for {prof_name}")

def scrape_rmp(prof_name):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    # Fixed: Use UMD school ID (1270) instead of UIUC (1112)
    search_url = f"https://www.ratemyprofessors.com/search/professors/1270?q={prof_name.replace(' ', '%20')}"
    driver.get(search_url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    prof_links = soup.find_all('a', href=True)
    prof_url = None
    target_name_lower = prof_name.lower()
    
    # Add name validation to ensure correct professor
    # Common name abbreviations for better matching
    name_variations = {
        'christopher': 'chris',
        'chris': 'christopher',
        'michael': 'mike',
        'mike': 'michael',
        'robert': 'rob',
        'rob': 'robert',
        'william': 'will',
        'will': 'william',
        'richard': 'rick',
        'rick': 'richard',
        'joseph': 'joe',
        'joe': 'joseph'
    }
    
    for link in prof_links:
        if '/professor/' in link['href']:
            # Get the professor's name from the card - use 'CardName' not 'TeacherName'
            parent = link.find_parent('div', class_=lambda x: x and 'TeacherCard' in x)
            if parent:
                name_elem = parent.find(class_=lambda x: x and 'CardName' in x)
                if name_elem:
                    displayed_name = name_elem.get_text(strip=True).lower()
                    target_parts = target_name_lower.split()
                    displayed_parts = displayed_name.split()
                    
                    # Check for exact match or fuzzy match with name variations
                    match_found = False
                    
                    # Exact substring match
                    if target_name_lower in displayed_name or displayed_name in target_name_lower:
                        match_found = True
                    # Check if all words from target appear in displayed (handles middle names, etc.)
                    elif all(word in displayed_name for word in target_parts):
                        match_found = True
                    # Check for name abbreviations (Chris vs Christopher)
                    elif len(target_parts) >= 2 and len(displayed_parts) >= 2:
                        # Check if last names match and first names are variations
                        if target_parts[-1] == displayed_parts[-1]:  # Last name match
                            first_target = target_parts[0]
                            first_displayed = displayed_parts[0]
                            # Check if one is a known variation of the other
                            if (first_target in name_variations and 
                                name_variations[first_target] == first_displayed):
                                match_found = True
                            elif first_target == first_displayed:
                                match_found = True
                    
                    if match_found:
                        prof_url = "https://www.ratemyprofessors.com" + link['href']
                        print(f"  → Matched professor: {name_elem.get_text(strip=True)}")
                        break
    
    if not prof_url:
        # Fallback: if no name match found, take first result (old behavior) but warn about it
        for link in prof_links:
            if '/professor/' in link['href']:
                prof_url = "https://www.ratemyprofessors.com" + link['href']
                print(f"  ⚠️ WARNING: No exact name match found, using first result")
                break
    
    if not prof_url:
        print(f"No RMP profile found for {prof_name}")
        driver.quit()
        return
    
    driver.get(prof_url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    reviews = [r.get_text(strip=True) for r in soup.select('.Comments__StyledComments-dzzyvm-0')]
    if not reviews:
        print(f"No RMP reviews found for {prof_name}")
        driver.quit()
        return
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    professor_id = get_professor_id(cur, prof_name)
    for text in reviews:
        store_review(cur, professor_id, "rmp", text, "Unknown")
    conn.commit()
    cur.close()
    conn.close()
    print(f"Fetched and stored {len(reviews)} RMP reviews for {prof_name}")
    driver.quit()

def main():
    print('sys.argv:', sys.argv)
    if len(sys.argv) < 3:
        print("Usage: python main.py [reddit|coursicle|rmp] [professor name]")
        sys.exit(1)
    source = sys.argv[1].strip().lower()
    prof_name = " ".join(sys.argv[2:]).strip()
    if source == "reddit":
        scrape_reddit(prof_name)
    elif source == "coursicle":
        scrape_coursicle(prof_name)
    elif source == "rmp":
        scrape_rmp(prof_name)
    else:
        print(f"Unknown source: {source}")

if __name__ == "__main__":
    main() 