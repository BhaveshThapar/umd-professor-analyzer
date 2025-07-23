# UMD Professor Analyzer

A full-stack platform for UMD students to search professors, view grade data, read summarized student opinions, and see AI-generated insights.

## .env Setup for Scrapers

**Create a file at `scrapers/.env` with the following content (do NOT commit this file to git):**

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT=your_user_agent
```

> **Note:** Never commit your `.env` file or any credentials to version control. The `.env` file is already in `scrapers/.gitignore`.

## Tech Stack
- **Backend:** Spring Boot (Java)
- **Frontend:** React.js + Tailwind CSS
- **Scraper/API:** Python (praw, requests, BeautifulSoup, Selenium, Chromium)
- **NLP Engine:** Python + FastAPI + transformers
- **DB:** PostgreSQL
- **Deployment:** Docker + Docker Compose

## Monorepo Structure
```
backend/        # Spring Boot backend
frontend/       # React + Tailwind frontend
scrapers/       # Python scrapers (Reddit, RMP, Coursicle)
nlp_service/    # FastAPI NLP microservice
/db/init.sql    # DB schema
```

## How to Use the Scrapers

### 1. Build All Services
```sh
docker-compose up --build
```

### 2. Run the Scrapers for a Professor
- **Reddit:**
  ```sh
  docker-compose run --rm scrapers python main.py reddit "Professor Name"
  ```
- **Coursicle:**
  ```sh
  docker-compose run --rm scrapers python main.py coursicle "Professor Name"
  ```
- **RateMyProfessors (RMP):**
  ```sh
  docker-compose run --rm scrapers python main.py rmp "Professor Name"
  ```

> **Note:**  
> If you see `Unknown source.`, make sure you typed the source exactly as above (`reddit`, `coursicle`, or `rmp`) and check for typos or extra spaces.

### 3. View Results
- Go to [http://localhost:3000](http://localhost:3000) and search for the professor.

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

## Customization
- Add your own endpoints, models, and logic in each service directory.
- Update Dockerfiles as needed for dependencies.

## Deployment
- All services are production-ready for Docker Compose
- Deploy to Render, Railway, Fly.io, or your own server

---