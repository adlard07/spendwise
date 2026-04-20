# PostgreSQL Architecture - Expense Tracking App

## Design Philosophy
- Normalized relational design with strategic denormalization
- ACID compliance for financial data integrity
- Optimized indexes for common query patterns
- Scalable to millions of transactions

---

## Schema Design

### 1. Users Table
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    default_currency VARCHAR(3) DEFAULT 'INR',
    default_account_id UUID,
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
```

---

### 2. Categories Table
```sql
CREATE TABLE categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7), -- Hex color code
    icon VARCHAR(50),
    is_system BOOLEAN DEFAULT FALSE, -- Pre-defined vs user-created
    display_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, name)
);

CREATE INDEX idx_categories_user ON categories(user_id);

-- Seed default categories
INSERT INTO categories (user_id, name, color, icon, is_system) VALUES
    (:user_id, 'Food & Dining', '#FF6B6B', 'utensils', TRUE),
    (:user_id, 'Transportation', '#4ECDC4', 'car', TRUE),
    (:user_id, 'Shopping', '#95E1D3', 'shopping-bag', TRUE),
    (:user_id, 'Bills & Utilities', '#F38181', 'file-text', TRUE),
    (:user_id, 'Entertainment', '#AA96DA', 'film', TRUE),
    (:user_id, 'Healthcare', '#FCBAD3', 'heart', TRUE),
    (:user_id, 'Other', '#FFFFD2', 'more-horizontal', TRUE);
```

---

### 3. Accounts Table
```sql
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- "HDFC Credit", "Cash", "Paytm"
    type VARCHAR(20) NOT NULL CHECK (type IN ('cash', 'upi', 'credit', 'debit', 'wallet')),
    last_four VARCHAR(4), -- Last 4 digits for cards
    provider VARCHAR(50), -- Bank/provider name
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, name)
);

CREATE INDEX idx_accounts_user ON accounts(user_id);
CREATE INDEX idx_accounts_active ON accounts(user_id, is_active);
```

---

### 4. Merchants Table
```sql
CREATE TABLE merchants (
    merchant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    canonical_name VARCHAR(255) NOT NULL, -- Normalized name
    last_category_id UUID REFERENCES categories(category_id),
    transaction_count INTEGER DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, canonical_name)
);

CREATE INDEX idx_merchants_user ON merchants(user_id);
CREATE INDEX idx_merchants_name ON merchants(user_id, canonical_name);
```

---

### 5. Merchant Aliases Table
```sql
CREATE TABLE merchant_aliases (
    alias_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    alias_name VARCHAR(255) NOT NULL, -- Raw input variant
    match_count INTEGER DEFAULT 0, -- How often this alias was used
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(merchant_id, alias_name)
);

CREATE INDEX idx_merchant_aliases_name ON merchant_aliases(alias_name);
CREATE INDEX idx_merchant_aliases_merchant ON merchant_aliases(merchant_id);
```

---

### 6. Transactions Table (Core)
```sql
CREATE TABLE transactions (
    txn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Financial details
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Categorization
    merchant_raw VARCHAR(255), -- Original user input
    merchant_id UUID REFERENCES merchants(merchant_id),
    category_id UUID REFERENCES categories(category_id),
    account_id UUID REFERENCES accounts(account_id),
    
    -- Temporal
    transaction_date DATE NOT NULL,
    transaction_time TIME,
    transaction_timestamp TIMESTAMPTZ NOT NULL,
    
    -- Metadata
    notes TEXT,
    source VARCHAR(20) DEFAULT 'manual' CHECK (source IN ('manual', 'import', 'api', 'sms')),
    
    -- Duplicate handling
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of UUID REFERENCES transactions(txn_id),
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CHECK (NOT (is_duplicate = TRUE AND duplicate_of IS NULL))
);

-- Performance-critical indexes
CREATE INDEX idx_txn_user_date ON transactions(user_id, transaction_date DESC);
CREATE INDEX idx_txn_user_timestamp ON transactions(user_id, transaction_timestamp DESC);
CREATE INDEX idx_txn_merchant ON transactions(merchant_id, transaction_timestamp DESC);
CREATE INDEX idx_txn_category ON transactions(user_id, category_id, transaction_date DESC);
CREATE INDEX idx_txn_account ON transactions(account_id, transaction_date DESC);
CREATE INDEX idx_txn_user_amount ON transactions(user_id, amount DESC); -- For top spends

-- Duplicate detection index
CREATE INDEX idx_txn_duplicate_check ON transactions(
    user_id, 
    merchant_id, 
    amount, 
    transaction_timestamp
) WHERE is_duplicate = FALSE;

-- Full-text search on merchant + notes
CREATE INDEX idx_txn_search ON transactions USING GIN(
    to_tsvector('english', COALESCE(merchant_raw, '') || ' ' || COALESCE(notes, ''))
);
```

---

### 7. Transaction Attachments Table
```sql
CREATE TABLE transaction_attachments (
    attachment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    txn_id UUID NOT NULL REFERENCES transactions(txn_id) ON DELETE CASCADE,
    file_url TEXT NOT NULL, -- S3/Cloud storage URL
    file_type VARCHAR(50), -- image/jpeg, application/pdf
    file_size_kb INTEGER,
    extracted_total DECIMAL(15, 2), -- OCR extracted amount
    extracted_date DATE, -- OCR extracted date
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_attachments_txn ON transaction_attachments(txn_id);
```

---

### 8. Monthly Aggregates Table (Materialized View)
```sql
CREATE TABLE monthly_stats (
    stats_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    month DATE NOT NULL, -- First day of month (YYYY-MM-01)
    
    -- Summary metrics
    total_transactions INTEGER DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    avg_transaction DECIMAL(15, 2) DEFAULT 0,
    
    -- Top performers
    top_category_id UUID REFERENCES categories(category_id),
    top_category_amount DECIMAL(15, 2),
    top_merchant_id UUID REFERENCES merchants(merchant_id),
    top_merchant_amount DECIMAL(15, 2),
    
    -- Computed timestamp
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, month)
);

CREATE INDEX idx_monthly_stats_user ON monthly_stats(user_id, month DESC);
```

---

### 9. Category Breakdowns Table (Denormalized for Speed)
```sql
CREATE TABLE category_breakdowns (
    breakdown_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(category_id),
    month DATE NOT NULL,
    
    transaction_count INTEGER DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    avg_amount DECIMAL(15, 2) DEFAULT 0,
    
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, category_id, month)
);

CREATE INDEX idx_category_breakdown ON category_breakdowns(user_id, month DESC);
```

---

## Triggers & Functions

### 1. Auto-update Timestamps
```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_merchants_timestamp
    BEFORE UPDATE ON merchants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_transactions_timestamp
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

### 2. Update Merchant Stats on Transaction Insert
```sql
CREATE OR REPLACE FUNCTION update_merchant_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update merchant transaction count and total
    UPDATE merchants
    SET 
        transaction_count = transaction_count + 1,
        total_amount = total_amount + NEW.amount,
        last_category_id = NEW.category_id,
        updated_at = NOW()
    WHERE merchant_id = NEW.merchant_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER txn_update_merchant_stats
    AFTER INSERT ON transactions
    FOR EACH ROW 
    WHEN (NEW.merchant_id IS NOT NULL)
    EXECUTE FUNCTION update_merchant_stats();
```

---

### 3. Merchant Alias Auto-creation
```sql
CREATE OR REPLACE FUNCTION create_merchant_alias()
RETURNS TRIGGER AS $$
BEGIN
    -- If merchant_raw doesn't match canonical_name, create alias
    IF NEW.merchant_raw IS NOT NULL AND NEW.merchant_id IS NOT NULL THEN
        INSERT INTO merchant_aliases (merchant_id, alias_name)
        VALUES (NEW.merchant_id, NEW.merchant_raw)
        ON CONFLICT (merchant_id, alias_name) 
        DO UPDATE SET match_count = merchant_aliases.match_count + 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER txn_create_alias
    AFTER INSERT ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION create_merchant_alias();
```

---

## Key Queries

### 1. Transaction Feed (Recent First)
```sql
SELECT 
    t.txn_id,
    t.amount,
    t.merchant_raw,
    m.canonical_name as merchant,
    c.name as category,
    c.color as category_color,
    a.name as account,
    t.transaction_date,
    t.notes
FROM transactions t
LEFT JOIN merchants m ON t.merchant_id = m.merchant_id
LEFT JOIN categories c ON t.category_id = c.category_id
LEFT JOIN accounts a ON t.account_id = a.account_id
WHERE t.user_id = :user_id
  AND t.is_duplicate = FALSE
ORDER BY t.transaction_timestamp DESC
LIMIT 50;
```

---

### 2. Search Transactions (Full-text)
```sql
SELECT 
    t.*,
    m.canonical_name,
    c.name as category
FROM transactions t
LEFT JOIN merchants m ON t.merchant_id = m.merchant_id
LEFT JOIN categories c ON t.category_id = c.category_id
WHERE t.user_id = :user_id
  AND to_tsvector('english', 
      COALESCE(t.merchant_raw, '') || ' ' || COALESCE(t.notes, '')
      ) @@ plainto_tsquery('english', :search_term)
ORDER BY t.transaction_timestamp DESC;
```

---

### 3. Duplicate Detection
```sql
SELECT 
    t2.txn_id,
    t2.amount,
    t2.merchant_raw,
    t2.transaction_timestamp
FROM transactions t1
JOIN transactions t2 ON (
    t2.user_id = t1.user_id
    AND t2.merchant_id = t1.merchant_id
    AND t2.amount = t1.amount
    AND t2.transaction_timestamp BETWEEN 
        t1.transaction_timestamp - INTERVAL '2 hours' AND
        t1.transaction_timestamp + INTERVAL '2 hours'
    AND t2.txn_id != t1.txn_id
    AND t2.is_duplicate = FALSE
)
WHERE t1.txn_id = :new_txn_id;
```

---

### 4. Monthly Category Breakdown
```sql
SELECT 
    c.name,
    c.color,
    COUNT(*) as txn_count,
    SUM(t.amount) as total_amount,
    AVG(t.amount) as avg_amount,
    ROUND((SUM(t.amount) * 100.0 / total.month_total), 2) as percentage
FROM transactions t
JOIN categories c ON t.category_id = c.category_id
CROSS JOIN (
    SELECT SUM(amount) as month_total
    FROM transactions
    WHERE user_id = :user_id
      AND transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND is_duplicate = FALSE
) total
WHERE t.user_id = :user_id
  AND t.transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND t.is_duplicate = FALSE
GROUP BY c.category_id, c.name, c.color, total.month_total
ORDER BY total_amount DESC;
```

---

### 5. Merchant Autocomplete
```sql
SELECT 
    m.merchant_id,
    m.canonical_name,
    m.last_category_id,
    c.name as suggested_category,
    ROUND(AVG(t.amount), 2) as typical_amount
FROM merchants m
LEFT JOIN categories c ON m.last_category_id = c.category_id
LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
WHERE m.user_id = :user_id
  AND m.canonical_name ILIKE :search || '%'
GROUP BY m.merchant_id, m.canonical_name, m.last_category_id, c.name
ORDER BY m.transaction_count DESC
LIMIT 5;
```

---

### 6. Spending Trend (Daily Totals)
```sql
SELECT 
    transaction_date as date,
    SUM(amount) as total,
    COUNT(*) as txn_count
FROM transactions
WHERE user_id = :user_id
  AND transaction_date >= CURRENT_DATE - INTERVAL '30 days'
  AND is_duplicate = FALSE
GROUP BY transaction_date
ORDER BY transaction_date;
```

---

## Materialized View Refresh

### Aggregate Refresh Function
```sql
CREATE OR REPLACE FUNCTION refresh_monthly_stats(p_user_id UUID, p_month DATE)
RETURNS VOID AS $$
BEGIN
    -- Delete existing stats
    DELETE FROM monthly_stats 
    WHERE user_id = p_user_id AND month = p_month;
    
    -- Recompute
    INSERT INTO monthly_stats (
        user_id, month, total_transactions, total_amount, avg_transaction
    )
    SELECT 
        user_id,
        DATE_TRUNC('month', transaction_date) as month,
        COUNT(*),
        SUM(amount),
        AVG(amount)
    FROM transactions
    WHERE user_id = p_user_id
      AND DATE_TRUNC('month', transaction_date) = p_month
      AND is_duplicate = FALSE
    GROUP BY user_id, month;
    
    -- Refresh category breakdowns
    DELETE FROM category_breakdowns
    WHERE user_id = p_user_id AND month = p_month;
    
    INSERT INTO category_breakdowns (
        user_id, category_id, month, transaction_count, total_amount, avg_amount
    )
    SELECT 
        user_id,
        category_id,
        DATE_TRUNC('month', transaction_date),
        COUNT(*),
        SUM(amount),
        AVG(amount)
    FROM transactions
    WHERE user_id = p_user_id
      AND DATE_TRUNC('month', transaction_date) = p_month
      AND is_duplicate = FALSE
    GROUP BY user_id, category_id, month;
END;
$$ LANGUAGE plpgsql;
```

---

## Partitioning Strategy (For Scale)

### Partition Transactions by Month
```sql
-- Convert to partitioned table (requires migration)
CREATE TABLE transactions_partitioned (
    LIKE transactions INCLUDING ALL
) PARTITION BY RANGE (transaction_date);

-- Create monthly partitions
CREATE TABLE transactions_2025_03 PARTITION OF transactions_partitioned
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

CREATE TABLE transactions_2025_04 PARTITION OF transactions_partitioned
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');

-- Auto-create future partitions via cron job or trigger
```

---

## Backup & Export

### CSV Export Query
```sql
COPY (
    SELECT 
        t.transaction_date,
        t.amount,
        t.currency,
        t.merchant_raw,
        m.canonical_name as merchant,
        c.name as category,
        a.name as account,
        t.notes,
        t.source,
        t.created_at
    FROM transactions t
    LEFT JOIN merchants m ON t.merchant_id = m.merchant_id
    LEFT JOIN categories c ON t.category_id = c.category_id
    LEFT JOIN accounts a ON t.account_id = a.account_id
    WHERE t.user_id = :user_id
      AND t.is_duplicate = FALSE
    ORDER BY t.transaction_date DESC
) TO STDOUT WITH CSV HEADER;
```

---

## Performance Optimization

### Connection Pooling
```
Max Connections: 100
Pool Size: 20 per app instance
Idle Timeout: 10 minutes
```

### Query Performance
```sql
-- Analyze query plans
EXPLAIN ANALYZE
SELECT * FROM transactions WHERE user_id = :user_id LIMIT 50;

-- Update statistics
ANALYZE transactions;

-- Vacuum regularly
VACUUM ANALYZE transactions;
```

### Indexes Review
```sql
-- Find unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Find missing indexes
SELECT * FROM pg_stat_statements
WHERE calls > 100 AND mean_exec_time > 100
ORDER BY mean_exec_time DESC;
```

---

## Security

### Row-Level Security (RLS)
```sql
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY txn_user_isolation ON transactions
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY merchant_user_isolation ON merchants
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);
```

### Encryption
```sql
-- Encrypt sensitive fields (if needed)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Example: Encrypt notes
ALTER TABLE transactions 
ADD COLUMN notes_encrypted BYTEA;

-- Encrypt on insert
INSERT INTO transactions (notes_encrypted)
VALUES (pgp_sym_encrypt('Sensitive note', :encryption_key));

-- Decrypt on select
SELECT pgp_sym_decrypt(notes_encrypted, :encryption_key) FROM transactions;
```

---

## Scaling Considerations

### Read Replicas
```yaml
Primary: Writes + Real-time reads
Replica 1: Analytics queries
Replica 2: Export/backup operations
```

### Horizontal Partitioning
```yaml
Shard by user_id:
- Shard 1: user_id 0-999999
- Shard 2: user_id 1000000-1999999
```

### Archive Old Data
```sql
-- Move transactions older than 2 years to archive table
CREATE TABLE transactions_archive (LIKE transactions);

INSERT INTO transactions_archive
SELECT * FROM transactions
WHERE transaction_date < CURRENT_DATE - INTERVAL '2 years';

DELETE FROM transactions
WHERE transaction_date < CURRENT_DATE - INTERVAL '2 years';
```

---

## Monitoring Queries

### Database Size
```sql
SELECT 
    pg_size_pretty(pg_database_size(current_database())) as db_size;
```

### Table Sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Slow Queries
```sql
SELECT 
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```