# CONVERSATION MEMORY RULES

Purpose:

Maintain conversational context between user messages.

The assistant must understand follow-up questions without requiring the user to repeat previous filters.

---

## CONTEXT STORAGE

The backend may provide previous context.

Context may contain:

{
"scope": "current",
"filters": {
"manufacturer": "TOYOTA"
},
"last_intent": "list_vehicles",
"last_vin": null,
"last_result_vins": [],
"last_selected_vin": null
}

---

## GENERAL RULE

If the user's new message is incomplete but depends on the previous message, merge it with existing context.

Do not discard valid previous filters unless the user explicitly changes them.

---

## FILTER EXTENSION

Example:

User:

მაჩვენე მიმდინარე მანქანები

Context:

{
"scope":"current"
}

User:

მხოლოდ Toyota

Result:

{
"scope":"current",
"manufacturer":"TOYOTA"
}

---

## FILTER REPLACEMENT

Example:

Current Context:

{
"manufacturer":"TOYOTA"
}

User:

არა BMW

Replace manufacturer.

Result:

{
"manufacturer":"BMW"
}

---

## DEBT FILTER CHAIN

Example:

User:

მაჩვენე მიმდინარე მანქანები

↓

User:

მხოლოდ Toyota

↓

User:

მხოლოდ დავალიანებები

Result:

{
"scope":"current",
"manufacturer":"TOYOTA",
"balance":"negative"
}

---

## ARCHIVE SWITCH

Example:

Current Context:

{
"scope":"current"
}

User:

მაჩვენე არქივში

Replace scope.

Result:

{
"scope":"archive"
}

---

## VIN MEMORY

If user selected a VIN previously:

Store:

{
"last_selected_vin":"4T1BF1FK0GU123456"
}

---

## VIN FOLLOW-UP

Example:

User:

4T1BF1FK0GU123456

↓

User:

ფინანსები

Interpret:

Financial details for previously selected VIN.

---

## PHOTO FOLLOW-UP

Example:

User:

4T1BF1FK0GU123456

↓

User:

ფოტოები

Interpret:

Photos for previously selected VIN.

---

## STATUS FOLLOW-UP

Example:

User:

4T1BF1FK0GU123456

↓

User:

სტატუსი

Interpret:

Current status for previously selected VIN.

---

## DETAILS FOLLOW-UP

Example:

User:

4T1BF1FK0GU123456

↓

User:

დეტალურად

Interpret:

Full vehicle details for previously selected VIN.

---

## FIRST VEHICLE REFERENCE

Store result VIN list.

Example:

{
"last_result_vins":[
"VIN1",
"VIN2",
"VIN3"
]
}

---

## FIRST VEHICLE

Example:

User:

პირველი

Result:

VIN1

---

## SECOND VEHICLE

Example:

User:

მეორე

Result:

VIN2

---

## THIRD VEHICLE

Example:

User:

მესამე

Result:

VIN3

---

## LAST VEHICLE

Example:

User:

ბოლო

Result:

Last VIN from result list.

---

## FIRST VEHICLE FINANCE

Example:

User:

პირველის ფინანსები

Interpret:

Financial details for VIN1.

---

## SECOND VEHICLE FINANCE

Example:

User:

მეორის ფინანსები

Interpret:

Financial details for VIN2.

---

## RESULT LIMIT MEMORY

Store last shown result list.

Never reference vehicles outside last shown result set.

---

## CLEAR CONTEXT

User may reset context.

Examples:

დაივიწყე

თავიდან დავიწყოთ

ახალი ძებნა

გაასუფთავე

Result:

{
"clear_context": true
}

---

## PRIORITY ORDER

Priority:

1. Explicit VIN
2. Selected VIN
3. Previous result list
4. Previous filters
5. Previous scope

---

## IMPORTANT RULE

Always prefer existing context when the user's message is incomplete.

Never ask the user to repeat information already available in context.

Use conversation memory whenever possible.
