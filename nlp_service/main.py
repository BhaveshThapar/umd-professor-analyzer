from fastapi import FastAPI, Body
from typing import List

app = FastAPI()

@app.post("/summarize")
def summarize(reviews: List[str] = Body(...)):
    return {"summary": "[Stub] Summary of reviews."}

@app.post("/tags")
def extract_tags(reviews: List[str] = Body(...)):
    return {"tags": ["[Stub] tag1", "[Stub] tag2"]}

@app.post("/sentiment")
def sentiment(reviews: List[str] = Body(...)):
    return {"sentiment": 0.5} 