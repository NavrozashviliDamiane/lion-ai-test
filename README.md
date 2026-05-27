# Lion AI Chat API

A FastAPI application for intelligent chat interactions with vehicle auction and logistics data using Redis embeddings and OpenAI LLM.

## Features

- **AI Chat Controller**: FastAPI endpoint for conversational AI
- **Redis Embeddings**: Semantic search using vector embeddings stored in Redis cache
- **Context-Aware Responses**: LLM analyzes database context without fixed retrieval
- **MariaDB Integration**: Fetches vehicle and transaction data via stored procedures
- **OpenAI Integration**: Uses GPT-4o for intelligent responses

## Architecture

```
User Query
    ↓
Chat Controller (FastAPI)
    ↓
Embedding Search (Redis)
    ↓
Context Retrieval + LLM Analysis
    ↓
AI Response with Context
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

**Required environment variables:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`: Redis connection details
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: MariaDB connection details

### 3. Run the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```

### Chat Endpoint
```
POST /chat
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "What vehicles do we have from Volkswagen?"
    }
  ],
  "author_id": 1748
}
```

**Response:**
```json
{
  "response": "Based on our records, we have a 2014 Volkswagen Passat...",
  "context_records": [
    {
      "record_id": 470225,
      "similarity": 0.92,
      "manufacturer": "VOLKSWAGEN",
      "model": "Passat",
      "year": "2014",
      "vin": "1VWAP7A31EC021766"
    }
  ],
  "model": "gpt-4o"
}
```

### Search Embeddings
```
GET /search?query=Kia+Sorento&author_id=1748&top_k=3
```

### Refresh Embeddings
```
POST /refresh-embeddings?author_id=1748
```

## How It Works

1. **Initialization**: On startup, the application fetches data from MariaDB using `PROC_GET_JSON(1748)` and generates embeddings for each record using OpenAI's embedding model.

2. **Storage**: Embeddings are stored in Redis with the record content and original text for quick retrieval.

3. **Query Processing**: When a user sends a chat message:
   - The query is converted to an embedding
   - Semantic search finds the most relevant records in Redis
   - Context is passed to GPT-4o along with the conversation history
   - The LLM generates a contextual response

4. **Response**: Returns the AI response along with the context records used.

## Database Schema

The application expects data from `PROC_GET_JSON(author_id)` which returns vehicle records with fields like:
- `id`: Record ID
- `manufacturer`: Vehicle manufacturer
- `model`: Vehicle model
- `year`: Manufacturing year
- `vin`: Vehicle Identification Number
- `auction_pay`: Auction payment amount
- `warehouse`: Storage location
- And many more (see `field_descrptions.json`)

## Performance Considerations

- Embeddings are cached in Redis for 30 days
- Semantic search is performed in-memory without database queries
- Context is limited to top 3 most relevant records to reduce token usage
- Temperature set to 0.3 for consistent, factual responses

## Error Handling

The API includes comprehensive error handling for:
- Database connection failures
- Redis connection issues
- OpenAI API errors
- Invalid requests

All errors return appropriate HTTP status codes with descriptive messages.
