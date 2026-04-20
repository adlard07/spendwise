## MVP Scope Principles

* **Capture first** (fast input, low friction)
* **Truth > magic** (clean data model, clear edits, minimal “AI” until you have enough data)
* **One import + one export** (so users can trust & move data)

---

## Must-have MVP Features

### 1) Expense Capture (Core)

* **Quick add**: one input box for `coffee 180 9pm` / “₹1200 rent on 5th”
* **Parser that extracts**: amount, date/time (default = now), merchant/title, notes
* **Manual edit screen** after parse (users must be able to correct fields)
* **Basic categories** (editable list) + assign category per transaction
* **Accounts/wallets** (Cash, UPI, Card) as a simple dropdown

**Acceptance:** user can add an expense in <10 seconds, and fix parser mistakes.

---

### 2) Transaction List + Search

* **Transaction feed** (most recent first)
* **Filters**: date range, category, account
* **Search**: by merchant/title/notes
* **Delete / edit transaction**

**Acceptance:** user can find “Uber” spends in the last 30 days in 2 taps.

---

### 3) Autocomplete (Light “Memory”)

* **Merchant suggestions** from previous merchants
* **Category suggestion** based on last used for that merchant (rule-of-thumb, not ML)
* **Recent amounts** suggestion optional (like “you usually spend ₹220 here”)

**Acceptance:** repeat entries become faster over time without complex modeling.

---

### 4) Merchant Normalization (Minimal Version)

* **User-side “merge merchants”**: select “AMZN”, “Amazon Pay” → merge into “Amazon”
* Store a **merchant_alias → canonical_merchant** mapping

**Acceptance:** analytics don’t split the same merchant into 10 names.

---

### 5) Duplicate Detection (Simple but Valuable)

* Detect probable duplicate if:

  * same merchant (or same normalized merchant)
  * same amount
  * within a time window (e.g., ±2 hours)
* Show prompt: **Keep both / Merge / Discard**

**Acceptance:** prevents accidental double-entry.

---

### 6) Receipts (MVP Lite)

* Allow **attach receipt image/PDF** to a transaction
* Store and display attachment
* (Optional in MVP) Basic extraction: **total + date** only if easy; otherwise skip extraction now

**Acceptance:** user can keep proof without depending on OCR accuracy.

---

### 7) Basic Insights (Non-negotiable)

* **Monthly summary**: total spend, top categories
* **Category breakdown** (pie or list)
* **Spending trend** (daily/weekly total line chart)

**Acceptance:** user instantly sees “where money went” without forecasting.

---

### 8) Data Portability & Trust

* **Export CSV** (date, amount, merchant, category, account, notes)
* **Local backups** (or cloud sync if you already have auth)
* **Audit-friendly fields**: created_at, updated_at, source (manual/import)

**Acceptance:** user feels safe adopting the app.

---

## Explicitly NOT in MVP (but next)

These are high-value, but depend on more data and more edge cases:

* Splitwise sync
* Smart reconciliation between imports + manual entries
* Rules engine UI (“if merchant contains…”)
* Forecasting / cashflow calendar / “safe-to-spend”
* Cohort comparisons
* Seasonality/event-aware prediction
* RAG “cite from your own data” assistant

---

## MVP Deliverable Checklist (1-screen view)

**Screens**

1. Add Expense (quick input + edit form)
2. Transactions (list + search + filters)
3. Insights (monthly overview + category breakdown)
4. Settings (categories, accounts, merchant merge, export)

**Backend/Schema must**

* Transaction schema v1 (amount, currency, timestamp, merchant_raw, merchant_id, category_id, account_id, notes, attachments[], source)
* Merchant table + alias mapping
* Category table
* Basic dedupe detector
