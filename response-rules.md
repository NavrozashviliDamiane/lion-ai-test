# RESPONSE RULES

Count questions:

Return summary only.

Example:

რამდენი Toyota მაქვს

---

Debt questions:

Return:

* vehicle count
* total debt
* VIN list

Do not return cards.

---

VIN details:

Return vehicle card.

Card fields:

* sale date
* auction
* VIN
* manufacturer
* model
* year
* total pay
* balance
* active date

---

VIN finance:
Return:

Vehicle card

*

Financial breakdown

---

Photos:

If photo = 1

show photo button.

If photo = 0

hide photo button.

---

Language:

Always Georgian.

JSON keys remain English.


# VIN CARD RESPONSE RULES

If user provides only full VIN:

Return simple vehicle card.

Card fields:

* manufacturer
* model
* year
* date
* auction_title
* total_pay
* balance
* record_status

The card must show status:

current
or
archive

---

# CURRENT STATUS DATE RULES

If record_status = current:

Show current vehicle progress/status based on available dates.

Status date priority should be determined by backend business logic.

Possible status stages:

1. Auction pickup date
2. Warehouse arrival date
3. Container loading date
4. Vessel / ship port arrival date
5. Container opening date
6. Vehicle release date
7. Green date

The backend must choose the latest meaningful status stage.

---

# ARCHIVE STATUS RULES

If record_status = archive:

Show green date.

Meaning:
Green date = date when dealer received vehicle from company.

---

# CARD BUTTON RULES

Every VIN card must include buttons:

1. სრული ინფორმაცია
2. სტატუსი
3. ფინანსური მდგომარეობა

If photo = 1:

Add photo button:

<a target="_blank" href="https://domain.com/carphoto/{base_id}">Photo</a>

If photo = 0:

Do not show photo button.

---

# AUCTION INFO RESPONSE RULES

If user asks:

რომელ აუქციონზე შევიძინე ავტომობილი VIN ნომრით

Return:

* auction_title
* date
* auction_pay
* buyer_id

Do not return full card unless user asks full details.
