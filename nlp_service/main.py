from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. For prod, use ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def call_gemini(prompt, max_tokens=256, temperature=0.7):
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
    )
    return response.text.strip()

@app.post("/summarize")
def summarize(reviews: List[str] = Body(...)):
    text = " ".join(reviews)
    if not text.strip():
        return {"summary": None}
    prompt = (
        "You are an expert education analyst. Read the following student reviews about a university professor. "
        "Write a concise, unbiased summary (2-3 sentences) that highlights the professor's teaching style, grading approach, strengths, weaknesses, and any recurring themes. "
        "Avoid generic statements. Be specific and use evidence from the reviews. If sentiment is mixed, reflect that nuance.\n\n"
        f"Reviews:\n{text}\n\nSummary:"
    )
    summary = call_gemini(prompt, max_tokens=120)
    return {"summary": summary}

@app.post("/tags")
def extract_tags(reviews: List[str] = Body(...)):
    text = " ".join(reviews)
    if not text.strip():
        return {"tags": []}
    prompt = (
        "You are analyzing student reviews for a university professor. "
        "Extract 3-7 descriptive tags or short phrases that capture the main themes, teaching style, grading policies, and student experiences. "
        "Tags should be specific (e.g., 'tough grader', 'group projects', 'helpful during office hours', 'no curves', 'engaging lectures', 'strict attendance'). "
        "Return only a comma-separated list of tags, no explanations.\n\n"
        f"Reviews:\n{text}\n\nTags:"
    )
    tags_str = call_gemini(prompt, max_tokens=60)
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    return {"tags": tags}

@app.post("/skills")
def extract_skills(reviews: List[str] = Body(...)):
    text = " ".join(reviews)
    if not text.strip():
        return {"skills": []}
    prompt = (
        "Based on the following student reviews, list any skills, topics, or concepts that this professor emphasizes in their teaching. "
        "Include both technical and soft skills (e.g., 'algorithms', 'critical thinking', 'teamwork', 'public speaking'). "
        "Return only a comma-separated list, no explanations.\n\n"
        f"Reviews:\n{text}\n\nSkills:"
    )
    skills_str = call_gemini(prompt, max_tokens=60)
    skills = [s.strip() for s in skills_str.split(",") if s.strip()]
    return {"skills": skills}

@app.post("/sentiment")
def sentiment(reviews: List[str] = Body(...)):
    text = " ".join(reviews)
    if not text.strip():
        return {"sentiment": None, "explanation": None}
    prompt = (
        "Analyze the overall sentiment of these student reviews about a university professor. "
        "Is the sentiment positive, negative, or mixed? Assign a score from 0 (very negative) to 1 (very positive). "
        "Then, provide a one-sentence explanation that justifies the score, referencing specific aspects (e.g., 'Students praise the professor's clarity but dislike the heavy workload.').\n\n"
        f"Reviews:\n{text}\n\nScore and Explanation:"
    )
    result = call_gemini(prompt, max_tokens=80)
    score, explanation = None, None
    if "Score:" in result:
        parts = result.split("Score:")[1].split("Explanation:")
        try:
            score = float(parts[0].strip().replace(",", ".")[:4]) if parts[0].strip() else None
        except Exception:
            score = None
        explanation = parts[1].strip() if len(parts) > 1 else None
    else:
        explanation = result.strip()
    return {"sentiment": score, "explanation": explanation}

@app.post("/toxicity")
def toxicity(reviews: List[str] = Body(...)):
    text = " ".join(reviews)
    if not text.strip():
        return {"toxic": False}
    prompt = (
        "Review the following student comments about a university professor. "
        "Are any of these reviews sarcastic, toxic, offensive, or inappropriate for academic decision-making? "
        "Answer only 'Yes' or 'No'.\n\n"
        f"Reviews:\n{text}\n\nToxic:"
    )
    result = call_gemini(prompt, max_tokens=5)
    return {"toxic": "yes" in result.lower()}

@app.post("/qa")
def qa(reviews: List[str] = Body(...), question: Optional[str] = Body(None)):
    text = " ".join(reviews)
    if not text.strip() or not question:
        return {"answer": None}
    prompt = (
        "You are an expert education analyst. Based on the following student reviews, answer the user's question as specifically and concisely as possible. "
        "If the answer is not present in the reviews, say 'Not enough information in the reviews.'\n\n"
        f"Question: {question}\n\nReviews:\n{text}\n\nAnswer:"
    )
    answer = call_gemini(prompt, max_tokens=120)
    return {"answer": answer.strip()} 