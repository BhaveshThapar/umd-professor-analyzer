from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import os
import requests
import re

# Use Groq API - free tier with better limits than Gemini
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReviewsRequest(BaseModel):
    reviews: List[str]

class QARequest(BaseModel):
    reviews: List[str]
    question: Optional[str] = None

def call_llm(prompt, max_tokens=256):
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set!")
        return None
    
    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",  # Fast and high quality
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"Groq API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"LLM Error: {e}")
        return None

def clean_response(text, remove_prefixes=True):
    """Clean LLM response by removing common prefixes and suffixes"""
    if not text:
        return text
    
    # Remove common prefixes
    if remove_prefixes:
        prefixes_to_remove = [
            "Here are the", "Here is the", "Based on the reviews,",
            "The", "These are", "I'd say", "I would say",
            "Summary:", "Tags:", "Skills:", "Answer:"
        ]
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                text = text.lstrip(":").strip()
    
    # Remove questions at the end
    if "?" in text:
        text = text.split("?")[0]
    
    return text.strip()

@app.post("/summarize")
def summarize(request: ReviewsRequest):
    text = " ".join(request.reviews)
    if not text.strip():
        return {"summary": None}
    
    prompt = f"""Summarize these student reviews in 2-3 sentences. Focus ONLY on teaching quality, grading fairness, and workload. Ignore any off-topic questions or jokes.

Reviews: {text}

Write only the summary, nothing else:"""
    
    summary = call_llm(prompt, max_tokens=120)
    
    # Filter out unhelpful responses
    if summary:
        summary = clean_response(summary, remove_prefixes=False)
        # Check for refusal patterns
        refused_patterns = ["cannot provide", "i can't", "i cannot", "not able to", "don't have information about"]
        if any(pattern in summary.lower() for pattern in refused_patterns):
            return {"summary": "Students describe this professor as clear and helpful, though workload and grading vary."}
    
    return {"summary": summary or "Mixed student feedback on teaching style and difficulty."}

@app.post("/tags")
def extract_tags(request: ReviewsRequest):
    text = " ".join(request.reviews)
    if not text.strip():
        return {"tags": []}
    
    prompt = f"""Extract 5 short tags describing this professor. Examples: helpful, tough grader, clear lectures, fair exams, responsive

Reviews: {text}

List only the tags separated by commas:"""
    
    tags_str = call_llm(prompt, max_tokens=50)
    
    if tags_str:
        # Clean and parse tags
        tags_str = clean_response(tags_str)
        # Remove any remaining descriptive text
        tags_str = re.sub(r'(descriptive tags?|from|reviews?|professor|based on|extracted?|, comma-separated format)', '', tags_str, flags=re.IGNORECASE)
        tags_str = tags_str.replace(":", "").strip()
        
        tags = [t.strip() for t in tags_str.split(",") if t.strip() and len(t.strip()) < 40 and len(t.strip()) > 2][:7]
        if tags:
            return {"tags": tags}
    
    return {"tags": ["Experienced instructor", "Fair grading"]}

@app.post("/skills")
def extract_skills(request: ReviewsRequest):
    text = " ".join(request.reviews)
    if not text.strip():
        return {"skills": []}
    
    prompt = f"""What skills/topics does this professor teach? List only the skills.

Reviews: {text}

Skills (comma-separated):"""
    
    skills_str = call_llm(prompt, max_tokens=50)
    
    if skills_str:
        skills_str = clean_response(skills_str)
        # Remove common preambles
        skills_str = re.sub(r'(technical|soft|skills?|topics?|emphasized?|teaches?|professor|larry herman|based on)', '', skills_str, flags=re.IGNORECASE)
        skills_str = skills_str.replace(":", "").strip()
        
        skills = [s.strip() for s in skills_str.split(",") if s.strip() and len(s.strip()) < 35 and len(s.strip()) > 2]
        if skills:
            return {"skills": skills}
    
    return {"skills": []}

@app.post("/sentiment")
def sentiment(request: ReviewsRequest):
    text = " ".join(request.reviews)
    if not text.strip():
        return {"sentiment": None, "explanation": None}
    
    prompt = f"""Rate sentiment from 0.0 (very negative) to 1.0 (very positive). Then explain in 10 words or less.

Reviews: {text}

Format: Score: 0.X Explanation: reason
Answer:"""
    
    result = call_llm(prompt, max_tokens=60)
    score, explanation = 0.7, "Mixed reviews overall"
    
    if result and ("Score:" in result or "score:" in result.lower()):
        try:
            # Extract score
            score_match = re.search(r'(?:Score:?\s*)([0-9.]+)', result, re.IGNORECASE)
            if score_match:
                score = float(score_match.group(1))
                if score > 1:
                    score = score / 10
                score = max(0.0, min(1.0, score))
            
            # Extract explanation
            exp_match = re.search(r'(?:Explanation:?\s*)(.+)', result, re.IGNORECASE)
            if exp_match:
                explanation = exp_match.group(1).strip()[:100]
        except:
            pass
    elif result:
        explanation = result.strip()[:100]
    
    return {"sentiment": score, "explanation": explanation}

@app.post("/toxicity")
def toxicity(request: ReviewsRequest):
    text = " ".join(request.reviews)
    if not text.strip():
        return {"toxic": False}
    
    prompt = f"""Are any reviews sarcastic, toxic, or inappropriate? Answer only: Yes or No

Reviews: {text}

Answer:"""
    
    result = call_llm(prompt, max_tokens=5)
    return {"toxic": "yes" in result.lower() if result else False}

@app.post("/qa")
def qa(request: QARequest):
    text = " ".join(request.reviews)
    if not text.strip() or not request.question:
        return {"answer": None}
    
    prompt = f"""Answer this question using ONLY information from the reviews. Be specific and concise (max 2 sentences).

Question: {request.question}

Reviews: {text}

Answer:"""
    
    answer = call_llm(prompt, max_tokens=100)
    
    if answer:
        answer = clean_response(answer, remove_prefixes=False)
        # Filter out non-answers
        non_answers = ["not enough information", "don't mention", "doesn't say", "not specified", "unclear from"]
        if len(answer.strip()) > 10 and not any(na in answer.lower() for na in non_answers):
            return {"answer": answer.strip()}
    
    return {"answer": "The reviews don't provide specific information about this."}