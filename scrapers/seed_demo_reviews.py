import psycopg2
from datetime import datetime

PROFESSOR_NAME = "John Smith"
DEPARTMENT = "CMSC"
REVIEWS = [
    ("reddit", "Challenging but fair. Weekly quizzes and lots of projects.", "Fall 2023"),
    ("rmp", "Explains concepts well, but grading is tough.", "Spring 2023"),
    ("coursicle", "Lots of group work, but learned a lot.", "Fall 2022"),
    ("reddit", "No curves, but very helpful during office hours.", "Spring 2022"),
]

DB_CONFIG = dict(
    dbname="umdprof",
    user="umdprof",
    password="umdprof",
    host="db",
    port=5432
)

def seed_demo_reviews():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO professor (name, department, avg_planetterp_gpa, avg_rating)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (name) DO NOTHING;
    """, (PROFESSOR_NAME, DEPARTMENT, 2.85, 3.5))
    cur.execute("SELECT id FROM professor WHERE name = %s", (PROFESSOR_NAME,))
    professor_id = cur.fetchone()[0]
    for source, text, semester in REVIEWS:
        cur.execute("""
            INSERT INTO review (professor_id, source, raw_text, semester, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (professor_id, source, text, semester, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()
    print("Seeded demo reviews for", PROFESSOR_NAME)

if __name__ == "__main__":
    seed_demo_reviews() 