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
    for submission in reddit.subreddit("UMD").search(prof_name, sort="new", limit=10):
        text = submission.title + "\n" + submission.selftext
        semester = "Unknown"
        store_review(cur, professor_id, "reddit", text, semester)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Fetched and stored Reddit reviews for {prof_name}")

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
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium-browser")
    driver = webdriver.Chrome(options=options)
    search_url = f"https://www.ratemyprofessors.com/search/professors/1112?q={prof_name.replace(' ', '%20')}"
    driver.get(search_url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    prof_links = soup.find_all('a', href=True)
    prof_url = None
    for link in prof_links:
        if '/professor/' in link['href']:
            prof_url = "https://www.ratemyprofessors.com" + link['href']
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

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py [reddit|coursicle|rmp] [professor name]")
        sys.exit(1)
    source = sys.argv[1]
    prof_name = sys.argv[2]
    if source == "reddit":
        scrape_reddit(prof_name)
    elif source == "coursicle":
        scrape_coursicle(prof_name)
    elif source == "rmp":
        scrape_rmp(prof_name)
    else:
        print("Unknown source.") 