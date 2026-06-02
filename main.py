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
        self.business_rules = ""
        self.redis_rules = ""
        self.response_example = []
        self.lion_system = ""
        self.lion_intents = ""
        self.lion_fields = ""
        self.lion_finance_fields = ""
        self.lion_synonyms = ""
        self.lion_examples = ""
        self.response_rules = ""
        self.full_context = ""  # Combined context for all files
        self.load_contexts()
    
    def load_contexts(self):
        import os
        
        # List of files to load with their attribute names
        files_to_load = [
            ("lion_ai_rule.md", "business_rules"),
            ("redis_query_rules.md", "redis_rules"),
            ("response-example.json", "response_example", "json"),
            ("lion_system.md", "lion_system"),
            ("lion_intents.md", "lion_intents"),
            ("lion_fields.md", "lion_fields"),
            ("lion_finance-fields.md", "lion_finance_fields"),
            ("lion_synonyms.md", "lion_synonyms"),
            ("lion_examples.md", "lion_examples"),
            ("response-rules.md", "response_rules"),
        ]
        
        loaded_files = []
        missing_files = []
        
        for file_info in files_to_load:
            filename = file_info[0]
            attr_name = file_info[1]
            file_type = file_info[2] if len(file_info) > 2 else "text"
            
            try:
                if os.path.exists(filename):
                    if file_type == "json":
                        with open(filename, "r", encoding="utf-8") as f:
                            setattr(self, attr_name, json.load(f))
                    else:
                        with open(filename, "r", encoding="utf-8") as f:
                            setattr(self, attr_name, f.read())
                    loaded_files.append(filename)
                else:
                    missing_files.append(filename)
                    logger.warning(f"[WARN] Context file not found: {filename}")
            except Exception as e:
                missing_files.append(filename)
                logger.warning(f"[WARN] Error loading {filename}: {e}")
        
        if loaded_files:
            logger.info(f"[OK] Context loaded: {len(loaded_files)} files - {', '.join(loaded_files)}")
        
        if missing_files:
            logger.warning(f"[WARN] {len(missing_files)} context files missing: {', '.join(missing_files)}")
            logger.warning("[WARN] System will continue with available context. Some features may be limited.")
        
        # Build combined full context
        self._build_full_context()
    
    def _build_full_context(self):
        """Build a comprehensive context string with all loaded files"""
        context_sections = []
        
        if self.lion_system:
            context_sections.append(f"=== SYSTEM RULES ===\n{self.lion_system}\n")
        
        if self.lion_intents:
            context_sections.append(f"=== SUPPORTED INTENTS ===\n{self.lion_intents}\n")
        
        if self.lion_fields:
            context_sections.append(f"=== FIELD DEFINITIONS ===\n{self.lion_fields}\n")
        
        if self.lion_finance_fields:
            context_sections.append(f"=== FINANCIAL FIELDS ===\n{self.lion_finance_fields}\n")
        
        if self.lion_synonyms:
            context_sections.append(f"=== SYNONYMS & NORMALIZATION ===\n{self.lion_synonyms}\n")
        
        if self.lion_examples:
            context_sections.append(f"=== QUERY EXAMPLES ===\n{self.lion_examples}\n")
        
        if self.business_rules:
            context_sections.append(f"=== BUSINESS RULES ===\n{self.business_rules}\n")
        
        if self.response_rules:
            context_sections.append(f"=== RESPONSE RULES ===\n{self.response_rules}\n")
        
        if self.redis_rules:
            context_sections.append(f"=== REDIS CACHING RULES ===\n{self.redis_rules}\n")
        
        self.full_context = "\n".join(context_sections)

context_bundle = ContextBundle()


def get_response_example_structure() -> str:
    """Returns a formatted string showing the structure of response data"""
    if context_bundle.response_example:
        example = context_bundle.response_example[0]
        fields = list(example.keys())
        return f"Available fields: {', '.join(fields[:20])}..."
    return "No example data available"


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
    system_prompt = f"""You are an intent detection system for a Georgian car dealer management chatbot.

{context_bundle.full_context}

CRITICAL: You MUST only use these exact intents:
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

Analyze the user's Georgian query and return a JSON object with:
- "intent": MUST be one of the exact intents listed above
- "detected_fields": List of field names that are relevant to this query
- "confidence": Confidence score (0-1)
- "parameters": Any extracted parameters (like VIN, dates, numbers)

IMPORTANT: If you cannot determine the intent with confidence, return:
{{"intent": "count_all_my_cars", "detected_fields": ["author"], "confidence": 0.5, "parameters": {{}}}}

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
        
        # Validate intent
        result = validate_intent(result)
        
        return result
    except Exception as e:
        print(f"Error in intent extraction: {e}")
        return {
            "intent": "count_all_my_cars",
            "detected_fields": ["author"],
            "confidence": 0.0,
            "parameters": {}
        }


def validate_intent(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that the detected intent is in the list of supported intents"""
    valid_intents = [
        "count_all_my_cars",
        "count_by_record_status",
        "sum_total_balance",
        "cars_with_positive_balance",
        "vehicle_by_vin",
        "vehicle_finance_by_vin",
        "group_by_make_model_year",
        "cars_by_location_or_stage",
        "records_by_period",
        "missing_documents_or_title"
    ]
    
    intent = result.get("intent", "count_all_my_cars")
    
    if intent not in valid_intents:
        logger.warning(f"[INTENT] Invalid intent detected: {intent}. Defaulting to count_all_my_cars")
        result["intent"] = "count_all_my_cars"
        result["detected_fields"] = ["author"]
        result["confidence"] = 0.3
    
    return result


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
        return {"error": "No records found for this dealer"}
    
    try:
        if intent == "count_all_my_cars":
            return {
                "total": len(records),
                "status": "success"
            }
        
        elif intent == "count_by_record_status":
            status_counts = {}
            for record in records:
                status = record.get("record_status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "by_status": status_counts,
                "total": len(records)
            }
        
        elif intent == "sum_total_balance":
            total_balance = sum(float(r.get("f2", 0) or 0) for r in records)
            cars_with_debt = len([r for r in records if float(r.get("f2", 0) or 0) > 0])
            return {
                "total_balance": total_balance,
                "currency": "GEL",
                "cars_with_debt": cars_with_debt
            }
        
        elif intent == "cars_with_positive_balance":
            count = len([r for r in records if float(r.get("f2", 0) or 0) > 0])
            return {
                "count": count
            }
        
        elif intent == "vehicle_by_vin":
            vin = parameters.get("vin") if parameters else None
            if not vin:
                return {"error": "VIN not provided"}
            
            print(f"[DEBUG] Searching for VIN: {vin}")
            print(f"[DEBUG] Total records to search: {len(records)}")
            
            for record in records:
                record_vin = record.get("vin", "").strip().upper()
                search_vin = vin.strip().upper()
                
                if record_vin == search_vin:
                    print(f"[DEBUG] VIN FOUND: {record_vin}")
                    return {
                        "vehicle": record,
                        "found": True
                    }
            
            print(f"[DEBUG] VIN NOT FOUND: {vin}")
            print(f"[DEBUG] Available VINs: {[r.get('vin') for r in records[:5]]}")
            return {"found": False, "error": f"Vehicle with VIN {vin} not found"}
        
        elif intent == "vehicle_finance_by_vin":
            vin = parameters.get("vin") if parameters else None
            if not vin:
                return {"error": "VIN not provided"}
            
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
                        }
                    }
            return {"found": False, "error": f"Vehicle with VIN {vin} not found"}
        
        elif intent == "group_by_make_model_year":
            grouped = {}
            for record in records:
                make = record.get("manufacturer", "Unknown")
                model = record.get("model", "Unknown")
                year = record.get("year", "Unknown")
                key = f"{make} {model} ({year})"
                grouped[key] = grouped.get(key, 0) + 1
            
            return {
                "grouped": grouped,
                "total": len(records)
            }
        
        elif intent == "cars_by_location_or_stage":
            locations = {}
            for record in records:
                warehouse = record.get("warehouse", "Unknown")
                locations[warehouse] = locations.get(warehouse, 0) + 1
            
            return {
                "by_location": locations,
                "total": len(records)
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
            
            filtered_count = 0
            for record in records:
                date_str = record.get("date", "")
                try:
                    record_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if record_date >= cutoff:
                        filtered_count += 1
                except:
                    pass
            
            return {
                "count": filtered_count,
                "period": period
            }
        
        elif intent == "missing_documents_or_title":
            missing_count = len([r for r in records if not r.get("title_received")])
            return {
                "count": missing_count
            }
        
        else:
            return {"error": f"Unknown intent: {intent}"}
    
    except Exception as e:
        return {"error": str(e)}


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

{context_bundle.full_context}

The user asked: {user_query}
The system detected intent: {intent}
The query result summary is: {json.dumps(result_summary, ensure_ascii=False, indent=2)}

Generate a natural, concise Georgian response that:
1. Answers the user's question directly
2. Presents numbers and data clearly
3. Is business-appropriate and helpful
4. Uses Georgian language naturally
5. Keep it brief (1-3 sentences max)
6. Follow the response rules for the detected intent

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
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: str
    detected_fields: List[str]
    cached: bool
    timestamp: str
    records: List[Dict] = []
    session_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    import uuid
    
    user_query = request.messages[-1].content if request.messages else ""
    author_id = request.author_id or AUTHOR_ID
    session_id = request.session_id or str(uuid.uuid4())
    
    logger.info(f"[CHAT] Session={session_id}, Author={author_id}, Query={user_query[:50]}...")
    
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
    
    response_data = {
        "response": response_text,
        "intent": intent,
        "detected_fields": detected_fields,
        "cached": False,
        "timestamp": datetime.now().isoformat(),
        "records": [],
        "session_id": session_id
    }
    
    if redis_client:
        try:
            redis_client.setex(cache_key, 3600, json.dumps(response_data, ensure_ascii=False))
            logger.info(f"[CACHE] STORED result for query: {user_query[:50]}...")
        except Exception as e:
            logger.error(f"[CACHE] Write error: {e}")
    
    logger.info(f"[SUCCESS] Session={session_id}, Query completed: {user_query[:50]}... -> {intent}")
    return ChatResponse(**response_data)


@app.get("/session/{session_id}")
async def get_session(session_id: str, author_id: Optional[int] = None):
    author_id = author_id or AUTHOR_ID
    
    if not redis_client:
        return {"error": "Redis not connected", "session_id": session_id}
    
    try:
        session_key = f"session:{author_id}:{session_id}"
        session_data = redis_client.get(session_key)
        
        if session_data:
            return {
                "session_id": session_id,
                "author_id": author_id,
                "history": json.loads(session_data)
            }
        else:
            return {
                "session_id": session_id,
                "author_id": author_id,
                "history": [],
                "message": "No session history found"
            }
    except Exception as e:
        logger.error(f"[SESSION] Error retrieving session {session_id}: {e}")
        return {"error": str(e), "session_id": session_id}


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
        "context_source": "lion_ai_rule.md",
        "response_structure": get_response_example_structure()
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "redis": "connected" if redis_client else "disconnected",
        "contexts_loaded": bool(context_bundle.business_rules),
        "context_files": {
            "business_rules": "lion_ai_rule.md",
            "redis_rules": "redis_query_rules.md",
            "response_example": "response-example.json"
        }
    }


@app.get("/cache/refresh")
async def cache_refresh():
    if not redis_client:
        return {"status": "error", "message": "Redis not connected"}
    
    try:
        redis_client.flushall()
        logger.info("[CACHE] Cache refreshed - all keys deleted")
        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[CACHE] Refresh error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/cache/stats")
async def cache_stats():
    if not redis_client:
        return {"status": "error", "message": "Redis not connected"}
    
    try:
        info = redis_client.info()
        keys = redis_client.keys('chat:*')
        return {
            "status": "success",
            "total_keys": len(keys),
            "memory_used": info.get('used_memory_human'),
            "connected_clients": info.get('connected_clients'),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[CACHE] Stats error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/aggregation")
async def aggregation(author_id: Optional[int] = None):
    author_id = author_id or AUTHOR_ID
    
    logger.info(f"[AGGREGATION] Computing stats for author_id={author_id}")
    
    try:
        records = fetch_author_data(author_id)
        
        if not records:
            return {
                "status": "success",
                "author_id": author_id,
                "total_cars_in_db": 0,
                "total_cars_for_author": 0,
                "data": {}
            }
        
        filtered_records = filter_records_by_author(records, author_id)
        
        total_balance = sum(float(r.get("f2", 0) or 0) for r in filtered_records)
        total_pay = sum(float(r.get("f1", 0) or 0) for r in filtered_records)
        
        status_counts = {}
        for record in filtered_records:
            status = record.get("record_status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        manufacturer_counts = {}
        for record in filtered_records:
            make = record.get("manufacturer", "Unknown")
            manufacturer_counts[make] = manufacturer_counts.get(make, 0) + 1
        
        warehouse_counts = {}
        for record in filtered_records:
            warehouse = record.get("warehouse", "Unknown")
            warehouse_counts[warehouse] = warehouse_counts.get(warehouse, 0) + 1
        
        cars_with_debt = len([r for r in filtered_records if float(r.get("f2", 0) or 0) > 0])
        
        logger.info(f"[AGGREGATION] Total in DB: {len(records)}, For author {author_id}: {len(filtered_records)}, balance={total_balance}")
        
        return {
            "status": "success",
            "author_id": author_id,
            "total_cars_in_db": len(records),
            "total_cars_for_author": len(filtered_records),
            "data": {
                "total_balance": total_balance,
                "total_pay": total_pay,
                "cars_with_debt": cars_with_debt,
                "by_status": status_counts,
                "by_manufacturer": manufacturer_counts,
                "by_warehouse": warehouse_counts
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[AGGREGATION] Error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/")
async def root():
    return {
        "name": "Lion Trans Chat AI",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat - Send a Georgian query",
            "context_guidance": "GET /context-guidance - Get intent and field detection",
            "health": "GET /health - Health check",
            "cache_refresh": "GET /cache/refresh - Clear all cache",
            "cache_stats": "GET /cache/stats - Cache statistics",
            "aggregation": "GET /aggregation - Get dealer statistics and aggregations"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
