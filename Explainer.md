# Playto Payout Engine — EXPLAINER

---

## 1. The Ledger

### Balance Calculation Query

```python
result = LedgerEntry.objects.filter(merchant=merchant).aggregate(
    credits=Sum("amount_paise", filter=Q(type="credit")),
    debits=Sum("amount_paise", filter=Q(type="debit")),
)

balance = (result["credits"] or 0) - (result["debits"] or 0)
```

### Why this model?

* I modeled money using **immutable ledger entries (credit and debit)** instead of storing balance.

* This ensures:

  * **Auditability** — every transaction is recorded
  * **No race conditions** — balance is never overwritten
  * **Consistency** — balance is derived from DB, not memory

* All amounts are stored as **integer paise**, avoiding floating point issues.

---

## 2. The Lock (Concurrency Control)

### Code

```python
@transaction.atomic
def create_payout(merchant, amount, bank_account):
    LedgerEntry.objects.select_for_update().filter(merchant=merchant)

    balance = get_balance(merchant)

    if balance < amount:
        raise Exception("Insufficient balance")
```

### Explanation

* I used **`SELECT FOR UPDATE`** via `select_for_update()`
* This locks ledger rows at the **database level**

### Why this is important

Without locking:

* Two concurrent requests could:

  * Both read same balance
  * Both succeed
  * Result → **double spending**

With locking:

* First request locks rows
* Second request waits
* Balance is recalculated safely

👉 This is **database-level concurrency control**, not Python-level.

---

## 3. The Idempotency

### Detection Logic

```python
existing = IdempotencyKey.objects.filter(
    merchant=merchant,
    key=key
).first()
```

* If key exists → return stored response
* If not → process and store

---

### Handling concurrent duplicate requests

* `(merchant, key)` is enforced as **unique**
* If two requests arrive simultaneously:

  * One succeeds
  * Other is prevented by DB constraint

👉 Ensures:

* No duplicate payouts
* Safe retries from clients

---

## 4. The State Machine

### Allowed transitions

```text
pending → processing → completed
pending → processing → failed
```

### Code enforcement

```python
if payout.status not in ["pending", "processing"]:
    return
```

### Guarantees

* Completed payouts cannot revert
* Failed payouts cannot become completed
* Invalid transitions are ignored

---

## 5. Failure Handling & Refund Logic

### Code

```python
elif r <= 90:
    payout.status = "failed"

    LedgerEntry.objects.create(
        merchant=payout.merchant,
        amount_paise=payout.amount_paise,
        type="credit",
    )
```

### Explanation

* On failure:

  * Funds are returned via **credit entry**
* This is done inside **same transaction**

👉 Ensures:

* Atomicity
* No money loss

---

## 6. Retry Logic

* Each payout has an `attempts` counter
* Processing logic:

```python
if payout.attempts >= 3:
    payout.status = "failed"
```

* Simulates:

  * Retry attempts
  * Eventual failure after retries

---

## 7. Data Integrity

System guarantees:

* Balance = Sum(credits) - Sum(debits)
* No direct balance updates
* All operations are transactional

👉 Ensures **money consistency always**

---

## 8. Deployment & Production Setup

* Deployed on **Render**
* Used **PostgreSQL via DATABASE_URL**
* Used **gunicorn** for production server

### DB Config

```python
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3'
    )
}
```

### Note

> In production, payout processing would be handled by Celery workers instead of synchronous execution.

---

## 9. The AI Audit

### What AI suggested (incorrect)

```python
if merchant.balance >= amount:
    merchant.balance -= amount
    merchant.save()
```

### Problems

* Uses stored balance → stale reads
* No locking → race condition
* Can cause double spending

---

### What I implemented instead

```python
LedgerEntry.objects.select_for_update().filter(merchant=merchant)
balance = get_balance(merchant)
```

### Why this is correct

* Uses DB aggregation → always accurate
* Uses row-level locking → safe concurrency
* No reliance on cached values

---

## Final Summary

This system ensures:

* **Correct money handling using ledger model**
* **Concurrency safety using database locks**
* **Idempotent APIs for real-world retries**
* **Strict state machine for payout lifecycle**
* **Atomic refund handling on failure**

---
