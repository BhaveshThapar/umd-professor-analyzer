# UMD Professor Analyzer

A full-stack platform for UMD students to search professors, view grade data, read summarized student opinions, and see AI-generated insights.

---

## Features
- **Search UMD Professors** by name
- **Live Grade Data** from PlanetTerp API (GPA, department, courses)
- **Aggregated Reviews** from Reddit, Coursicle, and RateMyProfessors (RMP)
- **AI-Powered Summaries**: LLM (Gemini) generates unbiased summaries, tags, skills, and sentiment
- **Toxicity Detection**: Flags inappropriate or toxic reviews
- **Q&A**: Ask questions about a professor and get LLM-powered answers
- **Auto-Scraping**: If a professor is not in the database, scrapers run automatically
- **Modern UI**: React + Tailwind CSS, responsive and user-friendly

---

## Architecture
- **Monorepo**: All services in one repo, orchestrated by Docker Compose
- **Backend**: Spring Boot (Java), REST API, connects to PostgreSQL, triggers scrapers, calls NLP microservice
- **Frontend**: React.js, Tailwind CSS, search UI, displays analytics and reviews
- **Scrapers**: Python, fetch reviews from Reddit (PRAW), Coursicle (requests/bs4), RMP (Selenium)
- **NLP Microservice**: FastAPI (Python), Gemini LLM for summarization, tags, skills, sentiment, toxicity, Q&A
- **Database**: PostgreSQL, schema for professors, reviews, and NLP summaries
- **Containerized**: All services run in Docker, including Selenium for headless scraping

---

## AI/NLP Capabilities
- **Summarization**: 2-3 sentence unbiased summary of all reviews
- **Tags**: Extracts 3-7 descriptive tags (e.g., "tough grader", "engaging lectures")
- **Skills/Topics**: Lists technical and soft skills emphasized by the professor
- **Sentiment Analysis**: Score (0-1) and explanation
- **Toxicity Detection**: Flags if reviews are toxic or inappropriate
- **Q&A**: Ask any question about the professor, get an LLM answer

---

## Scraping Sources
- **Reddit**: UMD subreddit, via PRAW (requires credentials)
- **Coursicle**: Public professor review pages
- **RateMyProfessors (RMP)**: Uses Selenium and Chromium (runs in Docker)

---

## Privacy & Security
- **Never commit `.env` files or real credentials**
- `.gitignore` is set up to exclude all secrets, build artifacts, and IDE files
- Store your Reddit and Gemini API keys in the appropriate `.env` files (see below)

---

## Developer Setup & Usage

### 1. Clone the Repository
```sh
git clone https://github.com/BhaveshThapar/umd-professor-analyzer.git
cd umd-professor-analyzer
```

### 2. Environment Variables
- **Create a file at `scrapers/.env` with the following content (do NOT commit this file to git):**
```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT=your_user_agent
```
- **Create a `.env` in the project root for Gemini:**
```
GOOGLE_API_KEY=your_gemini_api_key
```
- The `.env` files are already in `.gitignore`.

### 3. Build and Start All Services
```sh
docker-compose up --build
```
This will start the backend (Spring Boot), frontend (React), NLP microservice (FastAPI), PostgreSQL, Selenium, and the scrapers container.

### 4. Use the Web App
- Open your browser and go to: [http://localhost:3000](http://localhost:3000)
- Use the search bar to search for a professor (e.g., "John Smith").
- The app will display:
  - Professor info (from PlanetTerp)
  - AI-generated summary, tags, skills, and sentiment (from NLP microservice)
  - All reviews (from Reddit, Coursicle, RMP)
  - Sentiment trend, tags, skills, and toxicity warning if applicable
  - Q&A: Ask any question about the professor

### 5. (Optional) Manually Scrape Reviews for a Professor
If you want to force scraping, run:
- **Reddit:**
  ```sh
  docker-compose run --rm scrapers python main.py reddit "John Smith"
  ```
- **Coursicle:**
  ```sh
  docker-compose run --rm scrapers python main.py coursicle "John Smith"
  ```
- **RateMyProfessors (RMP):**
  ```sh
  docker-compose run --rm scrapers python main.py rmp "John Smith"
  ```

---

## Database Schema
See `db/init.sql` for details. Main tables:
- `professor` (id, name, department, avg_planetterp_gpa, avg_rating)
- `review` (id, professor_id, source, raw_text, semester, timestamp)
- `nlp_summary` (id, professor_id, summary, tags, tone_score, last_updated)

---

## Tech Stack
- **Frontend:** React, Tailwind CSS
- **Backend:** Spring Boot (Java), Maven, RestTemplate, JDBC
- **Scrapers:** Python 3.11, praw, requests, beautifulsoup4, selenium, python-dotenv, psycopg2-binary
- **NLP Service:** FastAPI, google-generativeai (Gemini API)
- **Database:** PostgreSQL 15
- **Containerization:** Docker, Docker Compose

---

## Troubleshooting
- For `Unknown source.`, check your command and ensure the source is one of: `reddit`, `coursicle`, `rmp`.
- For Selenium/Chromium errors, ensure you have rebuilt the scrapers image and Selenium service is running.
- For Gemini API errors, check your `GOOGLE_API_KEY` in `.env` and model name in `nlp_service/main.py`.
- For other issues, check your `.env` files and Docker logs.

---

## Contributing & Customization
- Fork the repo and open a PR!
- You can add new review sources, NLP features, or UI improvements.
- For production, restrict CORS and secure your API keys.

---

## Disclaimer
This project is for educational purposes. Respect the Terms of Service of all third-party sites (PlanetTerp, Reddit, Coursicle, RMP). Do not use for commercial purposes.