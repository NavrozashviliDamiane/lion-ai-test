# Redis Query Building Rules for AI

## How AI Should Query Redis Cache

### Cache Key Generation
The AI system generates cache keys using this pattern:

```python
cache_key = f"chat:{md5_hash}"
```

Where `md5_hash` is calculated from:
```python
md5_hash = hashlib.md5(f'{author_id}:{user_query}'.encode()).hexdigest()
```

**Example**:
- Author ID: `1748`
- User query: `"რამდენი მანქანა მაქვს?"`
- Cache key: `chat:a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### Query Flow for AI

```
1. Receive user query + author_id
   ↓
2. Generate cache_key = chat:{md5(author_id:query)}
   ↓
3. Try to GET from Redis using cache_key
   ↓
4. If FOUND → Return cached response immediately
   ↓
5. If NOT FOUND → Process query:
   - Fetch data from database
   - Filter by author_id
   - Detect intent
   - Execute query logic
   - Generate response
   - STORE in Redis with TTL=3600
   - Return response
```

## Redis Operations AI Should Use

### 1. Check Cache (Read)
```python
# Step 1: Build cache key
cache_key = f"chat:{hashlib.md5(f'{author_id}:{user_query}'.encode()).hexdigest()}"

# Step 2: Try to get from Redis
cached_response = redis_client.get(cache_key)

# Step 3: If found, parse and return
if cached_response:
    data = json.loads(cached_response)
    return data  # Contains: response, intent, fields, records, timestamp
```

### 2. Store in Cache (Write)
```python
# After generating fresh response
response_data = {
    "response": "თქვენ გაქვთ 25 მანქანა",
    "intent": "count_all_my_cars",
    "detected_fields": ["author"],
    "cached": False,
    "timestamp": "2026-06-02T23:40:00",
    "records": [...]  # Formatted records
}

# Store with 1 hour TTL
redis_client.setex(
    cache_key,
    3600,  # TTL in seconds
    json.dumps(response_data, ensure_ascii=False)
)
```

## Cache Key Uniqueness Rules

### What Makes Keys Unique
1. **Author ID**: Different dealers get different cache
2. **Exact query text**: "რამდენი მანქანა" ≠ "რამდენი ავტომობილი"
3. **Case sensitive**: "VIN" ≠ "vin" in query text

### Same Cache Key Examples
These queries generate the SAME cache key for same author:
- "რამდენი მანქანა მაქვს?" (asked at 10:00)
- "რამდენი მანქანა მაქვს?" (asked at 10:30)
→ Second query returns cached result from first

### Different Cache Key Examples
These queries generate DIFFERENT cache keys:
- Author 1748: "რამდენი მანქანა მაქვს?"
- Author 1749: "რამდენი მანქანა მაქვს?"
→ Each author gets their own cached result

## When AI Should NOT Use Cache

### Skip Cache Read If:
- Redis connection is unavailable
- Cache read throws error
- User explicitly requests fresh data

### Skip Cache Write If:
- Response contains error
- Query failed
- No valid data to cache
- Redis connection failed

## Cache Hit vs Miss Behavior

### On Cache HIT:
```
✅ Return cached response immediately
✅ Set cached=true in response
✅ Log: "[CACHE] HIT for query: {query}"
✅ Skip database query
✅ Skip intent detection
✅ Skip response generation
⚡ Response time: ~10-50ms
```

### On Cache MISS:
```
❌ Cache not found or expired
📊 Fetch from database
🧠 Detect intent
⚙️ Execute query logic
💬 Generate AI response
💾 Store in cache for next time
✅ Return fresh response
⏱️ Response time: ~200-500ms
```

## Error Handling for AI

### If Redis GET Fails:
```python
try:
    cached = redis_client.get(cache_key)
except Exception as e:
    # Log error but continue
    logger.error(f"[CACHE] Read error: {e}")
    cached = None  # Treat as cache miss
```

### If Redis SET Fails:
```python
try:
    redis_client.setex(cache_key, 3600, json_data)
except Exception as e:
    # Log error but still return response to user
    logger.error(f"[CACHE] Write error: {e}")
    # Continue - user gets response, just not cached
```

## Cache Invalidation

### When Cache Expires:
- **Automatic**: After 3600 seconds (1 hour)
- **Manual**: Admin calls `/cache/refresh` endpoint
- **Pattern**: No partial invalidation (all or nothing)

### What AI Should Know:
- Cached data is max 1 hour old
- If data changed in DB, cache might be stale for up to 1 hour
- For critical real-time queries, consider shorter TTL or skip cache

## Query Optimization Tips for AI

### Good Cache Candidates:
✅ "რამდენი მანქანა მაქვს?" - Rarely changes
✅ "სულ რამდენი დავალიანება მაქვს?" - Stable for hours
✅ "რომელი მანქანებია current სტატუსზე?" - Changes slowly

### Poor Cache Candidates:
❌ Queries with current timestamp
❌ Real-time status checks
❌ Queries that include "ახლა" (now) or "დღეს" (today)

## Data Structure in Cache

### Cached Object Format:
```json
{
  "response": "თქვენ გაქვთ 25 მანქანა. მათგან 20 current სტატუსზეა და 5 archive-ში.",
  "intent": "count_by_record_status",
  "detected_fields": ["author", "record_status"],
  "cached": false,
  "timestamp": "2026-06-02T23:40:15.123456",
  "records": [
    {
      "id": 470225,
      "vin": "1VWAP7A31EC021766",
      "manufacturer": "VOLKSWAGEN",
      "model": "Passat",
      "year": "2014",
      "warehouse": "All Cargo",
      "record_status": "current",
      "total_pay": 2595.0,
      "balance": -2595.0,
      "date": "2026-05-05"
    }
  ]
}
```

### Field Meanings:
- **response**: Georgian text response for user
- **intent**: Detected query intent
- **detected_fields**: Fields used in query
- **cached**: false when stored, true when retrieved
- **timestamp**: When response was generated
- **records**: Array of formatted vehicle records (max 10 fields each)

## AI Decision Tree for Redis

```
User Query Received
│
├─ Is Redis connected?
│  ├─ NO → Skip cache, process normally
│  └─ YES → Continue
│
├─ Generate cache_key
│
├─ Try GET cache_key
│  ├─ Found? → Return cached response
│  └─ Not found? → Continue
│
├─ Process query (DB + AI)
│
├─ Generate response
│
├─ Try SET cache_key with response
│  ├─ Success? → Log success
│  └─ Failed? → Log error, continue
│
└─ Return response to user
```

## Performance Expectations

### With Cache Hit:
- Response time: 10-50ms
- Database queries: 0
- OpenAI API calls: 0
- Cost: Minimal (Redis only)

### With Cache Miss:
- Response time: 200-500ms
- Database queries: 1
- OpenAI API calls: 2-3 (intent + response)
- Cost: Higher (DB + OpenAI)

### Cache Hit Rate Target:
- **Goal**: 60-80% hit rate for typical usage
- **Monitoring**: Track hits vs misses in logs
- **Optimization**: Increase TTL if data changes infrequently

## Query Examples for AI Learning / AI-ის სწავლების მაგალითები

### Example 1: Count All Cars
**Georgian Query**: "რამდენი მანქანა მაქვს?"
**Cache Key**: `chat:md5(1748:რამდენი მანქანა მაქვს?)`
**Cached Response**:
```json
{
  "response": "თქვენ გაქვთ სულ 255 მანქანა.",
  "intent": "count_all_my_cars",
  "detected_fields": ["author"],
  "cached": true,
  "timestamp": "2026-06-02T23:49:53.811876",
  "records": []
}
```

### Example 2: Count by Status
**Georgian Query**: "რამდენია current და რამდენია archive?"
**Cache Key**: `chat:md5(1748:რამდენია current და რამდენია archive?)`
**Cached Response**:
```json
{
  "response": "თქვენ გაქვთ 200 current მანქანა და 55 archive-ში.",
  "intent": "count_by_record_status",
  "detected_fields": ["author", "record_status"],
  "cached": true,
  "timestamp": "2026-06-02T23:50:00.000000",
  "records": []
}
```

### Example 3: Total Balance Query
**Georgian Query**: "სულ რამდენი მაქვს დავალიანება?"
**Cache Key**: `chat:md5(1748:სულ რამდენი მაქვს დავალიანება?)`
**Cached Response**:
```json
{
  "response": "თქვენი ჯამური დავალიანება არის 125,450 ლარი.",
  "intent": "sum_total_balance",
  "detected_fields": ["author", "f2"],
  "cached": true,
  "timestamp": "2026-06-02T23:50:15.000000",
  "records": []
}
```

### Example 4: Cars with Debt
**Georgian Query**: "რომელ მანქანებს აქვთ დავალიანება?"
**Cache Key**: `chat:md5(1748:რომელ მანქანებს აქვთ დავალიანება?)`
**Cached Response**:
```json
{
  "response": "თქვენ გაქვთ 145 მანქანა, რომელზეც დავალიანება დარჩა.",
  "intent": "cars_with_positive_balance",
  "detected_fields": ["author", "f2"],
  "cached": true,
  "timestamp": "2026-06-02T23:50:30.000000",
  "records": []
}
```

### Example 5: VIN Search
**Georgian Query**: "ამ VIN-ზე მომეცი ინფორმაცია: 1VWAP7A31EC021766"
**Cache Key**: `chat:md5(1748:ამ VIN-ზე მომეცი ინფორმაცია: 1VWAP7A31EC021766)`
**Cached Response**:
```json
{
  "response": "VIN 1VWAP7A31EC021766 - VOLKSWAGEN Passat, 2014 წელი. საწყობი: All Cargo. სტატუსი: current. სულ გადასახდელი: 2595 ლარი, დავალიანება: -2595 ლარი.",
  "intent": "vehicle_by_vin",
  "detected_fields": ["author", "vin"],
  "cached": true,
  "timestamp": "2026-06-02T23:50:45.000000",
  "records": []
}
```

### Example 6: Financial Details by VIN
**Georgian Query**: "ამ VIN-ზე რამდენი მაქვს გადასახდელი: 5XYRKDLF2PG229955"
**Cache Key**: `chat:md5(1748:ამ VIN-ზე რამდენი მაქვს გადასახდელი: 5XYRKDLF2PG229955)`
**Cached Response**:
```json
{
  "response": "VIN 5XYRKDLF2PG229955 (KIA Sorento 2023): სულ გადასახდელი 15,465 ლარი. გადახდილი: 16,970 ლარი. დავალიანება: -1,505 ლარი.",
  "intent": "vehicle_finance_by_vin",
  "detected_fields": ["author", "vin", "f1", "f2"],
  "cached": true,
  "timestamp": "2026-06-02T23:51:00.000000",
  "records": []
}
```

### Example 7: Group by Make/Model/Year
**Georgian Query**: "მარკების მიხედვით დამითვალე"
**Cache Key**: `chat:md5(1748:მარკების მიხედვით დამითვალე)`
**Cached Response**:
```json
{
  "response": "VOLKSWAGEN - 45 მანქანა, KIA - 38 მანქანა, TOYOTA - 32 მანქანა, BMW - 28 მანქანა, HYUNDAI - 25 მანქანა, სხვა - 87 მანქანა.",
  "intent": "group_by_make_model_year",
  "detected_fields": ["author", "manufacturer"],
  "cached": true,
  "timestamp": "2026-06-02T23:51:15.000000",
  "records": []
}
```

### Example 8: By Location/Warehouse
**Georgian Query**: "რომელი მანქანებია საწყობში?"
**Cache Key**: `chat:md5(1748:რომელი მანქანებია საწყობში?)`
**Cached Response**:
```json
{
  "response": "All Cargo - 120 მანქანა, Lion K 2 - 85 მანქანა, Lion K 1 - 50 მანქანა.",
  "intent": "cars_by_location_or_stage",
  "detected_fields": ["author", "warehouse"],
  "cached": true,
  "timestamp": "2026-06-02T23:51:30.000000",
  "records": []
}
```

### Example 9: By Period
**Georgian Query**: "ამ თვეში ნაყიდი მანქანები"
**Cache Key**: `chat:md5(1748:ამ თვეში ნაყიდი მანქანები)`
**Cached Response**:
```json
{
  "response": "ამ თვეში (ბოლო 30 დღეში) თქვენ ნაყიდი გაქვთ 42 მანქანა.",
  "intent": "records_by_period",
  "detected_fields": ["author", "date"],
  "cached": true,
  "timestamp": "2026-06-02T23:51:45.000000",
  "records": []
}
```

### Example 10: Missing Documents
**Georgian Query**: "რომელ მანქანებს არ აქვთ title?"
**Cache Key**: `chat:md5(1748:რომელ მანქანებს არ აქვთ title?)`
**Cached Response**:
```json
{
  "response": "თქვენ გაქვთ 23 მანქანა, რომელზეც title მიღებული არ არის.",
  "intent": "missing_documents_or_title",
  "detected_fields": ["author", "title_received"],
  "cached": true,
  "timestamp": "2026-06-02T23:52:00.000000",
  "records": []
}
```

## Creative Query Variations for AI / AI-ის კრეატიული მოთხოვნების ვარიაციები

### ⚠️ IMPORTANT: These Examples Are NOT Mandatory

**AI can and SHOULD create its own queries beyond these examples!**

The examples below are provided to help AI understand:
- Common Georgian phrasing patterns
- Synonyms and variations in the language
- How to map different user intents to the 10 standard intents
- Response formatting expectations

**However, AI is NOT limited to these examples.** If a user asks something creative or uses different wording, AI should:
1. Understand the underlying intent
2. Map it to one of the 10 standard intents
3. Generate an appropriate response
4. Create a cache key for that unique query
5. Cache the result for future use

### Counting Variations
- "სულ რამდენი ავტომობილია?" = "რამდენი მანქანა მაქვს?"
- "ჩემი მანქანების რაოდენობა" = "რამდენი მანქანა მაქვს?"
- "მანქანების ჯამი" = "რამდენი მანქანა მაქვს?"
- **AI can also understand**: "სულ რამდენი ჩანაწერი მაქვს?", "მოთხოვნილი რაოდენობა", "ინვენტარი"

### Balance Variations
- "რამდენია დარჩენილი გადასახდელი?" = "სულ რამდენი მაქვს დავალიანება?"
- "ჯამური ბალანსი" = "სულ რამდენი მაქვს დავალიანება?"
- "რამდენი ვალი მაქვს?" = "სულ რამდენი მაქვს დავალიანება?"
- **AI can also understand**: "ჯამური ღირებულება", "სულ რამდენი გადამხდელი", "ფინანსური ჯამი"

### Location Variations
- "სად არის ჩემი მანქანები?" = "რომელი მანქანებია საწყობში?"
- "ლოკაციების მიხედვით დამითვალე" = "რომელი მანქანებია საწყობში?"
- "საწყობის მიხედვით გაფილტრე" = "რომელი მანქანებია საწყობში?"
- **AI can also understand**: "რომელი მოდის ფოთში?", "ამერიკის საწყობი", "მიწოდების ადგილი"

### VIN Variations
- "ვინ კოდი 1VWAP7A31EC021766 რა ინფორმაციაა?" = "ამ VIN-ზე მომეცი ინფორმაცია: 1VWAP7A31EC021766"
- "1VWAP7A31EC021766 სად არის?" = "ამ VIN-ზე მომეცი ინფორმაცია: 1VWAP7A31EC021766"
- "ამ მანქანაზე რა გაქვთ?" = "ამ VIN-ზე მომეცი ინფორმაცია: [VIN]"
- **AI can also understand**: "უნიკალური კოდი", "მანქანის კოდი", "ავტომობილის ნომერი"

### Status Variations
- "current მანქანები რამდენია?" = "რამდენია current და რამდენია archive?"
- "აქტიური და არქივირებული მანქანები" = "რამდენია current და რამდენია archive?"
- "სტატუსების მიხედვით დამითვალე" = "რამდენია current და რამდენია archive?"
- **AI can also understand**: "მიმდინარე ჩანაწერები", "დასრულებული", "ისტორია"

### Time Period Variations
- "ბოლო თვეში ნაყიდი" = "ამ თვეში ნაყიდი მანქანები"
- "2026 წლის ჩანაწერები" = "ამ თვეში ნაყიდი მანქანები"
- "რა მანქანა ვიყიდე მაისში?" = "ამ თვეში ნაყიდი მანქანები"
- **AI can also understand**: "ბოლო კვირაში", "წელს", "გარკვეული თარიღის შემდეგ"

## AI Creative Query Generation Guidelines / AI-ის კრეატიული მოთხოვნების გენერაციის სახელმძღვანელო

### When User Asks Something Unique:

**Example 1**: User asks "რამდენი VOLKSWAGEN-ი მაქვს?"
- This is NOT in the examples
- But AI recognizes it's a "group_by_make_model_year" intent filtered by manufacturer
- AI generates response: "თქვენ გაქვთ 45 VOLKSWAGEN"
- AI creates unique cache key: `chat:md5(1748:რამდენი VOLKSWAGEN-ი მაქვს?)`
- AI caches the response for future use

**Example 2**: User asks "რომელი მანქანებია 2020 წლის?"
- This is NOT in the examples
- But AI recognizes it's a "group_by_make_model_year" intent filtered by year
- AI generates response: "თქვენ გაქვთ 28 მანქანა, რომელიც 2020 წელს გამოშვებული"
- AI creates unique cache key and caches it

**Example 3**: User asks "რა თანხა გადაიხადა კლიენტმა ამ VIN-ზე?"
- This is NOT in the examples
- But AI recognizes it's a "vehicle_finance_by_vin" intent
- AI extracts VIN and generates financial response
- AI creates unique cache key and caches it

### Rules for Creative Queries:

✅ **DO**:
- Map any user query to one of the 10 standard intents
- Create unique cache keys for unique queries
- Cache all successful responses
- Generate natural Georgian responses
- Filter by author_id always
- Handle null/empty values gracefully

❌ **DON'T**:
- Invent data that doesn't exist
- Ignore the 10 standard intents (they cover all use cases)
- Skip author_id filtering
- Cache error responses
- Respond in languages other than Georgian

### Cache Key Strategy for Creative Queries:

Every unique query gets its own cache key:
```python
# User asks something creative
user_query = "რამდენი BMW-ი მაქვს 2020 წლის?"
cache_key = f"chat:{md5(f'{author_id}:{user_query}')}"

# This key is unique and will be cached
# Next time same user asks same question → cache hit
# Different user asks same question → different cache key
```

### Response Generation for Creative Queries:

AI should:
1. Understand the intent (even if phrasing is unique)
2. Extract relevant parameters (VIN, dates, makes, etc.)
3. Execute the appropriate intent logic
4. Generate a natural Georgian response
5. Store in cache with the unique query key

**Example Response Generation**:
```
User: "რამდენი BMW-ი მაქვს 2020 წლის?"
Intent Detected: group_by_make_model_year (filtered)
Response: "თქვენ გაქვთ 12 BMW, რომელიც 2020 წელს გამოშვებული"
Cache Key: chat:unique_hash_for_this_query
Cached: Yes (for 1 hour)
```

## Summary for AI

**Before answering user query**:
1. Generate cache key from author_id + query
2. Check Redis cache
3. If found → return immediately
4. If not found → process and cache result

**For creative query generation**:
- Use the examples above to understand query patterns
- Recognize synonyms and variations in Georgian
- Map user intent to one of the 10 standard intents
- Generate natural Georgian responses based on cached data structure
- Always filter by author_id first for security

**Key principle**: Cache is transparent to user, improves performance, gracefully degrades if unavailable.
