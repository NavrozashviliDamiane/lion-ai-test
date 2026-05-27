from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, AUTHOR_ID
from embeddings import store_records_in_redis, store_field_embeddings_in_redis, search_records_by_intent
from embeddings import get_redis_connection
from field_metadata import get_field_context, get_field_mapping
import logging
from datetime import datetime
import tiktoken

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

encoding = tiktoken.encoding_for_model("gpt-4o")

GPT4O_INPUT_COST_PER_1K = 0.005
GPT4O_OUTPUT_COST_PER_1K = 0.015

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken"""
    try:
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}")
        return 0

def calculate_cost(input_tokens: int, output_tokens: int) -> dict:
    """Calculate cost in USD for input and output tokens"""
    input_cost = (input_tokens / 1000) * GPT4O_INPUT_COST_PER_1K
    output_cost = (output_tokens / 1000) * GPT4O_OUTPUT_COST_PER_1K
    total_cost = input_cost + output_cost
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6)
    }

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

class TokenCost(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float

class ChatResponse(BaseModel):
    response: str
    context_records: List[dict]
    model: str
    tokens: TokenCost

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
        author_id = request.author_id
        
        logger.info(f"=== CHAT REQUEST START ===")
        logger.info(f"Author ID: {author_id}")
        logger.info(f"User Message: {user_message[:200]}..." if len(user_message) > 200 else f"User Message: {user_message}")
        logger.info(f"Total Messages in Conversation: {len(request.messages)}")
        
        context_results = search_records_by_intent(user_message, author_id, top_k=3)
        
        logger.info(f"Intent Search Results: {len(context_results)} records found")
        for idx, result in enumerate(context_results):
            logger.info(f"  Result {idx+1}: Record ID {result['record_id']}, Similarity: {result['similarity']:.2f}")
        
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

## ფორმატირების მოთხოვნები

ყოველი პასუხი უნდა იყოს GitHub-flavored Markdown ფორმატში:

- **bold** - ღირებულებებისა და ლეიბლებისთვის (თანხები, სტატუსები, მნიშვნელოვანი ველები)
- ## / ### - სექციების სათაურებისთვის (მაგ. ## ფინანსური ინფორმაცია)
- **-** ან **1.** - სიების ელემენტებისთვის
- | ცხრილები | - სტრუქტურირებული მონაცემებისთვის (გადახდები, ხარჯები, შედარება)
- \`კოდი\` - VIN კოდებისთვის, ID-ებისთვის, სპეციალური კოდებისთვის
- > ციტატები - შენიშვნებისა და გაფრთხილებებისთვის

## კონტენტი

{field_context}

{context_text}

## პასუხის წესები

- ყოველთვის უპასუხე **ქართულ ენაზე**
- გამოიყენე Markdown ფორმატირება ზემოთ აღწერილი წესების მიხედვით
- მკაფიო და კონკრეტული პასუხი
- დაფუძნებული მოწოდებულ კონტექსტზე
- თუ ინფორმაცია არ არის, გამოიყენე blockquote: > ინფორმაცია არ მოიძებნა"""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        logger.info(f"Calling OpenAI API with model: {OPENAI_MODEL}")
        
        input_tokens = sum(count_tokens(msg["content"]) for msg in messages)
        logger.info(f"Input Tokens: {input_tokens}")
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        output_tokens = count_tokens(ai_response)
        
        logger.info(f"OpenAI Response Length: {len(ai_response)} characters")
        logger.info(f"Output Tokens: {output_tokens}")
        logger.info(f"Response Preview: {ai_response[:150]}..." if len(ai_response) > 150 else f"Response: {ai_response}")
        
        token_cost = calculate_cost(input_tokens, output_tokens)
        logger.info(f"Token Cost Breakdown:")
        logger.info(f"  Input: {token_cost['input_tokens']} tokens = ${token_cost['input_cost']:.6f}")
        logger.info(f"  Output: {token_cost['output_tokens']} tokens = ${token_cost['output_cost']:.6f}")
        logger.info(f"  Total: {token_cost['total_tokens']} tokens = ${token_cost['total_cost']:.6f}")
        
        chat_response = ChatResponse(
            response=ai_response,
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
            model=OPENAI_MODEL,
            tokens=TokenCost(**token_cost)
        )
        
        logger.info(f"=== CHAT REQUEST COMPLETE ===")
        logger.info(f"Context Records Returned: {len(chat_response.context_records)}")
        
        return chat_response
    
    except Exception as e:
        logger.error(f"=== CHAT REQUEST ERROR ===")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error Message: {str(e)}")
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
