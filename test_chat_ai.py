import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_chat(query: str, author_id: int = 1748) -> Dict[str, Any]:
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "messages": [{"role": "user", "content": query}],
            "author_id": author_id
        }
    )
    return response.json()


def test_context_guidance(query: str, author_id: int = 1748) -> Dict[str, Any]:
    response = requests.get(
        f"{BASE_URL}/context-guidance",
        params={"query": query, "author_id": author_id}
    )
    return response.json()


def print_response(query: str, response: Dict[str, Any]):
    print("\n" + "="*80)
    print(f"Query: {query}")
    print("="*80)
    print(f"Intent: {response.get('intent')}")
    print(f"Detected Fields: {response.get('detected_fields')}")
    print(f"Cached: {response.get('cached')}")
    print(f"Response:\n{response.get('response')}")
    print("-"*80)


if __name__ == "__main__":
    print("🚀 Lion Trans Chat AI - Test Suite")
    print("="*80)
    
    test_queries = [
        "სულ რამდენი მანქანა მაქვს?",
        "რამდენი Toyota მაქვს?",
        "რომელი მანქანებია საწყობში?",
        "სულ რამდენი მაქვს დავალიანება?",
        "რამდენია current და რამდენია archive?",
        "რომელ მანქანებს აქვთ დავალიანება?",
    ]
    
    print("\n📝 Testing Chat Endpoint")
    print("="*80)
    
    for query in test_queries:
        try:
            response = test_chat(query)
            print_response(query, response)
        except Exception as e:
            print(f"❌ Error testing query '{query}': {e}")
    
    print("\n🔍 Testing Context Guidance")
    print("="*80)
    
    for query in test_queries[:3]:
        try:
            guidance = test_context_guidance(query)
            print(f"\nQuery: {query}")
            print(f"Detected Intent: {guidance.get('detected_intent')}")
            print(f"Confidence: {guidance.get('confidence')}")
            print(f"Detected Fields: {guidance.get('detected_fields')}")
            print(f"Parameters: {guidance.get('parameters')}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Test suite completed!")
