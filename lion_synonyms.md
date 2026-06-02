# SYNONYMS AND NORMALIZATION RULES

---

## VEHICLE

მანქანა

Aliases:

ავტომობილი
ავტო
მანქანები
ავტომობილები
ავტოები

Normalized value:

vehicle

---

## CURRENT

მიმდინარე

Aliases:

აქტიური
გზაში
პროცესში
მიმდინარეები

Normalized value:

current

---

## ARCHIVE

არქივი

Aliases:

დასრულებული
ჩამოსული
დახურული
არქივში
მიღებული

Normalized value:

archive

---

## BALANCE

ბალანსი

Aliases:

balance
balansi
ვალი
დავალიანება
გადასახდელი
ვალები

Normalized value:

balance

---

## TOTAL PAY

ჯამური ღირებულება

Aliases:

total
total pay
სრული ღირებულება
სრული თანხა
სულ ღირებულება

Normalized value:

total_pay

---

## DEBT

დავალიანება

Aliases:

ვალი
ვალები
გადასახდელი
უარყოფითი ბალანსი

Normalized value:

debt

---

## PAYMENT

გადახდა

Aliases:

გადახდილი
ჩარიცხვა
ტრანში
payment
paid

Normalized value:

payment

---

## FINANCE

ფინანსები

Aliases:

ფინანსური ინფორმაცია
ხარჯები
გადასახადები
დეტალური ფინანსები
ფინანსური დეტალები
costs
finance

Normalized value:

finance

---

## PHOTO

ფოტო

Aliases:

ფოტოები
სურათი
სურათები
gallery
photos
images

Normalized value:

photo

---

## VIN

VIN

Aliases:

ვინ
vin code
vehicle vin

Normalized value:

vin

---

## TOYOTA

Aliases:

Toyota
toyota
ტოიოტა
ტაიოტა

Normalized value:

TOYOTA

---

## LEXUS

Aliases:

Lexus
lexus
ლექსუსი

Normalized value:

LEXUS

---

## BMW

Aliases:

BMW
bmw
ბეემვე
ბმვ

Normalized value:

BMW

---

## MERCEDES-BENZ

Aliases:

Mercedes
Mercedes-Benz
mercedes
benz
მერსედესი

Normalized value:

MERCEDES-BENZ

---

## FORD

Aliases:

Ford
ford
ფორდი

Normalized value:

FORD

---

## COPART

Aliases:

Copart
copart
კოპარტი

Normalized value:

COPART

---

## IAAI

Aliases:

IAAI
iaai
აიაი

Normalized value:

IAAI

---

## COUNT REQUEST

Aliases:

რამდენი
რაოდენობა
ჯამში რამდენია
სულ რამდენია

Normalized value:

count

---

## LIST REQUEST

Aliases:

მაჩვენე
მომეცი
ჩამომითვალე
სია
ჩამონათვალი

Normalized value:

list

---

## SUMMARY REQUEST

Aliases:

შეჯამება
სტატისტიკა
რეზიუმე
ჯამური ინფორმაცია

Normalized value:

summary

---

## NEGATIVE BALANCE

Aliases:

უარყოფითი ბალანსი
დავალიანება
ვალი
გადასახდელი

Normalized value:

balance_negative

---

## POSITIVE BALANCE

Aliases:

დაფარული
გადახდილი
ნულოვანი დავალიანება
დადებითი ბალანსი

Normalized value:

balance_positive

---

IMPORTANT RULE

Before intent detection:

Normalize all aliases to their normalized values.

Then perform:

Intent Detection
→ Filter Detection
→ Scope Detection
→ VIN Detection
→ JSON Output
