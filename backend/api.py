import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from embedding_search import *
from markupsafe import Markup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


directories = ["databases", "templates", "html_storages", "uploads"]
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)

class SearchRequest(BaseModel):
    query: str
    n: int
    context: str
    use_highlight: bool = False
    confidence: Optional[float] = None

@app.post("/search/")
async def search(request: SearchRequest):
    upload_path = os.path.join('uploads', 'context_file.txt')
    with open(upload_path, 'w', encoding='utf-8') as tmp_file:
        tmp_file.write(request.context)
    
    tmp_filename = os.path.basename(upload_path)

    try:
        if request.use_highlight:
            if request.confidence is None:
                raise HTTPException(status_code=400, detail="Confidence value must be provided when highlight is enabled.")
            
            run_highlight(tmp_filename, request.query, request.confidence)
            
            try:
                html_filename = f"html_storages/{tmp_filename}.html"
                with open(html_filename, 'r') as f:
                    result_html = f.read()
                if os.path.exists(html_filename):
                    os.remove(html_filename)
                return {"result_html": result_html}
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="Generated HTML file not found.")
        
        else:
            relevant_sentences = run_get_relevant(tmp_filename, request.query, request.n)
            if relevant_sentences:
                return {"sentences": relevant_sentences}
            else:
                raise HTTPException(status_code=404, detail="No relevant sentences found.")
    
    finally:
        if os.path.exists(upload_path):
            os.remove(upload_path)


@app.get("/")
async def root():
    return {"message": "FastAPI application is running!"}
