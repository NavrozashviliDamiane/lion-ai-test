# Lion Trans Chat AI - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file in the project root with your credentials:
```env
OPENAI_API_KEY=sk-your-key-here
REDIS_HOST=localhost
REDIS_PORT=6379
DB_HOST=185.49.165.116
DB_PORT=3310
DB_USER=liontest_user
DB_PASSWORD=nR2aJ6eS2u
DB_NAME=vps_liontest_db
```

### 3. Start Redis
```bash
redis-server
```

### 4. Run the Application
```bash
python main.py
```

You should see:
```
✓ Redis connected
✓ Context bundles loaded successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Testing the API

### Option 1: Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "messages": [{"role": "user", "content": "სულ რამდენი მანქანა მაქვს?"}],
        "author_id": 1748
    }
)

print(response.json()["response"])
```

### Option 2: Using cURL
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "სულ რამდენი მანქანა მაქვს?"}], "author_id": 1748}'
```

### Option 3: Using Test Script
```bash
python test_chat_ai.py
```

## Example Queries (Georgian)

### Count Queries
- "სულ რამდენი მანქანა მაქვს?" → Returns total count
- "რამდენი Toyota მაქვს?" → Returns count by make
- "რამდენია current და რამდენია archive?" → Returns status breakdown

### Financial Queries
- "სულ რამდენი მაქვს დავალიანება?" → Returns total balance
- "რომელ მანქანებს აქვთ დავალიანება?" → Returns vehicles with debt

### Location Queries
- "რომელი მანქანებია საწყობში?" → Returns warehouse inventory
- "რომელი მანქანებია კონტეინერში?" → Returns container inventory

### VIN Queries
- "ამ VIN-ზე მომეცი ინფორმაცია: 1VWAP7A31EC021766" → Returns full vehicle details
- "ამ VIN-ზე რამდენი მაქვს გადასახდელი?" → Returns financial info

### Date Queries
- "ამ თვეში ნაყიდი მანქანები" → Returns this month's purchases
- "ბოლო 30 დღეში ნაყიდი ავტომობილები" → Returns last 30 days

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Send query and get response |
| `/context-guidance` | GET | See intent detection details |
| `/health` | GET | Check system status |
| `/` | GET | API information |

## Understanding the Response

```json
{
  "response": "თქვენ გაქვთ სულ 2 მანქანა.",
  "intent": "count_all_my_cars",
  "detected_fields": ["author"],
  "cached": false,
  "timestamp": "2026-05-06T19:28:44.123456"
}
```

- **response**: The answer in Georgian
- **intent**: What the system understood you wanted
- **detected_fields**: Which database fields were used
- **cached**: Whether this result came from cache
- **timestamp**: When the query was processed

## How It Works

1. **You ask in Georgian** → "სულ რამდენი მანქანა მაქვს?"
2. **AI detects intent** → `count_all_my_cars`
3. **System extracts fields** → `author`, `record_status`
4. **Database is queried** → Filters by your dealer ID
5. **Results are cached** → For 1 hour
6. **Response is generated** → In Georgian
7. **You get the answer** → "თქვენ გაქვთ სულ 2 მანქანა."

## Context Engineering

The system uses three JSON files to understand your business:

1. **agent_context_bundle.json** - System rules and security
2. **fields_context.json** - What each database field means
3. **query_map.json** - How to handle different types of questions

These files teach the AI about your business domain, so it can:
- Understand Georgian business terminology
- Know which fields to use for each query
- Apply correct security filtering
- Generate accurate responses

## Troubleshooting

### "Connection refused" error
- Make sure Redis is running: `redis-server`
- Check Redis host/port in `.env`

### "Access denied" error
- Verify database credentials in `.env`
- Check database is accessible from your network

### "Invalid API key" error
- Check `OPENAI_API_KEY` in `.env`
- Ensure key is valid and has API access

### Wrong intent detected
- Try the `/context-guidance` endpoint to see what was detected
- Check if query is in Georgian
- Review similar intents in `query_map.json`

## Next Steps

1. Read `IMPLEMENTATION_GUIDE.md` for detailed documentation
2. Check `chat_examples.md` for more query examples
3. Review `test_questions.md` for additional test cases
4. Explore `response-example.json` to understand data structure

## Key Features

✅ Georgian language support  
✅ Automatic intent detection  
✅ Redis caching (1 hour TTL)  
✅ Dealer isolation (security)  
✅ Financial calculations  
✅ Location filtering  
✅ VIN-based lookups  
✅ Date range filtering  
✅ Error handling  
✅ Health monitoring  

## Architecture

```
User Query (Georgian)
    ↓
FastAPI Endpoint
    ↓
Intent Detection (GPT-4)
    ↓
Redis Cache Check
    ↓
Database Query
    ↓
Result Processing
    ↓
Response Generation (Georgian)
    ↓
Cache Storage
    ↓
Return to User
```

## Performance

- **Intent Detection**: ~500ms (OpenAI API)
- **Database Query**: ~100-500ms (depends on data size)
- **Response Generation**: ~500-1000ms (OpenAI API)
- **Cached Response**: ~10ms (Redis)

Total: 1-2 seconds for new queries, 10ms for cached queries

## Security

- All queries filtered by `author_id` (dealer isolation)
- Database credentials in `.env` (not in code)
- OpenAI API key in environment variables
- No sensitive data logged
- Redis optional (graceful degradation)

## Support

For detailed information, see:
- `IMPLEMENTATION_GUIDE.md` - Full documentation
- `chat_examples.md` - Example queries
- `test_questions.md` - Test cases
- `response-example.json` - Data format
