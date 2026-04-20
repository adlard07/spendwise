# DynamoDB Architecture - Expense Tracking App

## Design Philosophy
- Single-table design pattern for cost efficiency and performance
- GSIs for access patterns not covered by main table
- Optimized for write-heavy workloads (expense capture)
- Sub-50ms read latency for transaction lists

---

## Main Table: `ExpenseTracker`

### Primary Key Structure
- **PK (Partition Key)**: `USER#{user_id}`
- **SK (Sort Key)**: Composite pattern based on entity type

### Entity Patterns

#### 1. User Profile
```
PK: USER#123
SK: PROFILE#123
Attributes:
  - user_id
  - email
  - created_at
  - settings (MAP):
      - default_currency
      - default_account
      - categories[] (list)
      - accounts[] (list)
  - updated_at
```

#### 2. Transaction
```
PK: USER#123
SK: TXN#{timestamp_ms}#{txn_id}
Attributes:
  - txn_id (UUID)
  - amount (Number)
  - currency (default: INR)
  - timestamp (ISO 8601)
  - merchant_raw (original input)
  - merchant_id (FK to normalized merchant)
  - category_id
  - account_id (Cash/UPI/Card)
  - notes
  - attachments[] (S3 URLs)
  - source (manual/import/api)
  - is_duplicate (boolean)
  - duplicate_of (txn_id if merged)
  - created_at
  - updated_at
  - GSI1PK: USER#123#MERCHANT#{merchant_id}
  - GSI1SK: TXN#{timestamp_ms}
  - GSI2PK: USER#123#CATEGORY#{category_id}
  - GSI2SK: TXN#{timestamp_ms}
```

#### 3. Merchant (Normalized)
```
PK: USER#123
SK: MERCHANT#{merchant_id}
Attributes:
  - merchant_id (UUID)
  - canonical_name
  - aliases[] (list of raw merchant names)
  - last_category_used
  - typical_amounts[] (for suggestions)
  - transaction_count
  - created_at
  - updated_at
```

#### 4. Category
```
PK: USER#123
SK: CATEGORY#{category_id}
Attributes:
  - category_id (UUID)
  - name
  - color (for UI)
  - icon
  - is_system (boolean)
  - created_at
```

#### 5. Account/Wallet
```
PK: USER#123
SK: ACCOUNT#{account_id}
Attributes:
  - account_id (UUID)
  - name (Cash, UPI, HDFC Credit)
  - type (cash/upi/credit/debit)
  - last_four (for cards)
  - is_active
  - created_at
```

#### 6. Monthly Aggregates (Pre-computed)
```
PK: USER#123
SK: STATS#{YYYY-MM}
Attributes:
  - month (YYYY-MM)
  - total_spend
  - transaction_count
  - category_breakdown (MAP):
      - {category_id}: {amount, count}
  - account_breakdown (MAP)
  - top_merchants[]
  - daily_totals[] (array of 31 values)
  - computed_at
```

---

## Global Secondary Indexes

### GSI1: Merchant-Based Queries
```
GSI1PK: USER#123#MERCHANT#{merchant_id}
GSI1SK: TXN#{timestamp_ms}
Projection: ALL
```
**Access Pattern**: "Show all Amazon purchases in last 90 days"

### GSI2: Category-Based Queries
```
GSI2PK: USER#123#CATEGORY#{category_id}
GSI2SK: TXN#{timestamp_ms}
Projection: ALL
```
**Access Pattern**: "Show all Food expenses this month"

---

## Access Patterns & Query Examples

### 1. Quick Add Expense
```javascript
{
  PK: "USER#123",
  SK: `TXN#${Date.now()}#${uuid}`,
  amount: 180,
  merchant_raw: "coffee",
  // ... other attributes
}
```

### 2. Transaction Feed (Recent First)
```javascript
{
  KeyConditionExpression: "PK = :pk AND begins_with(SK, :sk)",
  ExpressionAttributeValues: {
    ":pk": "USER#123",
    ":sk": "TXN#"
  },
  ScanIndexForward: false,
  Limit: 50
}
```

### 3. Search by Merchant
```javascript
{
  IndexName: "GSI1",
  KeyConditionExpression: "GSI1PK = :pk",
  FilterExpression: "timestamp BETWEEN :start AND :end"
}
```

### 4. Monthly Insights (Pre-computed)
```javascript
{
  Key: {
    PK: "USER#123",
    SK: "STATS#2025-03"
  }
}
```

---

## Table Configuration

### Capacity Settings (MVP)
```
Mode: On-Demand
Estimated Cost: $5-15/month for 10K transactions

Alternative:
- RCU: 5, WCU: 5
- Auto-scaling enabled
```

### DynamoDB Streams
```yaml
StreamEnabled: true
StreamViewType: NEW_AND_OLD_IMAGES
Purpose: Update aggregates, merchant stats
```

---

## Performance Targets

```yaml
Write (PutItem): < 10ms (p99)
Read (GetItem): < 5ms (p99)
Query (50 items): < 20ms (p99)
Transaction Feed: < 100ms (p99)
```