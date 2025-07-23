# UMD Professor Analyzer

A full-stack platform for UMD students to search professors, view grade data, read summarized student opinions, and see AI-generated insights.

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
- The `.env` file is already in `scrapers/.gitignore`.

### 3. Build and Start All Services
```sh
docker-compose up --build
```
This will start the backend (Spring Boot), frontend (React), NLP microservice (FastAPI), PostgreSQL, and the scrapers container.

### 4. Scrape and Seed Reviews for a Professor
Run these commands to fetch and store reviews for a professor (e.g., "John Smith"):
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

### 5. Use the Web App
- Open your browser and go to: [http://localhost:3000](http://localhost:3000)
- Use the search bar to search for a professor (e.g., "John Smith").
- The app will display:
  - Professor info (from PlanetTerp)
  - AI-generated summary, tags, and sentiment (from NLP microservice)
  - All reviews (from Reddit, Coursicle, RMP)
  - Sentiment trend and tags

---

## Scraper Notes
- **Reddit credentials** must be in `scrapers/.env`.
- **RMP scraping** uses Selenium and Chromium. The Docker image installs all required dependencies.
- **Coursicle and RMP** scraping may not work for every professor due to site structure or anti-bot measures.
- If you see errors about Chromium or Selenium, rebuild the scrapers image:
  ```sh
  docker-compose build scrapers
  ```

---

## Troubleshooting
- For `Unknown source.`, check your command and ensure the source is one of: `reddit`, `coursicle`, `rmp`.
- For Selenium/Chromium errors, ensure you have rebuilt the scrapers image.
- For other issues, check your `.env` and Docker logs.

---

## Service Details
- **Backend**: Java 21, Maven, connects to DB, exposes REST API
- **Frontend**: React, Tailwind, served via `serve`
- **Scrapers**: Python 3.11, run with `python main.py [reddit|coursicle|rmp] "Professor Name"`
- **NLP Service**: FastAPI, endpoints for `/summarize`, `/tags`, `/sentiment`

## Database Schema
See `db/init.sql` for tables: `professor`, `review`, `nlp_summary`

---