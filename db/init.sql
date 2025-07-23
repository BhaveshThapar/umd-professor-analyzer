CREATE TABLE professor (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  department TEXT,
  avg_planetterp_gpa FLOAT,
  avg_rating FLOAT
);

CREATE TABLE review (
  id SERIAL PRIMARY KEY,
  professor_id INT REFERENCES professor(id),
  source TEXT CHECK (source IN ('reddit', 'rmp', 'coursicle')),
  raw_text TEXT,
  semester TEXT,
  timestamp TIMESTAMP
);

CREATE TABLE nlp_summary (
  id SERIAL PRIMARY KEY,
  professor_id INT REFERENCES professor(id),
  summary TEXT,
  tags TEXT[],
  tone_score FLOAT,
  last_updated TIMESTAMP
); 