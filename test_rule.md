


vin:
- Unique vehicle identification number.
- Main lookup field.
- Always 17 characters.
- Used when user asks about exact vehicle.

manufacturer:
- Vehicle brand/manufacturer.
- Example: TOYOTA, BMW, KIA.

model:
- Vehicle model.
- Example: Camry, X5, Sorento.

year:
- Vehicle production year.

record_status:
- Vehicle scope/status in dataset.
- current = active vehicle, not yet completed/handed over.
- archive = completed/archived vehicle.

auction_title:
- Auction name where vehicle was bought.

date:
- Purchase date / sale date.

buyer_id:
- Dealer purchase code.

f1:
- total_pay / total amount to pay.

f2:
- balance.
- If f2 >= 0 → paid / covered.
- If f2 < 0 → dealer owes money.