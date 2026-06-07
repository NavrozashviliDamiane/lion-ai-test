"""
Embeddings module for semantic search of field definitions
Uses OpenAI embeddings to create semantic vectors for field definitions
and stores them in Redis for fast similarity search
"""

import json
import redis
import numpy as np
from typing import List, Dict
from openai import OpenAI
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def get_redis_client():
    """Get Redis connection"""
    if REDIS_PASSWORD:
        return redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=False
        )
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)

def create_field_embeddings():
    """
    Load fields_context_concise.json and create embeddings for each field
    Store in Redis with field metadata
    """
    print("[EMBEDDINGS] Loading fields_context_concise.json...")
    
    try:
        with open('fields_context_concise.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[EMBEDDINGS] Error loading fields file: {e}")
        return False
    
    if 'fields' not in data:
        print("[EMBEDDINGS] No 'fields' key in JSON")
        return False
    
    fields = data['fields']
    redis_client = get_redis_client()
    
    print(f"[EMBEDDINGS] Creating embeddings for {len(fields)} fields...")
    
    for i, field in enumerate(fields):
        try:
            field_name = field.get('field_name', f'field_{i}')
            label = field.get('label', '')
            synonyms = field.get('synonyms', [])
            business_desc = field.get('business_description', '')
            
            # Create embedding text combining all field info
            embedding_text = f"{field_name} {label} {' '.join(synonyms)} {business_desc}"
            
            # Get embedding from OpenAI
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=embedding_text
            )
            
            embedding_vector = response.data[0].embedding
            
            # Store in Redis
            field_key = f"field_embedding:{field_name}"
            
            # Store embedding as bytes
            embedding_bytes = np.array(embedding_vector, dtype=np.float32).tobytes()
            redis_client.set(f"{field_key}:vector", embedding_bytes)
            
            # Store field metadata as JSON
            field_data = {
                'field_name': field_name,
                'label': label,
                'synonyms': synonyms,
                'business_description': business_desc,
                'data_type': field.get('data_type', ''),
                'category': field.get('category', ''),
                'example_questions': field.get('example_user_questions', [])[:2],  # Limit to 2 examples
            }
            redis_client.set(f"{field_key}:data", json.dumps(field_data, ensure_ascii=False))
            
            if (i + 1) % 10 == 0:
                print(f"[EMBEDDINGS] Processed {i + 1}/{len(fields)} fields...")
        
        except Exception as e:
            print(f"[EMBEDDINGS] Error processing field {field_name}: {e}")
            continue
    
    print(f"[EMBEDDINGS] ✓ Successfully created embeddings for {len(fields)} fields")
    return True

def search_relevant_fields(query: str, top_k: int = 5) -> List[Dict]:
    """
    Search for relevant fields based on user query using semantic similarity
    Returns top_k most relevant fields with their metadata
    Caches results in Redis for 1 hour to avoid repeated API calls
    """
    try:
        redis_client = get_redis_client()
        
        # Check cache first
        cache_key = f"embedding_search:{query}:{top_k}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            print(f"[EMBEDDINGS] Cache HIT for query: {query[:50]}...")
            return json.loads(cached_result)
        
        print(f"[EMBEDDINGS] Cache MISS - searching for: {query[:50]}...")
        
        # Get embedding for the query
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = np.array(response.data[0].embedding, dtype=np.float32)
        
        redis_client = get_redis_client()
        
        # Get all field embeddings from Redis
        field_keys = redis_client.keys("field_embedding:*:vector")
        
        similarities = []
        
        for key in field_keys:
            try:
                embedding_bytes = redis_client.get(key)
                if embedding_bytes:
                    stored_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, stored_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                    )
                    
                    # Get field name from key
                    field_name = key.decode().split(':')[1]
                    
                    # Get field data
                    data_key = f"field_embedding:{field_name}:data"
                    field_data = redis_client.get(data_key)
                    
                    if field_data:
                        field_info = json.loads(field_data)
                        similarities.append({
                            'field_name': field_name,
                            'similarity': float(similarity),
                            'info': field_info
                        })
            except Exception as e:
                print(f"[EMBEDDINGS] Error processing field: {e}")
                continue
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        results = similarities[:top_k]
        
        # Cache the results for 1 hour (3600 seconds)
        redis_client.setex(
            cache_key,
            3600,
            json.dumps(results, ensure_ascii=False)
        )
        print(f"[EMBEDDINGS] Cached results for future queries")
        
        return results
    
    except Exception as e:
        print(f"[EMBEDDINGS] Error searching fields: {e}")
        return []

def format_relevant_context(query: str, top_k: int = 5) -> str:
    """
    Search for relevant fields and format them as context for the LLM
    """
    relevant_fields = search_relevant_fields(query, top_k)
    
    if not relevant_fields:
        return ""
    
    context = "\n=== RELEVANT FIELD DEFINITIONS (Semantic Search) ===\n"
    context += f"Based on your query, here are the most relevant fields:\n\n"
    
    for i, field in enumerate(relevant_fields, 1):
        info = field['info']
        similarity = field['similarity']
        
        context += f"{i}. {info['field_name']} (Relevance: {similarity:.2%})\n"
        context += f"   Label: {info['label']}\n"
        context += f"   Description: {info['business_description']}\n"
        
        if info['synonyms']:
            context += f"   Georgian synonyms: {', '.join(info['synonyms'][:3])}\n"
        
        context += "\n"
    
    return context
