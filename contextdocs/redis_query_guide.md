# Redis Query Guide for AI

## Redis Architecture

### Cache Structure
```
Key Format: author_records:{author_id}
Value: JSON array of vehicle records
TTL: 3600 seconds (1 hour)
```

### Example Key
```
author_records:1748
```

### Data Structure in Redis
```json
[
  {
    "id": 470225,
    "vin": "1VWAP7A31EC021766",
    "year": "2014",
    "manufacturer": "VOLKSWAGEN",
    "model": "Passat",
    "auction_title": "Copart",
    "buyer_id": "Dealer 1748-381",
    "f1": 2595.0,
    "f2": -2595.0,
    "record_status": "current",
    "date": "2026-05-05",
    "warehouse": "All Cargo",
    "where_comes": "Poti, Georgia",
    // ... 80+ more fields
  },
  // ... more records
]
```

## Query Patterns

### Pattern 1: Count All Records
**Purpose**: Get total number of vehicles
**Logic**: 
```
1. Fetch key: author_records:{author_id}
2. Count array length
3. Return: Total count
```

### Pattern 2: Filter by Field Value
**Purpose**: Find records matching specific criteria
**Logic**:
```
1. Fetch key: author_records:{author_id}
2. Iterate through array
3. Filter where field == value
4. Return: Matching records
```

**Examples**:
- Find by VIN: `vin == "1VWAP7A31EC021766"`
- Find by status: `record_status == "current"`
- Find by manufacturer: `manufacturer == "VOLKSWAGEN"`

### Pattern 3: Filter by Numeric Range
**Purpose**: Find records within numeric range
**Logic**:
```
1. Fetch key: author_records:{author_id}
2. Iterate through array
3. Filter where field >= min AND field <= max
4. Return: Matching records
```

**Examples**:
- Find by year range: `year >= 2010 AND year <= 2020`
- Find by balance: `f2 > 0` (vehicles with debt)
- Find by total pay: `f1 >= 1000`

### Pattern 4: Filter by Date Range
**Purpose**: Find records within date range
**Logic**:
```
1. Fetch key: author_records:{author_id}
2. Iterate through array
3. Filter where date >= start_date AND date <= end_date
4. Return: Matching records
```

**Examples**:
- Find by month: `date >= "2026-05-01" AND date <= "2026-05-31"`
- Find recent: `date >= "2026-05-01"`

### Pattern 5: Group and Count
**Purpose**: Count records by category
**Logic**:
```
1. Fetch key: author_records:{author_id}
2. Group by field (e.g., record_status, manufacturer, year)
3. Count items in each group
4. Return: Grouped counts
```

**Examples**:
- Count by status: Group by `record_status` → {current: 200, archive: 55}
- Count by manufacturer: Group by `manufacturer` → {VOLKSWAGEN: 50, KIA: 45, ...}
- Count by year: Group by `year` → {2014: 30, 2015: 25, ...}

### Pattern 6: Aggregate Numeric Fields
**Purpose**: Sum or average numeric fields
**Logic**:
```
1. Fetch key: author_records:{author_id}
2. Filter records (optional)
3. Sum or average field values
4. Return: Aggregated value
```

**Examples**:
- Total debt: Sum all `f2` values
- Total payments: Sum all `f1` values
- Average balance: Average of `f2` values

### Pattern 7: Sort and Limit
**Purpose**: Get top N records by field
**Logic**:
```
1. Fetch key: author_records:{author_id}
2. Sort by field (ascending or descending)
3. Limit to N records
4. Return: Top N records
```

**Examples**:
- Top 10 highest debt: Sort by `f2` DESC, limit 10
- Most recent: Sort by `date` DESC, limit 5
- Oldest vehicles: Sort by `year` ASC, limit 10

### Pattern 8: Multi-Field Filter
**Purpose**: Complex queries with multiple conditions
**Logic**:
```
1. Fetch key: author_records:{author_id}
2. Apply multiple filters (AND/OR logic)
3. Return: Matching records
```

**Examples**:
- Current VWs with debt: `record_status == "current" AND manufacturer == "VOLKSWAGEN" AND f2 > 0`
- Recent Copart purchases: `auction_title == "Copart" AND date >= "2026-05-01"`
- Vehicles at warehouse: `warehouse == "All Cargo" AND record_status == "current"`

## Field Reference for Queries

### Identifier Fields
- `vin`: String (17 chars), unique vehicle identifier
- `id`: Integer, record ID
- `buyer_id`: String, auction code

### Vehicle Info Fields
- `manufacturer`: String, car brand
- `model`: String, car model
- `year`: String or Integer, manufacturing year
- `record_status`: String, "current" or "archive"

### Financial Fields
- `f1`: Float, total payment amount
- `f2`: Float, balance remaining
- `auction_pay`: Float, auction payment

### Date Fields
- `date`: String (YYYY-MM-DD), purchase date
- `amount_set_auction`: String, auction date
- `expect_delivery`: String, expected delivery date

### Location Fields
- `warehouse`: String, US warehouse name
- `where_comes`: String, destination port
- `usa_geo`: String, destination region

## Query Examples

### Example 1: VIN Lookup
```
Query: User asks about VIN "1VWAP7A31EC021766"
Logic:
  1. Fetch author_records:1748
  2. Find record where vin == "1VWAP7A31EC021766"
  3. Return: Complete record with all fields
Response: "2014, Copart, Dealer 1748-381"
```

### Example 2: Count Current Vehicles
```
Query: User asks "რამდენი მიმდინარე მანქანა მაქვს?"
Logic:
  1. Fetch author_records:1748
  2. Count records where record_status == "current"
  3. Return: Count
Response: "თქვენ გაქვთ 200 მიმდინარე მანქანა"
```

### Example 3: Total Debt
```
Query: User asks "სულ რამდენი დავალიანება მაქვს?"
Logic:
  1. Fetch author_records:1748
  2. Sum all f2 values
  3. Return: Total
Response: "თქვენი ჯამური დავალიანება 50000 GEL"
```

### Example 4: Vehicles with Debt
```
Query: User asks "რომელ მანქანებს აქვთ დავალიანება?"
Logic:
  1. Fetch author_records:1748
  2. Filter where f2 > 0
  3. Return: List of records
Response: List with VIN, manufacturer, model, balance
```

### Example 5: Recent Purchases
```
Query: User asks "მაისში რა ვიყიდე?"
Logic:
  1. Fetch author_records:1748
  2. Filter where date >= "2026-05-01" AND date <= "2026-05-31"
  3. Return: Matching records
Response: List of vehicles purchased in May
```

## Important Rules

### Always Remember
- ✅ Always fetch from: `author_records:{author_id}`
- ✅ Data is a JSON array of objects
- ✅ Each object has 80+ fields
- ✅ Use field names exactly as they appear
- ✅ Handle null/empty values gracefully

### Never Do
- ❌ Create new Redis keys
- ❌ Write to Redis
- ❌ Access other author's data
- ❌ Assume field existence
- ❌ Invent data that doesn't exist

### Response Format
- Always respond in Georgian
- Include relevant field values
- Format numbers with currency (GEL)
- Keep responses concise (1-3 sentences)
- Provide context when needed

## Query Execution Responsibility

**Important**: The AI describes the query logic, but the Python backend executes it.

The AI should:
1. Understand the query pattern needed
2. Describe what data to fetch and filter
3. Specify the logic to apply
4. Request the backend to execute

The Python backend:
1. Receives query description from AI
2. Executes Redis operations
3. Returns results to AI
4. AI formats response for user
