# EXAMPLES

USER:

რამდენი Toyota მაქვს?

OUTPUT:

{
"intent":"count",
"filters":{
"manufacturer":"TOYOTA"
},
"response_type":"summary"
}

---

USER:

მაჩვენე მიმდინარე Toyota

OUTPUT:

{
"intent":"list_vehicles",
"scope":"current",
"filters":{
"manufacturer":"TOYOTA"
},
"response_type":"list"
}

---

USER:

რამდენ ავტომობილზე მაქვს დავალიანება

OUTPUT:

{
"intent":"debt_summary",
"filters":{
"balance":"negative"
},
"response_type":"summary"
}

---

USER:

4T1BF1FK0GU123456

OUTPUT:

{
"intent":"vin_details",
"vin":"4T1BF1FK0GU123456",
"response_type":"vehicle_card"
}

---

USER:

მაჩვენე ამ VIN-ის ფინანსები

OUTPUT:

{
"intent":"vin_finance",
"vin":"4T1BF1FK0GU123456",
"response_type":"financial_details"
}

USER:

4T1BF1FK0GU123456

OUTPUT:

{
"intent": "vin_details",
"vin": "4T1BF1FK0GU123456",
"response_type": "vehicle_card"
}

--------------------------------------------------

USER:

რომელ აუქციონზე შევიძინე ავტომობილი 4T1BF1FK0GU123456?

OUTPUT:

{
"intent": "vin_auction_info",
"vin": "4T1BF1FK0GU123456",
"response_type": "auction_info"
}

--------------------------------------------------

USER:

ამ VIN-ის სტატუსი მაინტერესებს

OUTPUT:

{
"intent": "vin_status",
"response_type": "vehicle_status"
}

--------------------------------------------------

USER:

ფინანსური მდგომარეობა მაჩვენე

OUTPUT:

{
"intent": "vin_finance",
"response_type": "financial_details"
}