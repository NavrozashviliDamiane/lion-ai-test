import sys
import io
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

# Configure logging with UTF-8 encoding BEFORE wrapping stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/chat_ai.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Fix console encoding for Georgian characters on Windows (after logging setup)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

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
        self.test_rule = ""  # test_rule.md (centralized context)
        self.response_example = None  # response-example.json
        self.fields_context = None  # fields_context.json (field definitions)
        self.full_context = ""  # Combined context
        self.load_contexts()
    
    def load_contexts(self):
        import os
        
        # List of files to load with their attribute names
        # Format: (filename, attribute_name, file_type)
        files_to_load = [
            ("test_rule.md", "test_rule", "text"),
            ("response-example.json", "response_example", "json"),
            ("fields_context_concise.json", "fields_context", "json"),
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
        """Build a comprehensive context string with loaded files"""
        context_sections = []
        
        if self.test_rule:
            context_sections.append(f"{self.test_rule}\n")
        
        if self.fields_context:
            # Include concise field definitions
            fields_str = json.dumps(self.fields_context, ensure_ascii=False, indent=2)
            context_sections.append(f"## FIELD DEFINITIONS\n{fields_str}\n")
        
        if self.response_example:
            # Format response example as readable context
            example_str = json.dumps(self.response_example, ensure_ascii=False, indent=2)
            context_sections.append(f"## DATA STRUCTURE EXAMPLE\nHere is an example of the actual data structure in Redis:\n```json\n{example_str}\n```\n")
        
        self.full_context = "\n".join(context_sections)

context_bundle = ContextBundle()


def execute_ai_query(query_intent: Dict, records: List[Dict]) -> Dict:
    """Execute the AI-generated query intent on the loaded records"""
    import random
    
    if not query_intent or not records:
        return {"error": "No query intent or records", "records": []}
    
    query_type = query_intent.get("type", "unknown")
    filters = query_intent.get("filters", {})
    fields_needed = query_intent.get("fields_needed", [])
    limit = query_intent.get("limit")
    
    logger.info(f"[EXECUTE AI QUERY] Type: {query_type}, Filters: {filters}, Fields: {fields_needed}, Limit: {limit}")
    
    # Start with all records
    filtered = records
    
    # Apply filters
    if filters:
        for field, value in filters.items():
            logger.info(f"[EXECUTE AI QUERY] Filtering by {field} = {value}")
            filtered = [r for r in filtered if r.get(field) == value]
    
    logger.info(f"[EXECUTE AI QUERY] After filtering: {len(filtered)} records")
    
    # Handle different query types
    if query_type == "random":
        # Pick random record(s)
        if limit and limit > 0:
            result_records = random.sample(filtered, min(limit, len(filtered)))
        else:
            result_records = random.sample(filtered, min(1, len(filtered)))
    
    elif query_type == "calculation":
        # For COUNT queries, calculate breakdown by status if no filters
        result = {
            "count": len(filtered),
            "total": len(records),
            "records": filtered[:10] if fields_needed else []
        }
        
        # If no filters, calculate breakdown by record_status
        if not filters:
            current_count = len([r for r in records if r.get("record_status") == "current"])
            archive_count = len([r for r in records if r.get("record_status") == "archive"])
            result["current_count"] = current_count
            result["archive_count"] = archive_count
            logger.info(f"[EXECUTE AI QUERY] Breakdown: current={current_count}, archive={archive_count}")
        
        return result
    
    elif query_type == "filter":
        # Return filtered records
        if limit:
            result_records = filtered[:limit]
        else:
            result_records = filtered
    
    else:  # semantic, hybrid, or unknown
        result_records = filtered
    
    # Extract only requested fields if specified
    if fields_needed and result_records:
        result_records = [
            {field: record.get(field) for field in fields_needed if field in record}
            for record in result_records
        ]
    
    logger.info(f"[EXECUTE AI QUERY] Returning {len(result_records)} records")
    
    return {
        "count": len(result_records),
        "total": len(records),
        "records": result_records
    }


def get_response_example_structure() -> str:
    """Returns a formatted string showing the structure of response data"""
    return "Using test_rule.md for context"


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
    logger.info(f"[EXECUTE] Records type: {type(records)}, is list: {isinstance(records, list)}")
    if isinstance(records, str):
        logger.error(f"[EXECUTE] ERROR: Records is a string, not a list!")
        try:
            records = json.loads(records)
            logger.info(f"[EXECUTE] Converted string to list: {len(records)} records")
        except:
            return {"error": "Invalid records format"}
    
    if not records:
        return {"error": "No records found for this dealer"}
    
    try:
        if intent == "count_all_my_cars":
            # Count by record_status
            current_count = len([r for r in records if r.get("record_status") == "current"])
            archive_count = len([r for r in records if r.get("record_status") == "archive"])
            total_count = len(records)
            
            logger.info(f"[EXECUTE] Count breakdown - Total: {total_count}, Current: {current_count}, Archive: {archive_count}")
            
            return {
                "total": total_count,
                "count": current_count,
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
                    print(f"[DEBUG] Vehicle record keys: {list(record.keys())}")
                    print(f"[DEBUG] year: {record.get('year')}")
                    print(f"[DEBUG] auction_title: {record.get('auction_title')}")
                    print(f"[DEBUG] buyer_id: {record.get('buyer_id')}")
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


def log_redis_query_logic(user_query: str, intent: str, query_logic: str):
    """Log the Redis query logic that AI created"""
    logger.info(f"[REDIS QUERY] User Query: {user_query[:80]}")
    logger.info(f"[REDIS QUERY] Intent: {intent}")
    logger.info(f"[REDIS QUERY] Logic: {query_logic}")


def generate_response(intent: str, result: Dict, user_query: str) -> str:
    if "error" in result and not result.get("found") and not result.get("records"):
        return f"❌ {result['error']}"
    
    try:
        vehicle_info = {}
        if result.get("vehicle"):
            # Pass ALL fields from the vehicle record to the AI
            vehicle_info = result.get("vehicle")
        
        result_summary = {
            "intent": intent,
            "total": result.get("total", 0),
            "count": result.get("count", 0),
            "current_count": result.get("current_count"),
            "archive_count": result.get("archive_count"),
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
        
        system_prompt = f"""You are a COMPLETELY FREE AI for Lion Trans car dealer system.

{context_bundle.full_context}

YOU HAVE TOTAL FREEDOM:
- You understand field definitions from FIELD DEFINITIONS section
- You generate ANY Redis query needed to answer the user's question
- You match Georgian words to field names using Georgian synonyms
- You decide what data to extract and how to respond
- You are NOT limited to predefined intents or rules
- You can query ANY field, ANY combination, ANY way needed

AVAILABLE DATA:
- Total records available: {len(result.get('records', []))} vehicles
- All fields available in FIELD DEFINITIONS
- All records belong to author_id: {result.get('author_id', 'unknown')}

CONTEXT FOR THIS QUERY:
User asked (Georgian): {user_query}
Current result summary: {json.dumps(result_summary, ensure_ascii=False, indent=2)}

YOUR TASK:

STEP 1 - UNDERSTAND THE GEORGIAN QUERY:
- Read the user's Georgian question carefully
- Match Georgian words to FIELD DEFINITIONS using Georgian synonyms (after |)
- Examples:
  * "ვინ კოდი" → vin field (17-char vehicle identifier)
  * "წელი" → year field (manufacturing year)
  * "საწყობი" → warehouse field (location)
  * "დილერი" → author field (dealer name)
  * "რამდენი" → COUNT query (how many)
  * "რომელი" → FILTER query (which ones)
  * "რენდომად" → pick any/random record
  * "ნებისმიერი" → any/random
- Understand what the user really wants
- Determine what query is needed

STEP 2 - GENERATE THE QUERY:
Create a query that would answer the user's question:
- FILTER: Extract specific records matching criteria (e.g., year = 2015, vin = "ABC123")
- SEMANTIC: Search by text/description (e.g., cars with damage)
- CALCULATION: Aggregations (e.g., SUM f2, COUNT by status, AVG container_amount)
  * COUNT queries: "რამდენი" (how many), "სულ" (total) → COUNT records with filters
  * SUM queries: "სულ თანხა" (total amount) → SUM f1 or f2
  * GROUP queries: "დაჯგუფე" (group by) → GROUP BY field
- RANDOM: Pick any record from available data
- HYBRID: Combination of above

Output a JSON intent with:
- type: filter|semantic|calculation|random|hybrid
- query_description: What query you would create
- fields_needed: Which fields to extract
- filters: Any filters to apply (e.g., {{"record_status": "current"}})
- limit: How many records to return (1 for random, N for multiple, null for all)
- georgian_understanding: What Georgian words you matched

STEP 3 - RESPOND NATURALLY:
Generate response based on the query results.
Be conversational, precise, contextual.
Use Georgian naturally.
Provide actual data from the query.

CRITICAL RULES:
- FIRST output the JSON query intent
- THEN output the Georgian response
- Separate with: ---RESPONSE---
- The JSON must be valid
- The response must be ONLY Georgian text
- Be creative and flexible with queries
- If user asks for "any/random", pick one record
- If user asks for counts, calculate from data
- If user asks for specific field, extract it
- Match Georgian words to fields using synonyms
- ALWAYS validate field names against FIELD DEFINITIONS (check Georgian synonyms)
- Use the actual data provided in result_summary (current_count, archive_count, etc)
- Never hallucinate numbers - use only data from result_summary

OUTPUT FORMAT:
```json
{{"type": "...", "query_description": "...", "fields_needed": [...], "filters": {{...}}, "limit": N, "georgian_understanding": {{...}}}}
```

---RESPONSE---

[Your Georgian response here]"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User query: {user_query}\n\nIMPORTANT: You MUST output in this exact format:\n1. First: JSON query intent inside ```json``` block\n2. Then: ---RESPONSE--- separator\n3. Then: Georgian response text\n\nDo NOT skip the JSON or separator!"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        full_response = response.choices[0].message.content.strip()
        
        # Parse JSON intent and Georgian response
        query_intent = None
        response_text = full_response
        
        logger.info(f"[AI RESPONSE] Raw response length: {len(full_response)}")
        logger.info(f"[AI RESPONSE] Contains ---RESPONSE---: {'---RESPONSE---' in full_response}")
        
        if "---RESPONSE---" in full_response:
            parts = full_response.split("---RESPONSE---")
            intent_part = parts[0].strip()
            response_text = parts[1].strip() if len(parts) > 1 else ""
            
            logger.info(f"[AI RESPONSE] Intent part length: {len(intent_part)}")
            logger.info(f"[AI RESPONSE] Intent part preview: {intent_part[:200]}")
            
            # Extract JSON from intent part (handle markdown code blocks)
            try:
                # Remove markdown code block if present
                clean_intent = intent_part.replace("```json", "").replace("```", "").strip()
                
                # Find JSON in the intent part
                json_start = clean_intent.find("{")
                json_end = clean_intent.rfind("}") + 1
                logger.info(f"[AI RESPONSE] JSON positions: start={json_start}, end={json_end}")
                
                if json_start >= 0 and json_end > json_start:
                    json_str = clean_intent[json_start:json_end]
                    logger.info(f"[AI RESPONSE] Extracted JSON: {json_str[:300]}")
                    query_intent = json.loads(json_str)
                    logger.info(f"[QUERY INTENT] ✅ Successfully parsed!")
                    logger.info(f"[QUERY INTENT] Type: {query_intent.get('type', 'unknown')}")
                    logger.info(f"[QUERY INTENT] Description: {query_intent.get('query_description', 'N/A')}")
                    logger.info(f"[QUERY INTENT] Fields needed: {query_intent.get('fields_needed', [])}")
                    logger.info(f"[QUERY INTENT] Filters: {query_intent.get('filters', {})}")
                    logger.info(f"[QUERY INTENT] Limit: {query_intent.get('limit', 'N/A')}")
                    logger.info(f"[QUERY INTENT] Georgian understanding: {query_intent.get('georgian_understanding', {})}")
                    logger.info(f"[QUERY INTENT] Full JSON: {json.dumps(query_intent, ensure_ascii=False)}")
                else:
                    logger.warning(f"[AI RESPONSE] No JSON found in intent part")
            except json.JSONDecodeError as e:
                logger.warning(f"[QUERY INTENT] ❌ Failed to parse JSON: {e}")
                logger.warning(f"[QUERY INTENT] JSON string was: {json_str if 'json_str' in locals() else 'N/A'}")
                query_intent = {"type": "unknown", "error": str(e)}
        else:
            logger.warning(f"[AI RESPONSE] No ---RESPONSE--- separator found in response")
        
        logger.info(f"[RESPONSE] Generated text: {response_text[:100]}")
        logger.info(f"[RESPONSE] Intent: {intent}")
        logger.info(f"[RESPONSE] Query: {user_query}")
        logger.info(f"[RESPONSE] Result summary keys: {list(result_summary.keys())}")
        
        # Log the Redis query logic that AI would use
        logger.info(f"[REDIS QUERY] User asked: {user_query[:80]}")
        logger.info(f"[REDIS QUERY] Intent detected: {intent}")
        logger.info(f"[REDIS QUERY] Data structure available: {list(context_bundle.response_example[0].keys()) if context_bundle.response_example else 'None'}")
        
        # Log specific query details based on intent
        if intent == "count_all_my_cars":
            logger.info(f"[REDIS QUERY] Pattern: Count All Records - Total: {result.get('total', 0)}")
            logger.info(f"[REDIS QUERY] Query Logic: GET author_records:{{author_id}} -> COUNT all records")
        elif intent == "vehicle_by_vin":
            vin = result.get('vin', 'N/A')
            found = result.get('found', False)
            logger.info(f"[REDIS QUERY] Pattern: VIN Lookup - VIN: {vin}, Found: {found}")
            logger.info(f"[REDIS QUERY] Query Logic: GET author_records:{{author_id}} -> FILTER by vin='{vin}' -> EXTRACT year, auction_title, buyer_id")
        elif intent == "sum_total_balance":
            total_balance = result.get('total_balance', 0)
            logger.info(f"[REDIS QUERY] Pattern: Sum Balance - Total: {total_balance}")
            logger.info(f"[REDIS QUERY] Query Logic: GET author_records:{{author_id}} -> SUM field 'balance' for all records")
        else:
            logger.info(f"[REDIS QUERY] Pattern: {intent}")
        
        logger.info(f"[REDIS QUERY] AI Response: {response_text[:100]}")
        
        # Safety check: if response looks like JSON, extract the intent and regenerate
        if response_text.startswith("{") and response_text.endswith("}"):
            logger.warning(f"[RESPONSE] AI returned JSON instead of Georgian text. Regenerating...")
            # Retry with stricter instructions
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a Georgian language assistant. You ONLY respond in Georgian language. Never return JSON, code, or any structured format. Only return natural Georgian text."},
                    {"role": "user", "content": f"User asked: {user_query}\n\nBased on the data: {json.dumps(result_summary, ensure_ascii=False)}\n\nRespond in Georgian only. No JSON. No code. Only Georgian text."}
                ],
                temperature=0.7,
                max_tokens=300
            )
            response_text = response.choices[0].message.content.strip()
            logger.info(f"[RESPONSE] Regenerated text: {response_text[:100]}")
        
        return response_text, query_intent
    except Exception as e:
        logger.error(f"[RESPONSE] Error: {str(e)}")
        return f"⚠️ Response generation error: {str(e)}", None


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
    
    # Create cache key for author's records (not query-specific)
    author_cache_key = f"author_records:{author_id}"
    
    # ONLY query Redis - no database fallback
    filtered_records = None
    cached = False
    
    if not redis_client:
        logger.error(f"[REDIS] Redis client not available")
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    try:
        cached_data = redis_client.get(author_cache_key)
        if cached_data:
            logger.info(f"[REDIS] HIT for author {author_id} records")
            if isinstance(cached_data, bytes):
                cached_data = cached_data.decode('utf-8')
            filtered_records = json.loads(cached_data)
            logger.info(f"[REDIS] Retrieved {len(filtered_records)} records from cache")
            cached = True
        else:
            logger.warning(f"[REDIS] MISS for author {author_id} - no data in Redis")
            # Return error if data not in Redis
            raise HTTPException(status_code=404, detail=f"No cached data for author {author_id}. Please load data first.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[REDIS] Read error: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
    
    # AI will decide what to do - no backend intent detection
    # Just pass all data to AI for intelligent classification
    logger.info(f"[AI FREEDOM] Passing query to AI for classification and execution")
    
    # Final safety check
    logger.info(f"[CHAT] Before AI processing - filtered_records type: {type(filtered_records)}")
    if isinstance(filtered_records, str):
        logger.error(f"[CHAT] CRITICAL: filtered_records is still a string! Converting...")
        try:
            filtered_records = json.loads(filtered_records)
        except:
            filtered_records = []
    
    # Prepare data for AI to analyze
    query_result = {
        "total": len(filtered_records),
        "records": filtered_records,
        "author_id": author_id
    }
    
    logger.info(f"[AI FREEDOM] Passing {len(filtered_records)} records to AI for analysis")
    response_text, query_intent = generate_response("ai_decides", query_result, user_query)
    
    # Execute AI-generated query if intent was extracted
    if query_intent and query_intent.get("type") != "unknown":
        logger.info(f"[CHAT] Executing AI-generated query: {query_intent.get('type')}")
        query_result = execute_ai_query(query_intent, filtered_records)
        logger.info(f"[CHAT] Query executed, got {query_result.get('count', 0)} results")
        
        # Re-generate response with actual query results
        logger.info(f"[CHAT] Re-generating response with query results")
        response_text, _ = generate_response("ai_decides", query_result, user_query)
        logger.info(f"[CHAT] Response regenerated with actual data")
    
    # Extract intent from AI's response
    intent = "ai_classified"
    detected_fields = []
    
    response_data = {
        "response": response_text,
        "intent": intent,
        "detected_fields": detected_fields,
        "cached": cached,
        "timestamp": datetime.now().isoformat(),
        "records": [],
        "session_id": session_id
    }


    
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


@app.post("/load-data")
async def load_data(author_id: Optional[int] = None):
    """Load author data from database into Redis cache"""
    author_id = author_id or AUTHOR_ID
    
    if not redis_client:
        logger.error(f"[LOAD] Redis not available")
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    try:
        logger.info(f"[LOAD] Starting data load for author_id={author_id}")
        
        # Fetch from database
        records = fetch_author_data(author_id)
        logger.info(f"[LOAD] Retrieved {len(records)} records from database")
        
        if not records:
            logger.warning(f"[LOAD] No records found for author_id={author_id}")
            return {
                "status": "warning",
                "author_id": author_id,
                "records_loaded": 0,
                "message": f"No records found for author {author_id}"
            }
        
        # Filter records for this author
        filtered_records = filter_records_by_author(records, author_id)
        logger.info(f"[LOAD] Filtered to {len(filtered_records)} records for author_id={author_id}")
        
        # Store in Redis with 24-hour TTL
        author_cache_key = f"author_records:{author_id}"
        redis_client.setex(
            author_cache_key, 
            86400,  # 24 hours
            json.dumps(filtered_records, ensure_ascii=False)
        )
        logger.info(f"[LOAD] Stored {len(filtered_records)} records in Redis for author {author_id}")
        
        return {
            "status": "success",
            "author_id": author_id,
            "records_loaded": len(filtered_records),
            "cache_key": author_cache_key,
            "ttl_seconds": 86400,
            "message": f"Successfully loaded {len(filtered_records)} records into Redis"
        }
        
    except Exception as e:
        logger.error(f"[LOAD] Error loading data: {e}")
        raise HTTPException(status_code=500, detail=f"Data load error: {str(e)}")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "redis": "connected" if redis_client else "disconnected",
        "contexts_loaded": bool(context_bundle.test_rule),
        "context_files": {
            "test_rules": "test_rule.md",
            "redis_guide": "redis_query_guide.md",
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
