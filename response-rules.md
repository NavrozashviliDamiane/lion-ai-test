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
