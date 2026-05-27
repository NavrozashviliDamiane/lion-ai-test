import redis
import json
import numpy as np
from openai import OpenAI
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, OPENAI_API_KEY, EMBEDDING_MODEL, AUTHOR_ID, OPENAI_MODEL
from database import fetch_author_data
from field_metadata import load_field_descriptions

client = OpenAI(api_key=OPENAI_API_KEY)

def get_redis_connection():
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )
        r.ping()
        return r
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        raise

def get_embedding(text: str) -> list:
    try:
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        raise

def store_records_in_redis(author_id: int = AUTHOR_ID):
    """Store raw JSON records in Redis cache"""
    try:
        r = get_redis_connection()
        
        print(f"Fetching data for author_id {author_id}...")
        data = fetch_author_data(author_id)
        
        if not data:
            print(f"No data found for author_id {author_id}")
            return
        
        print(f"Found {len(data)} records, storing in Redis...")
        
        for idx, record in enumerate(data):
            try:
                record_id = record.get("id")
                redis_key = f"record:{author_id}:{record_id}"
                
                r.hset(redis_key, mapping={
                    "content": json.dumps(record)
                })
                
                r.expire(redis_key, 86400 * 30)
                
                if (idx + 1) % 50 == 0:
                    print(f"Stored {idx + 1}/{len(data)} records...")
            
            except Exception as record_error:
                print(f"Error storing record {record.get('id')}: {record_error}")
                continue
        
        print(f"Successfully stored {len(data)} records in Redis")
        
    except Exception as e:
        print(f"Error storing records: {e}")
        import traceback
        traceback.print_exc()
        raise

def store_field_embeddings_in_redis():
    """Store Georgian field descriptions as embeddings for intent detection"""
    try:
        r = get_redis_connection()
        fields = load_field_descriptions()
        
        print(f"Generating embeddings for {len(fields)} field descriptions...")
        
        for field in fields:
            try:
                field_name = field.get('field_name')
                label_name = field.get('label_name')
                field_desc = field.get('field_desc')
                questions = field.get('question', '')
                
                if not field_name:
                    continue
                
                combined_text = f"{label_name} {field_desc} {questions}"
                embedding = get_embedding(combined_text)
                
                redis_key = f"field_embedding:{field_name}"
                
                r.hset(redis_key, mapping={
                    "embedding": json.dumps(embedding),
                    "label": label_name,
                    "description": field_desc,
                    "questions": questions
                })
                
                r.expire(redis_key, 86400 * 365)
            
            except Exception as field_error:
                print(f"Error processing field {field.get('field_name')}: {field_error}")
                continue
        
        print(f"Successfully stored {len(fields)} field embeddings")
        
    except Exception as e:
        print(f"Error storing field embeddings: {e}")
        import traceback
        traceback.print_exc()
        raise

def extract_vin_from_query(query: str) -> str:
    """Extract VIN number from query if present"""
    import re
    vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
    match = re.search(vin_pattern, query.upper())
    return match.group(0) if match else None

def search_by_exact_field(field_name: str, field_value: str, author_id: int = AUTHOR_ID) -> list:
    """Search for exact field matches in Redis"""
    try:
        r = get_redis_connection()
        pattern = f"embedding:{author_id}:*"
        keys = r.keys(pattern)
        
        results = []
        for key in keys:
            stored_data = r.hgetall(key)
            if stored_data:
                content = json.loads(stored_data.get("content", "{}"))
                if content.get(field_name) == field_value:
                    results.append({
                        "record_id": content.get("id"),
                        "similarity": 1.0,
                        "content": content,
                        "text": stored_data.get("text", "")
                    })
        
        return results
    except Exception as e:
        print(f"Error in exact field search: {e}")
        return []

def detect_intent_fields(query: str) -> list:
    """Use AI to detect which fields the user is asking about"""
    try:
        fields = load_field_descriptions()
        field_list = "\n".join([
            f"- {f['field_name']} ({f['label_name']}): {f['field_desc']}"
            for f in fields if f.get('field_name')
        ])
        
        prompt = f"""Based on this Georgian query, identify which database fields the user is asking about.
        
Query: {query}

Available fields:
{field_list}

Return ONLY a JSON array of field names (field_name values) that match the user's intent. 
Example: ["manufacturer", "model", "year"]
If no fields match, return an empty array: []"""
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        import re
        match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if match:
            detected_fields = json.loads(match.group(0))
            print(f"Detected intent fields: {detected_fields}")
            return detected_fields
        return []
    
    except Exception as e:
        print(f"Error detecting intent: {e}")
        return []

def search_records_by_intent(query: str, author_id: int = AUTHOR_ID, top_k: int = 3) -> list:
    """Search records based on detected intent fields"""
    try:
        r = get_redis_connection()
        
        vin = extract_vin_from_query(query)
        if vin:
            print(f"Detected VIN in query: {vin}")
            pattern = f"record:{author_id}:*"
            keys = r.keys(pattern)
            
            results = []
            for key in keys:
                stored_data = r.hgetall(key)
                if stored_data:
                    content = json.loads(stored_data.get("content", "{}"))
                    if content.get("vin") == vin:
                        results.append({
                            "record_id": content.get("id"),
                            "similarity": 1.0,
                            "content": content
                        })
            
            if results:
                print(f"Found exact VIN match: {len(results)} records")
                return results[:top_k]
        
        detected_fields = detect_intent_fields(query)
        
        if not detected_fields:
            print("No intent fields detected, returning empty results")
            return []
        
        pattern = f"record:{author_id}:*"
        keys = r.keys(pattern)
        
        if not keys:
            return []
        
        results = []
        
        for key in keys:
            stored_data = r.hgetall(key)
            if stored_data:
                content = json.loads(stored_data.get("content", "{}"))
                
                relevant_fields = {}
                for field in detected_fields:
                    if field in content and content[field]:
                        relevant_fields[field] = content[field]
                
                if relevant_fields:
                    results.append({
                        "record_id": content.get("id"),
                        "similarity": len(relevant_fields) / len(detected_fields),
                        "content": content,
                        "relevant_fields": relevant_fields
                    })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:top_k]
    
    except Exception as e:
        print(f"Error searching records: {e}")
        raise

def cosine_similarity(a: list, b: list) -> float:
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
