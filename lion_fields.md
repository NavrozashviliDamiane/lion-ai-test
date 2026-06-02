# FIELD DEFINITIONS

record_status

Description:
Vehicle status category.

Allowed values:
* current
* archive

Meaning:

current = მიმდინარე ავტომობილი

archive = დასრულებული ავტომობილი

---

manufacturer

Description:
Vehicle manufacturer.

Examples:

Toyota
BMW
Mercedes-Benz
Lexus
Ford

Aliases:

მწარმოებელი
მარკა
brand

---

model

Description:
Vehicle model.

Examples:

Camry
Corolla
X5
GLE350

---

year

Description:
Vehicle production year.

---

vin

Description:
Vehicle VIN number.

Rules:

VIN must contain exactly 17 characters.

VIN search requires exact VIN.

---

auction_title

Description:
Auction name.

Examples:

Copart
IAAI
Manheim

Aliases:

აუქციონი

---

date

Description:
Vehicle purchase date.

Aliases:

purchase date
sale date

---

warehouse

Description:
Current warehouse location.

---

point_of_delivery

Description:
Port or destination location.

---

container_entry_date

Description:
Vehicle arrived at port.

---

date_open_container

Description:
Container opening date.

---

title_received

Description:
Title/document received date.

---

photo

Description:
Vehicle photo availability.

Values:

0 = no photos

1 = photos available

---

base_id

Description:
Unique vehicle identifier.

Used for gallery links.

---

author

Description:
Dealer identifier.

Used internally.

Never expose to user.

---

share_item

Description:
Main dealer information.

Used internally.

---

green_date

Description:
Date when dealer received vehicle from company.

Used only for archive vehicles.

---

active_date

Description:
Dynamic status date.

For current vehicles:

warehouse date
or port arrival date
or container opening date

depending on current status.
