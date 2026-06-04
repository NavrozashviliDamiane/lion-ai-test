# SUPPORTED INTENTS

count

Examples:
რამდენი მანქანა მაქვს
რამდენი Toyota მაქვს

---

list_vehicles

Examples:

მაჩვენე მანქანები

მაჩვენე მიმდინარე მანქანები

---

debt_summary

Examples:

რამდენ მანქანაზე მაქვს დავალიანება

მაჩვენე დავალიანებები

---

vin_details

Examples:

4T1BF1FK0GU123456

მაჩვენე ეს VIN

---

vin_finance

Examples:

ფინანსები ამ VIN-ზე

მაჩვენე სრული ფინანსური ინფორმაცია

---

aggregation

Examples:

რამდენია საერთო ბალანსი

რამდენია საერთო გადახდილი თანხა

---

clarification_needed

Used when user intent is unclear.

# VIN RELATED INTENTS

vin_details

Used when user provides only a full VIN.

Purpose:
Return simple vehicle card.

Required:

* vin

Response type:
vehicle_card

---

vin_auction_info

Used when user asks:

* რომელ აუქციონზე შევიძინე ეს VIN
* სად ვიყიდე ეს მანქანა
* აუქციონი ამ VIN-ზე
* შესყიდვის ინფორმაცია VIN-ზე

Required:

* vin

Fields to return:

* auction_title
* date
* auction_pay
* buyer_id

Response type:
auction_info

---

vin_full_info

Used when user clicks or asks:

* სრული ინფორმაცია
* დეტალურად
* სრული დეტალები

Required:

* vin

Response type:
full_vehicle_info

---

vin_status

Used when user clicks or asks:

* სტატუსი
* სად არის მანქანა
* რა ეტაპზეა

Required:

* vin

Response type:
vehicle_status

---

vin_finance

Used when user clicks or asks:

* ფინანსური მდგომარეობა
* ფინანსები
* ხარჯები
* ბალანსი
* გადასახდელი

Required:

* vin

Response type:
financial_details
