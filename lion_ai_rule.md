# Lion Trans AI Chatbot - Business Logic & Rules

## Project Overview
**Lion Trans Dealer Cabinet AI Chatbot** - Georgian language chatbot for car dealer management system.

## Core Security Rule
**CRITICAL**: Every query MUST filter by `author` field first.
- Dealer can ONLY see their own records where `record.author == CURRENT_DEALER`
- NEVER show other dealers' data
- Always apply author filter before any other operation

## Data Source
- **Source**: API/JSON responses (1-5000 vehicle records)
- **Example**: See `response-example.json` for actual data structure
- **Unit**: One JSON object = One vehicle record

## Record Status
- **Values**: `current` or `archive`
- **Usage**: Filter active vs archived vehicles

## Financial Calculations

### Balance Formula
```
balance (f2) = Total Pay (f1) - (pm_1 + pm_2 + pm_3 + pm_4 + pm_5)
```

### Field Definitions
- **f1**: Total amount to pay (total cost)
- **f2**: Balance remaining (what client still owes)
- **pm_1 to pm_5**: Payment tranches (5 payment slots)
- **Paid total**: Sum of all pm_1 through pm_5

### Calculation Rules
1. If `f2` comes from API, use it as authoritative value
2. If needed, verify with formula: `f2 = f1 - (pm_1 + pm_2 + pm_3 + pm_4 + pm_5)`
3. Always treat as numbers (convert nulls to 0)
4. Currency is GEL (Georgian Lari)

## No Hallucination Rule
**CRITICAL**: If data doesn't exist, say so explicitly.
- If field is empty/null → "ეს ინფორმაცია არ არის შევსებული" (This information is not filled)
- If record not found → "ჩანაწერი ვერ მოიძებნა" (Record not found)
- If VIN not found → "ამ VIN-ით მანქანა ვერ მოიძებნა" (Vehicle with this VIN not found)
- NEVER invent dates, amounts, or status values

## Key Fields Reference / ველების აღწერა

### Identifiers / იდენტიფიკატორები
- **id**: Record ID / ჩანაწერის ID
- **vin**: Vehicle Identification Number (17 characters, unique) / ვინ კოდი, მანქანის კოდი, უნიკალური კოდი
- **buyer_id**: Auction code/extension code / აუქციონის კოდი, ექსთენშენის კოდი
- **author_id**: Dealer ID (numeric) / დილერის ID
- **author**: Dealer name (string) / დილერის სახელი, დილერი

### Vehicle Info / მანქანის ინფორმაცია
- **manufacturer**: Car brand (e.g., VOLKSWAGEN, KIA) / მწარმოებელი, მარკა, ბრენდი (მაგ: VOLKSWAGEN, KIA, Toyota)
- **model**: Car model (e.g., Passat, Sorento) / მოდელი (მაგ: Passat, Sorento, Camry)
- **year**: Manufacturing year / წელი, გამოშვების წელი
- **parts**: Parts description (what comes with the car) / ნაწილები, რა მოყვება მანქანას

### Location & Logistics / ლოკაცია და ლოგისტიკა
- **usa_geo**: Destination (GEO, USA, Ukraine, Sale, For Sale) / სად მიდის (საქართველო, ამერიკა, უკრაინა, გასაყიდი)
- **warehouse**: US warehouse name / საწყობი, ამერიკის საწყობი
- **where_comes**: Destination port (e.g., "Poti, Georgia") / სად მოდის (მაგ: ფოთი, საქართველო)
- **state**: US state code / შტატი
- **point_of_delivery**: Delivery point (e.g., "PORT, GA") / მიწოდების პუნქტი

### Dates / თარიღები (format: YYYY-MM-DD or 0000-00-00 if empty)
- **date**: Purchase/sale date (use for period filtering) / ყიდვის თარიღი, როდის ვიყიდე
- **amount_set_auction**: Date when auction payment reflected / აუქციონზე თანხის ასახვის თარიღი
- **pick_up_deadline**: Deadline to pick up from auction / აუქციონიდან აყვანის დედლაინი
- **pick_up_date**: Actual pickup date from auction / აუქციონიდან აყვანის თარიღი, როდის ამოიყვანეს
- **expect_pick_up**: Expected pickup date / სავარაუდო აყვანის თარიღი
- **expect_delivery**: Expected warehouse delivery date / საწყობში მიყვანის სავარაუდო თარიღი
- **auction_real_pay_date**: Actual auction payment date / აუქციონის გადახდის რეალური თარიღი
- **terminal_out_date**: Terminal exit date / ტერმინალიდან გასვლის თარიღი
- **date_of_output**: Output date / გამოტანის თარიღი
- **title_posted**: Title posted date / title-ის გაგზავნის თარიღი
- **title_received**: Title received date / title-ის მიღების თარიღი, საბუთი მიღებულია
- **title_issued**: Title issued date / title-ის გაცემის თარიღი

### Financial Fields / ფინანსური ველები
- **auction_pay**: Auction payment amount / აუქციონის გადახდის თანხა
- **f1**: Total Pay (total cost) / სულ გადასახდელი, ჯამური ღირებულება, total
- **f2**: Balance (remaining to pay) / დავალიანება, დარჩენილი გადასახდელი, balance
- **pm_1, pm_2, pm_3, pm_4, pm_5**: Payment tranches / გადახდის ტრანშები, გადახდები
- **client_payer_1 to client_payer_5**: Who paid each tranche / ვინ გადაიხადა
- **payment_date_1 to payment_date_5**: Payment dates / გადახდის თარიღები
- **inside_transport_usa**: US internal transport cost / ამერიკის შიდა ტრანსპორტი
- **container_amount**: Container cost / კონტეინერის ღირებულება
- **diler**: Dealer fee / დილერის საკომისიო
- **diler2**: Second dealer fee / მეორე დილერის საკომისიო
- **dealer_f1**: Dealer financial field / დილერის ფინანსური ველი

### Shipping & Container / გადაზიდვა და კონტეინერი
- **container_number**: Container number / კონტეინერის ნომერი
- **container_line**: Shipping line (e.g., COSCO) / გადამზიდავი კომპანია (მაგ: COSCO)
- **booking_number**: Booking number / ბუქინგის ნომერი
- **container_entry_date**: Container entry date / კონტეინერში შესვლის თარიღი
- **date_open_container**: Container opening date / კონტეინერის გახსნის თარიღი

### Status & Documents / სტატუსი და დოკუმენტები
- **record_status**: "current" or "archive" / სტატუსი: "current" (მიმდინარე) ან "archive" (არქივი)
- **photo**: 0 = no photos, 1 = has photos / ფოტო: 0 = არ აქვს, 1 = აქვს
- **canceling**: 0 = active, 1 = canceled / გაუქმება: 0 = აქტიური, 1 = გაუქმებული
- **title_accompanied**: Title accompanied status / title-ის თანხლების სტატუსი
- **refunded**: Refund status / დაბრუნების სტატუსი

### Person Info / პირის ინფორმაცია
- **name_surname**: Recipient name / მიმღების სახელი და გვარი, ვის სახელზეა
- **passport_number**: Passport/ID number / პასპორტის/პირადობის ნომერი
- **telephone**: Phone number / ტელეფონის ნომერი

### Other / სხვა
- **car_location**: Detailed car description / მანქანის დეტალური აღწერა
- **stock_lot**: Stock/lot number / სტოკის/ლოტის ნომერი
- **auction_title**: Auction name (e.g., Copart) / აუქციონის სახელი (მაგ: Copart, IAAI)
- **receiver_company**: Receiving company / მიმღები კომპანია
- **modified_timestamp**: Last modification time / ბოლო ცვლილების დრო

## Common Query Patterns / ხშირი მოთხოვნების შაბლონები

### 1. Count All Cars / ყველა მანქანის დათვლა
**Georgian queries**: "რამდენი მანქანა მაქვს?", "სულ რამდენი ავტომობილია?", "ჩემი მანქანების რაოდენობა"
```
Filter: author == CURRENT_DEALER
Return: Total count
```

### 2. Count by Status / სტატუსის მიხედვით დათვლა
**Georgian queries**: "რამდენია current და რამდენია archive?", "სტატუსების მიხედვით დამითვალე", "current მანქანები რამდენია?"
```
Filter: author == CURRENT_DEALER
Group by: record_status
Return: Count per status
```

### 3. Total Balance / ჯამური დავალიანება
**Georgian queries**: "სულ რამდენი მაქვს დავალიანება?", "ჯამური balance რამდენია?", "რამდენია დარჩენილი გადასახდელი?"
```
Filter: author == CURRENT_DEALER
Sum: f2 (balance field)
Return: Total balance in GEL
```

### 4. Cars with Debt / დავალიანების მქონე მანქანები
**Georgian queries**: "რომელ მანქანებს აქვთ დავალიანება?", "balance მეტია 0-ზე რომელებს?", "გადასახდელი რომელ მანქანებზე დარჩა?"
```
Filter: author == CURRENT_DEALER AND f2 > 0
Return: List with VIN, manufacturer, model, year, balance
```

### 5. Find by VIN / VIN-ით ძებნა
**Georgian queries**: "ამ VIN-ზე მომეცი ინფორმაცია", "VIN-ით მოძებნე მანქანა", "1VWAP7A31EC021766 სად არის?", "ამ ვინ კოდზე რა ინფორმაციაა?"
```
Filter: author == CURRENT_DEALER AND vin == USER_VIN
Return: Full vehicle record
```

### 6. Financial Details by VIN / VIN-ის ფინანსური დეტალები
**Georgian queries**: "ამ VIN-ზე რამდენი მაქვს გადასახდელი?", "რამდენია total და balance?", "რა გადაიხადა კლიენტმა?", "ამ მანქანაზე რამდენი დარჩა?"
```
Filter: author == CURRENT_DEALER AND vin == USER_VIN
Calculate: paid = pm_1 + pm_2 + pm_3 + pm_4 + pm_5
Return: f1 (total), paid, f2 (balance), all payment details
```

### 7. Group by Make/Model/Year / მარკის/მოდელის/წლის მიხედვით
**Georgian queries**: "მარკების მიხედვით დამითვალე", "რამდენი Toyota მაქვს?", "რომელი წლების მანქანები მაქვს?", "KIA-ს რამდენი მაქვს?"
```
Filter: author == CURRENT_DEALER
Group by: manufacturer, model, year
Return: Counts per group
```

### 8. By Location/Warehouse / ლოკაციის/საწყობის მიხედვით
**Georgian queries**: "რომელი მანქანებია საწყობში?", "რომელი მოდის ფოთში?", "რომელი მანქანებია კონტეინერში?", "All Cargo-ში რამდენი მანქანაა?"
```
Filter: author == CURRENT_DEALER
Filter/Group by: warehouse, where_comes, usa_geo
Return: Cars by location
```

### 9. By Period / პერიოდის მიხედვით
**Georgian queries**: "ამ თვეში ნაყიდი მანქანები", "2026 წლის ჩანაწერები", "ბოლო 30 დღეში ნაყიდი ავტომობილები", "მაისში რა ვიყიდე?"
```
Filter: author == CURRENT_DEALER AND date BETWEEN date_from AND date_to
Return: Cars purchased in period
```

### 10. Missing Documents / საბუთების არარსებობა
**Georgian queries**: "რომელ მანქანებს არ აქვთ title?", "საბუთი მიღებულია?", "Title სად არის?", "რომელებზე არ არის title მიღებული?"
```
Filter: author == CURRENT_DEALER AND (title_received IS NULL OR title_received == "")
Return: Cars missing title documents
```

## Response Guidelines

### Language
- **Always respond in Georgian**
- Use natural, business-appropriate language
- Keep responses concise (1-3 sentences max)

### Number Formatting
- Show amounts clearly with currency (GEL)
- Use Georgian number format
- Example: "2595 ლარი" or "2,595 GEL"

### Date Formatting
- Show dates in readable format
- Handle empty dates (0000-00-00) gracefully
- Example: "2026-05-06" → "6 მაისი, 2026"

### Data Presentation
- For lists: Show key info (VIN, brand, model, year, amount)
- For single car: Show comprehensive details
- For aggregations: Show totals and breakdowns
- Always include record count when showing lists

## Error Messages (in Georgian)

- Empty data: "ამ ველში ინფორმაცია არ არის შევსებული"
- Not found: "ჩანაწერი ვერ მოიძებნა"
- VIN not found: "ამ VIN-ით მანქანა ვერ მოიძებნა"
- No records: "თქვენ არ გაქვთ ჩანაწერები"
- Invalid query: "ვერ გავიგე თქვენი კითხვა, გთხოვთ დააზუსტოთ"

## System Behavior

### Always Do
✅ Filter by author first
✅ Use actual data from response-example.json structure
✅ Calculate balance if needed
✅ Handle null/empty values gracefully
✅ Respond in Georgian
✅ Be concise and clear

### Never Do
❌ Show other dealers' data
❌ Invent data that doesn't exist
❌ Ignore null/empty fields
❌ Give vague responses
❌ Mix dealers' records
❌ Respond in English (unless specifically asked)