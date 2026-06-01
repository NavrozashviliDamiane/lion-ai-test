# Lion Trans Chat AI - Implementation Guide

## Overview

This is a Georgian-language Chat AI system for the Lion Trans Dealer Cabinet. It uses **context engineering** with three JSON configuration files to understand user queries, extract intents, and provide intelligent responses based on vehicle data stored in Redis cache and a MariaDB database.

## Architecture

### Core Components

1. **main.py** - FastAPI application with chat endpoints
2. **agent_context_bundle.json** - System rules, security scope, and core business logic
3. **fields_context.json** - Detailed field definitions with Georgian synonyms and usage guidelines
4. **query_map.json** - Intent definitions with example queries and execution logic
5. **config.py** - Configuration for Redis, Database, and OpenAI
6. **database.py** - Database connection and data fetching

### Data Flow

```
User Query (Georgian)
    ↓
Intent Detection (OpenAI GPT-4)
    ↓
Field Extraction & Parameter Parsing
    ↓
Redis Cache Check
    ↓
Database Query (if not cached)
    ↓
Intent Execution (JSON Logic)
    ↓
Response Generation (Georgian)
    ↓
Cache Storage (1 hour TTL)
    ↓
Return to User
```

## Context Engineering System

### 1. Agent Context Bundle (`agent_context_bundle.json`)

Defines the overall system behavior:

- **Core Rules**: Project scope, data source, security constraints
- **Security Scope**: Dealer filtering - all queries filtered by `author == CURRENT_DEALER`
- **Record Status Values**: `current` or `archive`
- **Balance Logic**: `f2 = f1 - (pm_1 + pm_2 + pm_3 + pm_4 + pm_5)`
- **System Prompt**: Instructions for the AI chatbot

### 2. Fields Context (`fields_context.json`)

Describes each data field with:

- **Field Name**: Database column name (e.g., `usa_geo`, `warehouse`)
- **Label**: Human-readable name
- **Category**: Type of field (location, identifier, person_party, etc.)
- **Business Description**: What the field means in business terms
- **Synonyms**: Georgian and English variations
- **Example User Questions**: Common queries using this field
- **Agent Usage**: How the AI should use this field
- **Response Rule**: How to present the data
- **Nullable Handling**: What to do if data is missing

### 3. Query Map (`query_map.json`)

Defines intents with:

- **Intent Name**: Unique identifier (e.g., `count_all_my_cars`)
- **User Examples**: Georgian example queries
- **Required Fields**: Fields needed for this intent
- **JSON Logic**: How to process records
- **SQL Template**: Alternative SQL execution
- **Response Rule**: How to format the answer

## Supported Intents

| Intent | Description | Example Query |
|--------|-------------|----------------|
| `count_all_my_cars` | Total vehicle count | "სულ რამდენი მანქანა მაქვს?" |
| `count_by_record_status` | Count by current/archive | "რამდენია current და რამდენია archive?" |
| `sum_total_balance` | Total outstanding balance | "სულ რამდენი მაქვს დავალიანება?" |
| `cars_with_positive_balance` | Vehicles with debt | "რომელ მანქანებს აქვთ დავალიანება?" |
| `vehicle_by_vin` | Get vehicle by VIN | "ამ VIN-ზე მომეცი ინფორმაცია: 1VWAP7A31EC021766" |
| `vehicle_finance_by_vin` | Financial info by VIN | "ამ VIN-ზე რამდენი მაქვს გადასახდელი?" |
| `group_by_make_model_year` | Group by manufacturer | "რამდენი Toyota მაქვს?" |
| `cars_by_location_or_stage` | Filter by warehouse/container | "რომელი მანქანებია საწყობში?" |
| `records_by_period` | Filter by date range | "ამ თვეში ნაყიდი მანქანები" |
| `missing_documents_or_title` | Find missing documents | "რომელ მანქანებს არ აქვთ title?" |

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

DB_HOST=185.49.165.116
DB_PORT=3310
DB_USER=liontest_user
DB_PASSWORD=nR2aJ6eS2u
DB_NAME=vps_liontest_db

OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small

AUTHOR_ID=1748
```

### 3. Start Redis Server

```bash
redis-server
```

### 4. Run the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /chat

Send a Georgian query and get an intelligent response.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "სულ რამდენი მანქანა მაქვს?"}
  ],
  "author_id": 1748
}
```

**Response:**
```json
{
  "response": "თქვენ გაქვთ სულ 2 მანქანა.",
  "intent": "count_all_my_cars",
  "detected_fields": ["author"],
  "cached": false,
  "timestamp": "2026-05-06T19:28:44.123456"
}
```

### GET /context-guidance

Get intent and field detection for a query without executing it.

**Request:**
```
GET /context-guidance?query=რამდენი%20მანქანა%20მაქვს%20საწყობში
```

**Response:**
```json
{
  "query": "რამდენი მანქანა მაქვს საწყობში",
  "detected_intent": "cars_by_location_or_stage",
  "confidence": 0.95,
  "detected_fields": ["warehouse", "author"],
  "parameters": {},
  "intent_details": {...},
  "field_details": [...]
}
```

### GET /health

Check system health and connectivity.

**Response:**
```json
{
  "status": "healthy",
  "redis": "connected",
  "contexts_loaded": true
}
```

### GET /

Get API information.

## Testing

### Using Python Test Script

```bash
python test_chat_ai.py
```

### Using cURL

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "სულ რამდენი მანქანა მაქვს?"}],
    "author_id": 1748
  }'
```

### Using Python Requests

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "messages": [{"role": "user", "content": "სულ რამდენი მანქანა მაქვს?"}],
        "author_id": 1748
    }
)

print(response.json())
```

## Context Engineering Features

### 1. Intent Detection

The system uses OpenAI GPT-4 to analyze Georgian queries and detect the user's intent. It matches the query against known intents and extracts relevant parameters.

### 2. Field Extraction

Based on the detected intent and user query, the system identifies which fields are relevant and should be included in the response.

### 3. Security Filtering

All queries are automatically filtered by `author_id` to ensure dealers only see their own vehicle records. This is enforced at the database level and in the JSON logic.

### 4. Redis Caching

Query results are cached for 1 hour using Redis. Cache keys are generated from the author_id and query hash, ensuring personalized caching.

### 5. Georgian Language Support

- All system prompts are in Georgian
- Field synonyms include Georgian variations
- Responses are generated in Georgian using GPT-4
- User queries are expected in Georgian

### 6. Data Validation

- Null/empty field handling: If data is missing, the system reports it rather than hallucinating
- Type conversion: Numbers are properly converted for calculations
- Date parsing: Dates are parsed and filtered correctly

## Key Business Logic

### Balance Calculation

```
balance (f2) = Total Pay (f1) - Sum of Payments (pm_1 + pm_2 + pm_3 + pm_4 + pm_5)
```

If `f2` is already provided by the API, it's used as the authoritative value.

### Dealer Scope

Every query must filter records where:
```
record.author == CURRENT_DEALER
```

This is enforced in:
- Intent execution logic
- JSON filters
- SQL templates

### Record Status

Records have two statuses:
- `current`: Active vehicles
- `archive`: Archived vehicles

Users can query by status or see both.

## Performance Optimization

### Caching Strategy

- **Cache Key**: `chat:{md5(author_id:query)}`
- **TTL**: 3600 seconds (1 hour)
- **Fallback**: If Redis is unavailable, queries still work without caching

### Query Optimization

- Intent detection uses low temperature (0.3) for consistency
- Response generation uses moderate temperature (0.7) for naturalness
- Max tokens limited to prevent excessive API usage

## Error Handling

The system handles:

- Missing Redis connection (graceful degradation)
- Database connection errors (HTTP 500)
- Invalid JSON in context files (startup error)
- OpenAI API errors (fallback responses)
- Missing or null data fields (explicit reporting)

## Extending the System

### Adding a New Intent

1. Add intent definition to `query_map.json`:
```json
{
  "intent": "new_intent_name",
  "user_examples": ["Georgian example 1", "Georgian example 2"],
  "required_fields": ["field1", "field2"],
  "json_logic": "...",
  "sql_template": "...",
  "response": "Response template"
}
```

2. Add execution logic in `execute_intent()` function in `main.py`:
```python
elif intent == "new_intent_name":
    # Implementation
    return result
```

### Adding a New Field

1. Add field definition to `fields_context.json`:
```json
{
  "id": 999,
  "field_name": "new_field",
  "label": "New Field",
  "category": "category_type",
  "data_type": "string|null",
  "business_description": "...",
  "synonyms": ["synonym1", "synonym2"],
  "example_user_questions": ["..."],
  "agent_usage": "...",
  "response_rule": "...",
  "nullable_handling": "..."
}
```

2. The field will automatically be available for intent detection and filtering.

## Troubleshooting

### Redis Connection Issues

```
⚠ Redis connection failed: Connection refused
```

**Solution**: Start Redis server or check connection settings in `.env`

### Database Connection Issues

```
Error connecting to MariaDB: Access denied for user
```

**Solution**: Verify database credentials in `.env` and ensure database is accessible

### OpenAI API Issues

```
Error: Invalid API key provided
```

**Solution**: Check `OPENAI_API_KEY` in `.env` and ensure it's valid

### Intent Detection Issues

If the system detects the wrong intent, check:
1. Is the query in Georgian?
2. Are there similar intents that might be confused?
3. Try the `/context-guidance` endpoint to see what was detected

## Monitoring

Check system health:

```bash
curl http://localhost:8000/health
```

View logs:

```bash
tail -f logs/chat_ai.log
```

## Security Considerations

1. **Dealer Isolation**: All queries are filtered by `author_id`
2. **API Key Management**: Store `OPENAI_API_KEY` in environment variables
3. **Database Credentials**: Use `.env` file (never commit to git)
4. **Input Validation**: User queries are validated before processing
5. **Rate Limiting**: Consider adding rate limiting for production

## Future Enhancements

- [ ] Multi-language support (English, Russian)
- [ ] Advanced analytics and reporting
- [ ] Custom intent creation UI
- [ ] Query logging and analytics
- [ ] Webhook integrations
- [ ] Batch query processing
- [ ] Advanced caching strategies
- [ ] A/B testing for response generation

## Support

For issues or questions, refer to:
- `chat_examples.md` - Example queries
- `test_questions.md` - Additional test cases
- `response-example.json` - Sample data structure
