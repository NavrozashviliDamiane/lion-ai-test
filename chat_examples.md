# Chat Query Examples for Lion Trans AI

Based on `agent_context_bundle.json`, `fields_context.json`, and `query_map.json`

## Count & Aggregate Queries

### Count All Cars
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "სულ რამდენი მანქანა მაქვს?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `count_all_my_cars`
**Expected Response**: Total count of dealer's vehicles

---

### Count by Status
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "რამდენია current და რამდენია archive?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `count_by_record_status`
**Expected Response**: Breakdown by current/archive status

---

### Total Balance
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "სულ რამდენი მაქვს დავალიანება?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `sum_total_balance`
**Expected Response**: Total balance (f2) sum

---

## VIN-Based Queries

### Get Vehicle by VIN
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "ამ VIN-ზე მომეცი სრული ინფორმაცია: 1HGBH41JXMN109186"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `vehicle_by_vin`
**Expected Response**: Complete vehicle card with all details

---

### Finance Info by VIN
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "ამ VIN-ზე რამდენი მაქვს გადასახდელი? 1HGBH41JXMN109186"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `vehicle_finance_by_vin`
**Expected Response**: Total pay (f1), paid amount, balance (f2)

---

## Location & Stage Queries

### Cars in Warehouse
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "რომელი მანქანებია საწყობში?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `cars_by_location_or_stage`
**Expected Fields**: warehouse, where_comes, container_number
**Expected Response**: List of vehicles in warehouse

---

### Cars in Container
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "რომელი მანქანებია კონტეინერში?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `cars_by_location_or_stage`
**Expected Response**: Vehicles with container numbers

---

## Grouping & Statistics

### Count by Make
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "მარკების მიხედვით დამითვალე რამდენი მანქანა მაქვს?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `group_by_make_model_year`
**Expected Response**: Count grouped by manufacturer

---

### Count by Year
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "რომელი წლების მანქანები მაქვს?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `group_by_make_model_year`
**Expected Response**: Vehicles grouped by year

---

### How Many Toyota
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "რამდენი Toyota მაქვს?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `group_by_make_model_year`
**Expected Response**: Count of Toyota vehicles

---

## Period-Based Queries

### This Month
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "ამ თვეში ნაყიდი მანქანები"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `records_by_period`
**Expected Response**: Vehicles purchased in current month

---

### Last 30 Days
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "ბოლო 30 დღეში ნაყიდი ავტომობილები"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `records_by_period`
**Expected Response**: Recent purchases

---

## Document & Title Queries

### Missing Title
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "რომელ მანქანებს არ აქვთ title?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `missing_documents_or_title`
**Expected Response**: Vehicles without title documents

---

### Title Status
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "საბუთი მიღებულია?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `missing_documents_or_title`
**Expected Response**: Title document status

---

## Field-Specific Queries

### USA-GEO Location
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "USA-GEO-ის მიხედვით რამდენი მანქანა მაქვს?"}],
    "author_id": 1748
  }'
```

**Expected Fields**: usa_geo
**Expected Response**: Count by USA-GEO location

---

### Cars with Positive Balance
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "რომელ მანქანებს აქვთ დავალიანება?"}],
    "author_id": 1748
  }'
```

**Expected Intent**: `cars_with_positive_balance`
**Expected Response**: List of vehicles with balance > 0

---

### Photos Status
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "ატვირთულია თუა რა ფოტოები?"}],
    "author_id": 1748
  }'
```

**Expected Fields**: photo
**Expected Response**: Photos upload status

---

### Parts Information
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "რა ნაწილები მოყვება ამ მანქანას?"}],
    "author_id": 1748
  }'
```

**Expected Fields**: parts
**Expected Response**: Parts included with vehicle

---

## Complex Queries

### Multi-Field Analysis
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "საწყობში რამდენი მანქანა მაქვს და რა მარკებია?"}],
    "author_id": 1748
  }'
```

**Expected Fields**: warehouse, manufacturer
**Expected Response**: Warehouse inventory by make

---

### Financial Summary
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "სულ რამდენი გადახდილი და რამდენი დარჩა გადასახდელი?"}],
    "author_id": 1748
  }'
```

**Expected Fields**: f1, f2, pm_1, pm_2, pm_3, pm_4, pm_5
**Expected Response**: Total paid vs remaining balance

---

## Testing with Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_chat(query, author_id=1748):
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "messages": [{"role": "user", "content": query}],
            "author_id": author_id
        }
    )
    return response.json()

# Test examples
queries = [
    "სულ რამდენი მანქანა მაქვს?",
    "რამდენი Toyota მაქვს?",
    "რომელი მანქანებია საწყობში?",
    "სულ რამდენი მაქვს დავალიანება?",
]

for query in queries:
    result = test_chat(query)
    print(f"Query: {query}")
    print(f"Response: {result['response']}\n")
```

---

## Context Guidance Testing

To see what fields and intents are detected for a query:

```bash
curl "http://localhost:8000/context-guidance?query=რამდენი%20მანქანა%20მაქვს%20საწყობში"
```

This shows:
- Relevant fields detected
- Matching intents
- Similarity scores
- Required fields for each intent
