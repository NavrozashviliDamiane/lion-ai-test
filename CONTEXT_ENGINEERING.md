# Context Engineering Guide

## What is Context Engineering?

Context Engineering is the practice of teaching AI systems about your specific business domain through structured configuration files. Instead of relying on the AI's general knowledge, you provide explicit rules, field definitions, and intent mappings that guide the AI to make correct decisions for your specific use case.

## The Three Context Files

### 1. agent_context_bundle.json

This file defines the **core rules and system behavior**.

```json
{
  "core_rules": {
    "project": "Lion Trans Dealer Cabinet AI Chatbot",
    "data_source": "API/JSON, 1-5000 vehicle records",
    "security_scope": {
      "dealer_filter_field": "author",
      "rule": "ყველა query ჯერ უნდა გაფილტროს current dealer-ის მიხედვით"
    },
    "record_status_values": ["current", "archive"],
    "balance_logic": "balance/f2 = Total Pay/f1 - (pm_1 + pm_2 + pm_3 + pm_4 + pm_5)",
    "no_hallucination": "თუ ველი/ჩანაწერი/თარიღი/თანხა არ არსებობს..."
  },
  "system_prompt": "შენ ხარ Lion Trans Dealer Cabinet-ის AI Chatbot..."
}
```

**Key Components:**

- **core_rules**: Business constraints and logic
- **security_scope**: How to filter data (dealer isolation)
- **record_status_values**: Valid status values
- **balance_logic**: Financial calculation rules
- **no_hallucination**: Instruction to not make up data
- **system_prompt**: Main instruction for the AI

**Why it matters:**
- Ensures consistent behavior across all queries
- Enforces security constraints
- Defines business logic
- Prevents hallucination

### 2. fields_context.json

This file describes **each database field** in business terms.

```json
{
  "fields": [
    {
      "id": 1,
      "field_name": "usa_geo",
      "label": "USA-GEO",
      "category": "location",
      "data_type": "string|null",
      "business_description": "აღმნიშვნელი სტატუსი სად მიდის მანქანა",
      "source_description": "ამ ველში ქვეყნების სია...",
      "synonyms": ["ლოკაცია", "სად", "USA-GEO"],
      "example_user_questions": [
        "რომელი ქვეყნაში მიდის მანქანა?",
        "USA-GEO-ის მიხედვით რამდენი მანქანა მაქვს?"
      ],
      "agent_usage": "გამოიყენე ლოკაციის მიხედვით ფილტრაციის/დაჯგუფებისთვის",
      "response_rule": "დააბრუნე მოკლე, ბიზნესისთვის გასაგები მნიშვნელობა",
      "nullable_handling": "თუ მნიშვნელობა ცარიელია/null — არ გამოიგონო"
    }
  ]
}
```

**Key Components:**

- **field_name**: Database column name
- **label**: Human-readable name
- **category**: Type of field (location, identifier, person_party, etc.)
- **business_description**: What it means in business
- **synonyms**: Georgian and English variations
- **example_user_questions**: How users might ask about this field
- **agent_usage**: How the AI should use this field
- **response_rule**: How to present the data
- **nullable_handling**: What to do if data is missing

**Why it matters:**
- Teaches the AI what each field represents
- Provides synonyms for natural language understanding
- Shows example questions to improve intent detection
- Defines how to handle missing data

### 3. query_map.json

This file defines **intents and how to execute them**.

```json
{
  "query_map": [
    {
      "intent": "count_all_my_cars",
      "user_examples": [
        "სულ რამდენი მანქანა მაქვს?",
        "რამდენი ავტომობილია ჩემს ბაზაში?"
      ],
      "required_fields": ["author"],
      "json_logic": "records.filter(r => r.author == CURRENT_DEALER).length",
      "sql_template": "SELECT COUNT(*) AS total FROM records WHERE author = :current_dealer;",
      "response": "თქვი ჯამური რაოდენობა მხოლოდ ამ დილერის ჩანაწერებში."
    }
  ]
}
```

**Key Components:**

- **intent**: Unique identifier for this type of query
- **user_examples**: Georgian examples of how users ask this question
- **required_fields**: Which fields must be present
- **json_logic**: How to process the data (JavaScript-like)
- **sql_template**: Alternative SQL execution
- **response**: How to format the answer

**Why it matters:**
- Maps user questions to specific actions
- Provides examples for intent detection training
- Defines execution logic
- Ensures consistent responses

## How Context Engineering Works in the System

### Step 1: User Sends Query

```
User: "სულ რამდენი მანქანა მაქვს?"
```

### Step 2: Intent Detection

The system uses GPT-4 with the context files to detect:

```python
system_prompt = """
Available intents:
- count_all_my_cars
- count_by_record_status
- sum_total_balance
...
"""
```

The AI analyzes the query against:
- User examples from `query_map.json`
- Field synonyms from `fields_context.json`
- Business rules from `agent_context_bundle.json`

Result:
```json
{
  "intent": "count_all_my_cars",
  "detected_fields": ["author"],
  "confidence": 0.95
}
```

### Step 3: Field Extraction

The system identifies which fields are relevant:

```python
detected_fields = ["author"]  # From intent definition
```

### Step 4: Data Processing

The system executes the intent logic:

```python
# From query_map.json
json_logic = "records.filter(r => r.author == CURRENT_DEALER).length"

# Applied to data
result = len([r for r in records if r.author == "GE MOTORS"])
# Result: 2
```

### Step 5: Response Generation

The system generates a Georgian response:

```python
system_prompt = """
The user asked: "სულ რამდენი მანქანა მაქვს?"
The intent is: count_all_my_cars
The result is: 2

Generate a natural Georgian response.
"""

# Result: "თქვენ გაქვთ სულ 2 მანქანა."
```

## Context Engineering Best Practices

### 1. Keep Synonyms Comprehensive

Include all variations users might use:

```json
"synonyms": [
  "დილერი",
  "Dealer",
  "author",
  "ჩემი დილერი",
  "dealer name",
  "ავტორი"
]
```

### 2. Provide Clear Business Descriptions

Don't just describe the database field, explain the business meaning:

```json
"business_description": "დილერის დასახელება",
"source_description": "დილერის სახელი და გვარი ან კომპანიის სახელი, რომელიც განისაზღვრება ID სახელი მოდის ცხრილიდან users"
```

### 3. Include Diverse Example Questions

Cover different ways users might ask:

```json
"example_user_questions": [
  "რომელი ქვეყნაში მიდის მანქანა?",
  "ფასდაკლებაზე ხომ არ არის?",
  "USA-GEO-ის მიხედვით რამდენი მანქანა მაქვს?"
]
```

### 4. Define Clear Execution Logic

Make the logic explicit and testable:

```json
"json_logic": "records.filter(r => r.author == CURRENT_DEALER && number(r.f2) > 0)"
```

### 5. Handle Edge Cases

Specify what to do with missing or invalid data:

```json
"nullable_handling": "თუ მნიშვნელობა ცარიელია/null — არ გამოიგონო; უთხარი, რომ მონაცემი არ არის შევსებული."
```

### 6. Enforce Security Rules

Always include dealer filtering:

```json
"security_scope": {
  "dealer_filter_field": "author",
  "rule": "ყველა query ჯერ უნდა გაფილტროს current dealer-ის მიხედვით"
}
```

## Adding New Intents

### Example: Add "cars_by_state" Intent

1. **Add to query_map.json:**

```json
{
  "intent": "cars_by_state",
  "user_examples": [
    "რამდენი მანქანა მაქვს ფლორიდაში?",
    "სახელმწიფოების მიხედვით დამითვალე"
  ],
  "required_fields": ["author", "state"],
  "json_logic": "groupBy(records.filter(r => r.author == CURRENT_DEALER), 'state')",
  "sql_template": "SELECT state, COUNT(*) AS count FROM records WHERE author = :current_dealer GROUP BY state;",
  "response": "დააბრუნე მანქანების რაოდენობა სახელმწიფოების მიხედვით"
}
```

2. **Add field context if needed (in fields_context.json):**

```json
{
  "id": 35,
  "field_name": "state",
  "label": "State",
  "category": "location",
  "data_type": "string|null",
  "business_description": "აშშ-ის შტატი სადაც მდებარეობს მანქანა",
  "synonyms": ["შტატი", "state", "ამერიკის შტატი"],
  "example_user_questions": [
    "რამდენი მანქანა მაქვს ფლორიდაში?",
    "სახელმწიფოების მიხედვით დამითვალე"
  ],
  "agent_usage": "გამოიყენე სახელმწიფოს მიხედვით ფილტრაციის/დაჯგუფებისთვის",
  "response_rule": "დააბრუნე მოკლე, ბიზნესისთვის გასაგები მნიშვნელობა",
  "nullable_handling": "თუ მნიშვნელობა ცარიელია/null — არ გამოიგონო"
}
```

3. **Add execution logic in main.py:**

```python
elif intent == "cars_by_state":
    states = {}
    for record in records:
        state = record.get("state", "Unknown")
        if state not in states:
            states[state] = []
        states[state].append({
            "vin": record.get("vin"),
            "manufacturer": record.get("manufacturer"),
            "model": record.get("model")
        })
    return {"by_state": states, "total": len(records)}
```

## Context Engineering for Different Domains

### E-commerce

```json
{
  "field_name": "product_category",
  "synonyms": ["კატეგორია", "category", "ტიპი", "type"],
  "example_user_questions": [
    "რამდენი პროდუქტი მაქვს ელექტრონიკაში?",
    "კატეგორიების მიხედვით დამითვალე"
  ]
}
```

### Healthcare

```json
{
  "field_name": "patient_status",
  "synonyms": ["სტატუსი", "status", "მდგომარეობა"],
  "example_user_questions": [
    "რამდენი პაციენტი გამოჯანმრთელდა?",
    "სტატუსების მიხედვით დამითვალე"
  ]
}
```

### Real Estate

```json
{
  "field_name": "property_type",
  "synonyms": ["ტიპი", "type", "უძრავი ქონება"],
  "example_user_questions": [
    "რამდენი ბინა მაქვს?",
    "ტიპების მიხედვით დამითვალე"
  ]
}
```

## Testing Your Context Engineering

### 1. Test Intent Detection

```bash
curl "http://localhost:8000/context-guidance?query=რამდენი%20მანქანა%20მაქვს%20საწყობში"
```

Check if the correct intent is detected.

### 2. Test Field Extraction

Verify that relevant fields are identified:

```json
{
  "detected_intent": "cars_by_location_or_stage",
  "detected_fields": ["warehouse", "author"],
  "confidence": 0.95
}
```

### 3. Test Response Quality

Send a query and verify:
- Intent is correct
- Fields are relevant
- Response is in Georgian
- Data is accurate

### 4. Test Edge Cases

- Missing fields
- Null values
- Invalid dates
- Non-existent VINs

## Common Mistakes to Avoid

### ❌ Incomplete Synonyms

```json
"synonyms": ["dealer"]  // Missing Georgian variations
```

### ✅ Comprehensive Synonyms

```json
"synonyms": ["დილერი", "Dealer", "author", "ჩემი დილერი", "dealer name", "ავტორი"]
```

---

### ❌ Vague Business Descriptions

```json
"business_description": "A field"
```

### ✅ Clear Business Descriptions

```json
"business_description": "დილერის დასახელება",
"source_description": "დილერის სახელი და გვარი ან კომპანიის სახელი"
```

---

### ❌ No Security Filtering

```json
"json_logic": "records.filter(r => r.status == 'active')"
```

### ✅ With Security Filtering

```json
"json_logic": "records.filter(r => r.author == CURRENT_DEALER && r.status == 'active')"
```

---

### ❌ No Error Handling

```json
"nullable_handling": "Return the value"
```

### ✅ With Error Handling

```json
"nullable_handling": "თუ მნიშვნელობა ცარიელია/null — არ გამოიგონო; უთხარი, რომ მონაცემი არ არის შევსებული."
```

## Monitoring Context Engineering Effectiveness

### Metrics to Track

1. **Intent Detection Accuracy**: % of queries with correct intent
2. **Field Extraction Accuracy**: % of queries with relevant fields
3. **Response Quality**: User satisfaction with responses
4. **Cache Hit Rate**: % of queries served from cache
5. **Error Rate**: % of queries that fail

### Improvement Loop

1. Monitor metrics
2. Identify low-performing intents
3. Review and improve context definitions
4. Test with new examples
5. Deploy and measure improvement

## Conclusion

Context Engineering is powerful because it:

✅ Makes AI behavior predictable and consistent  
✅ Ensures domain-specific accuracy  
✅ Enforces security and business rules  
✅ Reduces hallucination and errors  
✅ Makes the system maintainable and extensible  
✅ Provides clear documentation  
✅ Enables non-technical users to modify behavior  

By investing in good context engineering, you create an AI system that truly understands your business.
