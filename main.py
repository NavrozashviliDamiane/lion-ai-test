import json
import redis
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from openai import OpenAI
import hashlib
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, OPENAI_API_KEY, OPENAI_MODEL, AUTHOR_ID
from database import fetch_author_data

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/chat_ai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lion Trans Chat AI", version="1.0.0")

client = OpenAI(api_key=OPENAI_API_KEY)

try:
    if REDIS_PASSWORD:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
    else:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
    redis_client.ping()
    logger.info("[OK] Redis connected")
except Exception as e:
    logger.warning(f"[WARN] Redis connection failed: {e}")
    redis_client = None


class ContextBundle:
    def __init__(self):
        self.agent_context = {}
        self.fields_context = {}
        self.query_map = {}
        self.load_contexts()
    
    def load_contexts(self):
        try:
            with open("agent_context_bundle.json", "r", encoding="utf-8") as f:
                self.agent_context = json.load(f)
            
            with open("fields_context.json", "r", encoding="utf-8") as f:
                self.fields_context = json.load(f)
            
            with open("query_map.json", "r", encoding="utf-8") as f:
                self.query_map = json.load(f)
            
            logger.info("[OK] Context bundles loaded successfully")
        except Exception as e:
            logger.error(f"[ERROR] Error loading context bundles: {e}")
            raise

context_bundle = ContextBundle()


def get_field_by_name(field_name: str) -> Optional[Dict]:
    for field in context_bundle.fields_context.get("fields", []):
        if field.get("field_name") == field_name:
            return field
    return None


def get_intent_by_name(intent_name: str) -> Optional[Dict]:
    for intent in context_bundle.query_map.get("query_map", []):
        if intent.get("intent") == intent_name:
            return intent
    return None


def extract_vin_from_query(query: str) -> Optional[str]:
    import re
    vin_pattern = r'[A-HJ-NPR-Z0-9]{17}'
    match = re.search(vin_pattern, query)
    if match:
        vin = match.group(0).strip()
        print(f"[DEBUG] Extracted VIN: {vin}")
        return vin
    print(f"[DEBUG] No VIN found in query: {query}")
    return None


def extract_intent_and_fields(user_query: str) -> Dict[str, Any]:
    system_prompt = """You are an intent detection system for a Georgian car dealer management chatbot.
    
Analyze the user's Georgian query and return a JSON object with:
- "intent": The most likely intent from the available intents
- "detected_fields": List of field names that are relevant to this query
- "confidence": Confidence score (0-1)
- "parameters": Any extracted parameters (like VIN, dates, numbers)

Available intents:
- count_all_my_cars
- count_by_record_status
- sum_total_balance
- cars_with_positive_balance
- vehicle_by_vin
- vehicle_finance_by_vin
- group_by_make_model_year
- cars_by_location_or_stage
- records_by_period
- missing_documents_or_title

Respond ONLY with valid JSON, no additional text."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {user_query}"}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            if "{" in result_text and "}" in result_text:
                start = result_text.find("{")
                end = result_text.rfind("}") + 1
                result = json.loads(result_text[start:end])
            else:
                result = {
                    "intent": "count_all_my_cars",
                    "detected_fields": ["author"],
                    "confidence": 0.5,
                    "parameters": {}
                }
        
        vin = extract_vin_from_query(user_query)
        if vin and result.get("intent") in ["vehicle_by_vin", "vehicle_finance_by_vin"]:
            result["parameters"]["vin"] = vin
        
        return result
    except Exception as e:
        print(f"Error in intent extraction: {e}")
        return {
            "intent": "count_all_my_cars",
            "detected_fields": ["author"],
            "confidence": 0.0,
            "parameters": {}
        }


def filter_records_by_author(records: List[Dict], author_id: int) -> List[Dict]:
    return [r for r in records if r.get("author_id") == author_id or r.get("author") == str(author_id)]


def format_car_record(record: Dict) -> Dict:
    """Format a car record with 10 essential fields for frontend display"""
    return {
        "id": record.get("id"),
        "vin": record.get("vin"),
        "manufacturer": record.get("manufacturer"),
        "model": record.get("model"),
        "year": record.get("year"),
        "warehouse": record.get("warehouse"),
        "record_status": record.get("record_status"),
        "total_pay": float(record.get("f1", 0) or 0),
        "balance": float(record.get("f2", 0) or 0),
        "date": record.get("date")
    }


def execute_intent(intent: str, records: List[Dict], parameters: Dict = None) -> Any:
    if not records:
        return {"error": "No records found for this dealer", "records": []}
    
    try:
        if intent == "count_all_my_cars":
            return {
                "total": len(records),
                "status": "success",
                "records": [format_car_record(r) for r in records]
            }
        
        elif intent == "count_by_record_status":
            status_counts = {}
            status_records = {}
            for record in records:
                status = record.get("record_status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
                if status not in status_records:
                    status_records[status] = []
                status_records[status].append(format_car_record(record))
            
            return {
                "by_status": status_counts,
                "total": len(records),
                "records_by_status": status_records
            }
        
        elif intent == "sum_total_balance":
            total_balance = sum(float(r.get("f2", 0) or 0) for r in records)
            return {
                "total_balance": total_balance,
                "currency": "GEL",
                "records": [format_car_record(r) for r in records if float(r.get("f2", 0) or 0) > 0]
            }
        
        elif intent == "cars_with_positive_balance":
            cars = [format_car_record(r) for r in records if float(r.get("f2", 0) or 0) > 0]
            return {
                "cars": cars,
                "count": len(cars),
                "records": cars
            }
        
        elif intent == "vehicle_by_vin":
            vin = parameters.get("vin") if parameters else None
            if not vin:
                return {"error": "VIN not provided", "records": []}
            
            print(f"[DEBUG] Searching for VIN: {vin}")
            print(f"[DEBUG] Total records to search: {len(records)}")
            
            for record in records:
                record_vin = record.get("vin", "").strip().upper()
                search_vin = vin.strip().upper()
                
                if record_vin == search_vin:
                    print(f"[DEBUG] VIN FOUND: {record_vin}")
                    return {
                        "vehicle": record,
                        "found": True,
                        "records": [format_car_record(record)]
                    }
            
            print(f"[DEBUG] VIN NOT FOUND: {vin}")
            print(f"[DEBUG] Available VINs: {[r.get('vin') for r in records[:5]]}")
            return {"found": False, "error": f"Vehicle with VIN {vin} not found", "records": []}
        
        elif intent == "vehicle_finance_by_vin":
            vin = parameters.get("vin") if parameters else None
            if not vin:
                return {"error": "VIN not provided", "records": []}
            
            for record in records:
                if record.get("vin", "").upper() == vin.upper():
                    f1 = float(record.get("f1", 0) or 0)
                    f2 = float(record.get("f2", 0) or 0)
                    paid = sum(float(record.get(f"pm_{i}", 0) or 0) for i in range(1, 6))
                    
                    return {
                        "vin": record.get("vin"),
                        "total_pay": f1,
                        "paid": paid,
                        "balance": f2,
                        "payments": {
                            "pm_1": float(record.get("pm_1", 0) or 0),
                            "pm_2": float(record.get("pm_2", 0) or 0),
                            "pm_3": float(record.get("pm_3", 0) or 0),
                            "pm_4": float(record.get("pm_4", 0) or 0),
                            "pm_5": float(record.get("pm_5", 0) or 0),
                        },
                        "records": [format_car_record(record)]
                    }
            return {"found": False, "error": f"Vehicle with VIN {vin} not found", "records": []}
        
        elif intent == "group_by_make_model_year":
            grouped = {}
            grouped_records = {}
            for record in records:
                make = record.get("manufacturer", "Unknown")
                model = record.get("model", "Unknown")
                year = record.get("year", "Unknown")
                key = f"{make} {model} ({year})"
                grouped[key] = grouped.get(key, 0) + 1
                if key not in grouped_records:
                    grouped_records[key] = []
                grouped_records[key].append(format_car_record(record))
            
            return {
                "grouped": grouped,
                "total": len(records),
                "records_by_group": grouped_records
            }
        
        elif intent == "cars_by_location_or_stage":
            locations = {}
            for record in records:
                warehouse = record.get("warehouse", "Unknown")
                if warehouse not in locations:
                    locations[warehouse] = []
                locations[warehouse].append(format_car_record(record))
            
            return {
                "by_location": {k: len(v) for k, v in locations.items()},
                "total": len(records),
                "records_by_location": locations
            }
        
        elif intent == "records_by_period":
            period = parameters.get("period", "month") if parameters else "month"
            
            if period == "month":
                cutoff = datetime.now() - timedelta(days=30)
            elif period == "week":
                cutoff = datetime.now() - timedelta(days=7)
            elif period == "year":
                cutoff = datetime.now() - timedelta(days=365)
            else:
                cutoff = datetime.now() - timedelta(days=30)
            
            filtered = []
            for record in records:
                date_str = record.get("date", "")
                try:
                    record_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if record_date >= cutoff:
                        filtered.append(record)
                except:
                    pass
            
            return {
                "records": [format_car_record(r) for r in filtered],
                "count": len(filtered),
                "period": period
            }
        
        elif intent == "missing_documents_or_title":
            missing = [r for r in records if not r.get("title_received")]
            return {
                "missing_title": [format_car_record(r) for r in missing],
                "count": len(missing),
                "records": [format_car_record(r) for r in missing]
            }
        
        else:
            return {"error": f"Unknown intent: {intent}", "records": []}
    
    except Exception as e:
        return {"error": str(e), "records": []}


def generate_response(intent: str, result: Dict, user_query: str) -> str:
    if "error" in result and not result.get("found") and not result.get("records"):
        return f"❌ {result['error']}"
    
    try:
        vehicle_info = {}
        if result.get("vehicle"):
            vehicle = result.get("vehicle")
            vehicle_info = {
                "vin": vehicle.get("vin"),
                "manufacturer": vehicle.get("manufacturer"),
                "model": vehicle.get("model"),
                "year": vehicle.get("year"),
                "warehouse": vehicle.get("warehouse"),
                "record_status": vehicle.get("record_status")
            }
        
        result_summary = {
            "intent": intent,
            "total": result.get("total", 0),
            "count": result.get("count", 0),
            "total_balance": result.get("total_balance"),
            "currency": result.get("currency"),
            "period": result.get("period"),
            "by_status": result.get("by_status"),
            "grouped": result.get("grouped"),
            "by_location": result.get("by_location"),
            "found": result.get("found"),
            "vin": result.get("vin"),
            "total_pay": result.get("total_pay"),
            "paid": result.get("paid"),
            "balance": result.get("balance"),
            "vehicle": vehicle_info if vehicle_info else None,
        }
        
        result_summary = {k: v for k, v in result_summary.items() if v is not None}
        
        print(f"[DEBUG] Response summary: {result_summary}")
        
        system_prompt = f"""You are a helpful Georgian-speaking car dealer assistant.

The user asked: {user_query}
The system detected intent: {intent}
The query result summary is: {json.dumps(result_summary, ensure_ascii=False, indent=2)}

Generate a natural, concise Georgian response that:
1. Answers the user's question directly
2. Presents numbers and data clearly
3. Is business-appropriate and helpful
4. Uses Georgian language naturally
5. Keep it brief (1-3 sentences max)

Respond in Georgian only."""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Please provide the response in Georgian."}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Response generation error: {str(e)}"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    author_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    intent: str
    detected_fields: List[str]
    cached: bool
    timestamp: str
    records: Optional[List[Dict]] = []


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_query = request.messages[-1].content if request.messages else ""
    author_id = request.author_id or AUTHOR_ID
    
    logger.info(f"[CHAT] Query from author_id={author_id}: {user_query}")
    
    if not user_query:
        logger.warning(f"[CHAT] Empty query from author_id={author_id}")
        raise HTTPException(status_code=400, detail="Empty query")
    
    cache_key = f"chat:{hashlib.md5(f'{author_id}:{user_query}'.encode()).hexdigest()}"
    
    if redis_client:
        try:
            cached_response = redis_client.get(cache_key)
            if cached_response:
                logger.info(f"[CACHE] HIT for query: {user_query[:50]}...")
                cached_data = json.loads(cached_response)
                cached_data["cached"] = True
                return ChatResponse(**cached_data)
        except Exception as e:
            logger.error(f"[CACHE] Read error: {e}")
    
    logger.info(f"[DB] Fetching data for author_id={author_id}")
    try:
        records = fetch_author_data(author_id)
        logger.info(f"[DB] Retrieved {len(records)} records")
    except Exception as e:
        logger.error(f"[DB] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    filtered_records = filter_records_by_author(records, author_id)
    logger.info(f"[FILTER] Filtered to {len(filtered_records)} records for author_id={author_id}")
    
    logger.info(f"[INTENT] Detecting intent for query: {user_query[:50]}...")
    intent_result = extract_intent_and_fields(user_query)
    intent = intent_result.get("intent", "count_all_my_cars")
    detected_fields = intent_result.get("detected_fields", [])
    parameters = intent_result.get("parameters", {})
    logger.info(f"[INTENT] Detected: {intent}, Fields: {detected_fields}, Params: {parameters}")
    
    logger.info(f"[EXECUTE] Executing intent: {intent}")
    query_result = execute_intent(intent, filtered_records, parameters)
    logger.info(f"[EXECUTE] Result records count: {len(query_result.get('records', []))}")
    
    logger.info(f"[RESPONSE] Generating response for intent: {intent}")
    response_text = generate_response(intent, query_result, user_query)
    
    records_data = query_result.get("records", [])
    
    response_data = {
        "response": response_text,
        "intent": intent,
        "detected_fields": detected_fields,
        "cached": False,
        "timestamp": datetime.now().isoformat(),
        "records": records_data
    }
    
    if redis_client:
        try:
            redis_client.setex(cache_key, 3600, json.dumps(response_data, ensure_ascii=False))
            logger.info(f"[CACHE] STORED result for query: {user_query[:50]}...")
        except Exception as e:
            logger.error(f"[CACHE] Write error: {e}")
    
    logger.info(f"[SUCCESS] Query completed: {user_query[:50]}... -> {intent}")
    return ChatResponse(**response_data)


@app.get("/context-guidance")
async def context_guidance(query: str, author_id: Optional[int] = None):
    author_id = author_id or AUTHOR_ID
    
    intent_result = extract_intent_and_fields(query)
    
    return {
        "query": query,
        "detected_intent": intent_result.get("intent"),
        "confidence": intent_result.get("confidence"),
        "detected_fields": intent_result.get("detected_fields"),
        "parameters": intent_result.get("parameters"),
        "intent_details": get_intent_by_name(intent_result.get("intent")),
        "field_details": [
            get_field_by_name(field) for field in intent_result.get("detected_fields", [])
        ]
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "redis": "connected" if redis_client else "disconnected",
        "contexts_loaded": bool(context_bundle.agent_context)
    }


@app.get("/")
async def root():
    return {
        "name": "Lion Trans Chat AI",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat - Send a Georgian query",
            "context_guidance": "GET /context-guidance - Get intent and field detection",
            "health": "GET /health - Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
