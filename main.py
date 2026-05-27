from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, AUTHOR_ID
from embeddings import store_records_in_redis, store_field_embeddings_in_redis, search_records_by_intent
from embeddings import get_redis_connection
from field_metadata import get_field_context, get_field_mapping

app = FastAPI(title="Lion AI Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=OPENAI_API_KEY)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    author_id: int = AUTHOR_ID

class ChatResponse(BaseModel):
    response: str
    context_records: List[dict]
    model: str

@app.on_event("startup")
async def startup_event():
    try:
        print("Initializing cache from database...")
        store_records_in_redis(AUTHOR_ID)
        print("Storing field embeddings for intent detection...")
        store_field_embeddings_in_redis()
        print("Cache initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize cache on startup: {e}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/clear-cache")
async def clear_cache(author_id: int = AUTHOR_ID):
    """Clear Redis cache for a specific author"""
    try:
        r = get_redis_connection()
        pattern = f"record:{author_id}:*"
        keys = r.keys(pattern)
        
        if keys:
            r.delete(*keys)
            print(f"Cleared {len(keys)} records from cache")
        
        return {"status": "ok", "cleared": len(keys)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear-all-cache")
async def clear_all_cache():
    """Clear all Redis cache"""
    try:
        r = get_redis_connection()
        r.flushdb()
        print("Cleared all cache")
        return {"status": "ok", "message": "All cache cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        user_message = request.messages[-1].content if request.messages else ""
        
        context_results = search_records_by_intent(user_message, request.author_id, top_k=3)
        
        field_context = get_field_context()
        field_mapping = get_field_mapping()
        
        context_text = ""
        if context_results:
            context_text = "\n\nრელევანტური ინფორმაცია ბაზიდან:\n"
            for result in context_results:
                context_text += f"\nჩანაწერი ID {result['record_id']} (მსგავსება: {result['similarity']:.2f}):\n"
                
                record = result['content']
                for key, value in record.items():
                    if value and key in field_mapping:
                        label = field_mapping[key]['label']
                        context_text += f"  • {label}: {value}\n"
                
                context_text += "\n"
        
        system_prompt = f"""შენ ხარ AI ასისტენტი მანქანების აუქციონისა და ლოგისტიკის მართვის სისტემისთვის.
შენ გაქვს წვდომა მანქანების ჩანაწერებსა და ტრანზაქციების მონაცემებზე.

ᲛᲜᲘᲨᲕᲜᲔᲚᲝᲕᲐᲜᲘ: ყოველთვის უპასუხე ქართულ ენაზე!

{field_context}

{context_text}

პასუხი უნდა იყოს:
- ქართულ ენაზე
- მკაფიო და კონკრეტული
- დაფუძნებული მოწოდებულ კონტექსტზე
- თუ ინფორმაცია არ არის, ეს მიუთითე"""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        return ChatResponse(
            response=response.choices[0].message.content,
            context_records=[
                {
                    "record_id": r["record_id"],
                    "similarity": r["similarity"],
                    "manufacturer": r["content"].get("manufacturer"),
                    "model": r["content"].get("model"),
                    "year": r["content"].get("year"),
                    "vin": r["content"].get("vin")
                }
                for r in context_results
            ],
            model=OPENAI_MODEL
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh-cache")
async def refresh_cache(author_id: int = AUTHOR_ID):
    try:
        store_records_in_redis(author_id)
        store_field_embeddings_in_redis()
        return {"status": "success", "message": f"Cache refreshed for author_id {author_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(query: str, author_id: int = AUTHOR_ID, top_k: int = 3):
    try:
        results = search_records_by_intent(query, author_id, top_k)
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
