# SQL Server to Snowflake/dbt Conversion Guide

A quick-reference for migrating SQL Server T-SQL to Snowflake using dbt. Each section maps SQL Server functions and patterns to their **dbt (platform-agnostic)** and **Snowflake-native** equivalents.

**Priority order:** dbt macro/function > Snowflake SQL > raw SQL workaround

**Key resources:**
- [dbt Jinja Functions](https://docs.getdbt.com/reference/dbt-jinja-functions)
- [dbt_utils package](https://github.com/dbt-labs/dbt-utils)
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference-functions)

---

## Table of Contents
1. [Date & Time Functions](#1-date--time-functions)
2. [String Functions](#2-string-functions)
3. [Type Casting & Conversion](#3-type-casting--conversion)
4. [Aggregate Functions](#4-aggregate-functions)
5. [Window / Analytical Functions](#5-window--analytical-functions)
6. [Conditional Logic](#6-conditional-logic)
7. [Joins & Set Operations](#7-joins--set-operations)
8. [CTEs & Subqueries](#8-ctes--subqueries)
9. [Table & Schema Patterns](#9-table--schema-patterns)
10. [Stored Procedures & Control Flow](#10-stored-procedures--control-flow)
11. [dbt-Specific Patterns](#11-dbt-specific-patterns)
12. [Key Behavioral Differences](#12-key-behavioral-differences)

---

## 1. Date & Time Functions

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `GETDATE()` | `{{ dbt.current_timestamp() }}` | `CURRENT_TIMESTAMP()` |
| `GETUTCDATE()` | `{{ dbt.current_timestamp() }}` (Snowflake defaults to UTC) | `CURRENT_TIMESTAMP()` |
| `SYSDATETIME()` | `{{ dbt.current_timestamp() }}` | `CURRENT_TIMESTAMP()` |
| `DATEADD(day, 7, col)` | `{{ dateadd('day', 7, 'col') }}` | `DATEADD('day', 7, col)` |
| `DATEDIFF(day, start, end)` | `{{ datediff('day', 'start', 'end') }}` | `DATEDIFF('day', start, end)` |
| `DATEPART(year, col)` | -- | `DATE_PART('year', col)` or `EXTRACT(year FROM col)` |
| `DATENAME(month, col)` | -- | `MONTHNAME(col)` or `TO_CHAR(col, 'MMMM')` |
| `YEAR(col)` / `MONTH(col)` / `DAY(col)` | -- | `YEAR(col)` / `MONTH(col)` / `DAY(col)` |
| `EOMONTH(col)` | `{{ last_day('col', 'month') }}` | `LAST_DAY(col, 'month')` |
| `DATEFROMPARTS(y, m, d)` | -- | `DATE_FROM_PARTS(y, m, d)` |
| `ISDATE(val)` | -- | `TRY_TO_DATE(val) IS NOT NULL` |
| `CONVERT(DATE, col)` | `{{ dbt.date_trunc('day', 'col') }}` | `col::DATE` or `TO_DATE(col)` |
| `CONVERT(VARCHAR, col, 112)` | -- | `TO_CHAR(col, 'YYYYMMDD')` |
| `FORMAT(col, 'yyyy-MM-dd')` | -- | `TO_CHAR(col, 'YYYY-MM-DD')` |
| `SWITCHOFFSET(col, '+00:00')` | -- | `CONVERT_TIMEZONE('UTC', col)` |

### Common date style codes (CONVERT)

| SQL Server Style | Format | Snowflake TO_CHAR Equivalent |
|---|---|---|
| `101` | `MM/DD/YYYY` | `TO_CHAR(col, 'MM/DD/YYYY')` |
| `103` | `DD/MM/YYYY` | `TO_CHAR(col, 'DD/MM/YYYY')` |
| `110` | `MM-DD-YYYY` | `TO_CHAR(col, 'MM-DD-YYYY')` |
| `112` | `YYYYMMDD` | `TO_CHAR(col, 'YYYYMMDD')` |
| `120` | `YYYY-MM-DD HH:MI:SS` | `TO_CHAR(col, 'YYYY-MM-DD HH24:MI:SS')` |
| `23` | `YYYY-MM-DD` | `TO_CHAR(col, 'YYYY-MM-DD')` |

### DATEDIFF examples

```sql
-- SQL Server: days between two dates
DATEDIFF(DAY, start_date, end_date)

-- dbt (preferred)
{{ datediff('start_date', 'end_date', 'day') }}

-- Snowflake
DATEDIFF('day', start_date, end_date)

-- SQL Server: months between two dates
DATEDIFF(MONTH, hire_date, GETDATE())

-- dbt (preferred)
{{ datediff('hire_date', dbt.current_timestamp(), 'month') }}

-- Snowflake
DATEDIFF('month', hire_date, CURRENT_TIMESTAMP())
```

> **Note:** SQL Server's `DATEDIFF` counts boundary crossings (e.g. Dec 31 → Jan 1 = 1 month), while Snowflake's behaves the same way. However, be aware that dbt's `datediff` macro argument order is `(first_date, second_date, datepart)` — the datepart is **last**, unlike SQL Server where it's first.

### Date arithmetic

```sql
-- SQL Server: add 30 days
DATEADD(DAY, 30, order_date)

-- dbt (preferred)
{{ dateadd('day', 30, 'order_date') }}

-- Snowflake
DATEADD('day', 30, order_date)
-- or simply:
order_date + 30
```

---

## 2. String Functions

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `LEN(col)` | -- | `LENGTH(col)` |
| `DATALENGTH(col)` | -- | `OCTET_LENGTH(col)` |
| `SUBSTRING(col, start, len)` | -- | `SUBSTRING(col, start, len)` or `SUBSTR(col, start, len)` |
| `LEFT(col, n)` | -- | `LEFT(col, n)` |
| `RIGHT(col, n)` | -- | `RIGHT(col, n)` |
| `CHARINDEX(search, col)` | -- | `CHARINDEX(search, col)` or `POSITION(search IN col)` |
| `CHARINDEX(search, col, start)` | -- | `CHARINDEX(search, col, start)` |
| `PATINDEX('%pattern%', col)` | -- | `REGEXP_INSTR(col, 'pattern')` |
| `REPLACE(col, old, new)` | -- | `REPLACE(col, old, new)` |
| `STUFF(col, start, len, new)` | -- | `INSERT(col, start, len, new)` |
| `REPLICATE(str, n)` | -- | `REPEAT(str, n)` |
| `LTRIM(col)` / `RTRIM(col)` | -- | `LTRIM(col)` / `RTRIM(col)` or `TRIM(col)` |
| `UPPER(col)` / `LOWER(col)` | -- | `UPPER(col)` / `LOWER(col)` |
| `CONCAT(a, b, c)` | `{{ dbt.concat(['a', 'b', 'c']) }}` | `CONCAT(a, b, c)` or `a \|\| b \|\| c` |
| `CONCAT_WS(',', a, b)` | -- | `CONCAT_WS(',', a, b)` |
| `STRING_AGG(col, ',')` | `{{ dbt_utils.listagg('col', "','") }}` | `LISTAGG(col, ',')` |
| `REVERSE(col)` | -- | `REVERSE(col)` |
| `SPACE(n)` | -- | `SPACE(n)` |
| `STRING_SPLIT(col, ',')` | -- | `SPLIT_TABLE(SPLIT(col, ','))` or `LATERAL FLATTEN` |
| `FORMAT(num, 'N2')` | -- | `TO_CHAR(num, '999,999.00')` |
| `QUOTENAME(col)` | -- | `'"' \|\| col \|\| '"'` |
| `ISNUMERIC(col)` | -- | `TRY_TO_NUMBER(col) IS NOT NULL` |

### STUFF (insert/replace within string)

```sql
-- SQL Server: remove first comma from a string_agg result
STUFF(
    (SELECT ',' + name FROM items FOR XML PATH('')),
    1, 1, ''
)

-- Snowflake: LISTAGG handles this directly, no STUFF needed
LISTAGG(name, ',') WITHIN GROUP (ORDER BY name)
```

### STRING_SPLIT / Flattening delimited strings

```sql
-- SQL Server
SELECT value FROM STRING_SPLIT('a,b,c', ',')

-- Snowflake
SELECT f.value::STRING AS value
FROM TABLE(FLATTEN(INPUT => SPLIT('a,b,c', ','))) f
```

### Pattern matching

```sql
-- SQL Server: PATINDEX
PATINDEX('%[0-9]%', col)

-- Snowflake: REGEXP_INSTR
REGEXP_INSTR(col, '[0-9]')

-- SQL Server: LIKE with wildcard
col LIKE '%test%'

-- Snowflake: same, or use ILIKE for case-insensitive
col ILIKE '%test%'
```

---

## 3. Type Casting & Conversion

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `CAST(col AS INT)` | `CAST(col AS {{ dbt.type_int() }})` | `col::INT` or `CAST(col AS INT)` |
| `CAST(col AS VARCHAR(50))` | `CAST(col AS {{ dbt.type_string() }})` | `col::VARCHAR(50)` |
| `CAST(col AS DECIMAL(10,2))` | `CAST(col AS {{ dbt.type_numeric() }})` | `col::DECIMAL(10,2)` or `col::NUMBER(10,2)` |
| `CAST(col AS DATETIME)` | `CAST(col AS {{ dbt.type_timestamp() }})` | `col::TIMESTAMP` |
| `CAST(col AS FLOAT)` | `CAST(col AS {{ dbt.type_float() }})` | `col::FLOAT` |
| `CONVERT(INT, col)` | same as CAST | `col::INT` |
| `CONVERT(VARCHAR, col, style)` | -- | `TO_CHAR(col, format)` (see date styles above) |
| `TRY_CAST(col AS INT)` | `{{ dbt.safe_cast('col', dbt.type_int()) }}` | `TRY_CAST(col AS INT)` |
| `TRY_CONVERT(INT, col)` | `{{ dbt.safe_cast('col', dbt.type_int()) }}` | `TRY_CAST(col AS INT)` |
| `ISNULL(col, default)` | -- | `NVL(col, default)` or `COALESCE(col, default)` |
| `COALESCE(a, b, c)` | -- | `COALESCE(a, b, c)` |
| `NULLIF(a, b)` | -- | `NULLIF(a, b)` |
| `IIF(cond, true, false)` | -- | `IFF(cond, true, false)` |

### dbt type macros

Use these in your models to keep data types platform-agnostic:

```sql
-- In a dbt model
SELECT
    CAST(id AS {{ dbt.type_int() }})           AS id,
    CAST(name AS {{ dbt.type_string() }})      AS name,
    CAST(amount AS {{ dbt.type_numeric() }})   AS amount,
    CAST(created AS {{ dbt.type_timestamp() }}) AS created_at
FROM {{ source('raw', 'orders') }}
```

### Safe casting pattern

```sql
-- SQL Server
SELECT TRY_CONVERT(INT, user_input) AS safe_val

-- dbt (preferred — returns NULL instead of erroring on bad input)
SELECT {{ dbt.safe_cast('user_input', dbt.type_int()) }} AS safe_val

-- Snowflake
SELECT TRY_CAST(user_input AS INT) AS safe_val

-- For dates specifically:
-- SQL Server
SELECT TRY_CONVERT(DATE, date_string, 101)

-- dbt (preferred)
SELECT {{ dbt.safe_cast('date_string', dbt.type_timestamp()) }} AS safe_val

-- Snowflake (with format string — more precise for known formats)
SELECT TRY_TO_DATE(date_string, 'MM/DD/YYYY')
```

---

## 4. Aggregate Functions

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `COUNT(*)` | -- | `COUNT(*)` |
| `COUNT(DISTINCT col)` | -- | `COUNT(DISTINCT col)` |
| `COUNT_BIG(*)` | -- | `COUNT(*)` (Snowflake returns BIGINT natively) |
| `SUM(col)` | -- | `SUM(col)` |
| `AVG(col)` | -- | `AVG(col)` |
| `MIN(col)` / `MAX(col)` | -- | `MIN(col)` / `MAX(col)` |
| `STRING_AGG(col, ',')` | `{{ dbt_utils.listagg('col', "','") }}` | `LISTAGG(col, ',')` |
| `STRING_AGG(col, ',') WITHIN GROUP (ORDER BY col)` | `{{ dbt_utils.listagg('col', "','", "ORDER BY col") }}` | `LISTAGG(col, ',') WITHIN GROUP (ORDER BY col)` |
| `GROUPING(col)` | -- | `GROUPING(col)` |
| `STDEV(col)` | -- | `STDDEV(col)` |
| `VAR(col)` | -- | `VARIANCE(col)` |
| `CHECKSUM_AGG(col)` | -- | `HASH_AGG(col)` |
| `APPROX_COUNT_DISTINCT(col)` | -- | `APPROX_COUNT_DISTINCT(col)` or `HLL(col)` |

### GROUP BY with ROLLUP/CUBE

```sql
-- SQL Server
SELECT region, product, SUM(sales)
FROM orders
GROUP BY ROLLUP(region, product)

-- Snowflake: identical syntax
SELECT region, product, SUM(sales)
FROM orders
GROUP BY ROLLUP(region, product)

-- SQL Server: GROUP BY with GROUPING SETS
GROUP BY GROUPING SETS ((region), (product), ())

-- Snowflake: identical
GROUP BY GROUPING SETS ((region), (product), ())
```

---

## 5. Window / Analytical Functions

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `ROW_NUMBER() OVER (...)` | -- | `ROW_NUMBER() OVER (...)` |
| `RANK() OVER (...)` | -- | `RANK() OVER (...)` |
| `DENSE_RANK() OVER (...)` | -- | `DENSE_RANK() OVER (...)` |
| `NTILE(n) OVER (...)` | -- | `NTILE(n) OVER (...)` |
| `LEAD(col, n) OVER (...)` | -- | `LEAD(col, n) OVER (...)` |
| `LAG(col, n) OVER (...)` | -- | `LAG(col, n) OVER (...)` |
| `FIRST_VALUE(col) OVER (...)` | -- | `FIRST_VALUE(col) OVER (...)` |
| `LAST_VALUE(col) OVER (...)` | -- | `LAST_VALUE(col) OVER (...)` |
| `PERCENT_RANK() OVER (...)` | -- | `PERCENT_RANK() OVER (...)` |
| `CUME_DIST() OVER (...)` | -- | `CUME_DIST() OVER (...)` |
| `SUM(col) OVER (...)` | -- | `SUM(col) OVER (...)` |
| `COUNT(col) OVER (...)` | -- | `COUNT(col) OVER (...)` |

Window functions are **largely identical** between SQL Server and Snowflake. Key differences:

### LAST_VALUE gotcha

```sql
-- SQL Server: LAST_VALUE default frame is RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
-- This means LAST_VALUE often doesn't return what you expect without explicit framing.
-- Same issue exists in Snowflake. Always specify the frame:

LAST_VALUE(col) OVER (
    PARTITION BY grp
    ORDER BY sort_col
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
)
```

### Running totals

```sql
-- SQL Server
SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date
                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)

-- Snowflake: identical syntax
SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date
                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
```

### QUALIFY (Snowflake bonus — no SQL Server equivalent)

```sql
-- SQL Server: filter on window function requires subquery
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) AS rn
    FROM orders
) sub
WHERE rn = 1

-- Snowflake: QUALIFY eliminates the subquery
SELECT *
FROM orders
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1
```

---

## 6. Conditional Logic

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `CASE WHEN x THEN y END` | -- | `CASE WHEN x THEN y END` |
| `IIF(cond, true, false)` | -- | `IFF(cond, true, false)` (note: one F) |
| `CHOOSE(idx, a, b, c)` | -- | Use `CASE` or array: `ARRAY_CONSTRUCT(a,b,c)[idx-1]` |
| `COALESCE(a, b, c)` | -- | `COALESCE(a, b, c)` |
| `ISNULL(col, default)` | -- | `NVL(col, default)` or `IFNULL(col, default)` or `COALESCE(col, default)` |
| `NULLIF(a, b)` | -- | `NULLIF(a, b)` |
| `CASE col WHEN 1 THEN 'a' ...` | -- | `DECODE(col, 1, 'a', ...)` or use `CASE` |

### ISNULL vs NVL vs COALESCE

```sql
-- SQL Server
ISNULL(col, 'default')        -- 2 args only, uses datatype of first arg

-- Snowflake options:
NVL(col, 'default')           -- 2 args, same as ISNULL
IFNULL(col, 'default')        -- 2 args, alias for NVL
COALESCE(col, alt, 'default') -- N args (preferred for dbt portability)

-- Recommendation: use COALESCE everywhere for portability
```

### Snowflake extras (no SQL Server equivalent)

```sql
-- ZEROIFNULL: returns 0 if null (handy for numeric columns)
ZEROIFNULL(amount)  -- equivalent to: COALESCE(amount, 0)

-- NVL2: if not null return x, if null return y
NVL2(col, 'has value', 'is null')
-- equivalent to: CASE WHEN col IS NOT NULL THEN 'has value' ELSE 'is null' END
```

---

## 7. Joins & Set Operations

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `INNER JOIN` | -- | `INNER JOIN` |
| `LEFT OUTER JOIN` | -- | `LEFT OUTER JOIN` |
| `RIGHT OUTER JOIN` | -- | `RIGHT OUTER JOIN` |
| `FULL OUTER JOIN` | -- | `FULL OUTER JOIN` |
| `CROSS JOIN` | -- | `CROSS JOIN` |
| `CROSS APPLY` | -- | `, LATERAL (subquery)` |
| `OUTER APPLY` | -- | `LEFT JOIN LATERAL (subquery)` |
| `CROSS APPLY OPENJSON(col)` | -- | `, LATERAL FLATTEN(INPUT => col)` |
| `TOP n` | -- | `LIMIT n` |
| `TOP n WITH TIES` | -- | Use `QUALIFY RANK() OVER (...) <= n` |
| `UNION` | -- | `UNION` |
| `UNION ALL` | -- | `UNION ALL` |
| `EXCEPT` | -- | `EXCEPT` or `MINUS` |
| `INTERSECT` | -- | `INTERSECT` |

### CROSS APPLY / OUTER APPLY

```sql
-- SQL Server: CROSS APPLY (like INNER JOIN LATERAL)
SELECT o.order_id, d.product_id
FROM orders o
CROSS APPLY (
    SELECT TOP 1 product_id
    FROM order_details d
    WHERE d.order_id = o.order_id
    ORDER BY quantity DESC
) d

-- Snowflake: LATERAL + LIMIT
SELECT o.order_id, d.product_id
FROM orders o,
LATERAL (
    SELECT product_id
    FROM order_details d
    WHERE d.order_id = o.order_id
    ORDER BY quantity DESC
    LIMIT 1
) d

-- SQL Server: OUTER APPLY (like LEFT JOIN LATERAL)
-- Snowflake:
LEFT JOIN LATERAL (...) d ON TRUE
```

### Flattening JSON / arrays

```sql
-- SQL Server: CROSS APPLY with OPENJSON
SELECT o.id, j.value
FROM orders o
CROSS APPLY OPENJSON(o.tags) j

-- Snowflake: LATERAL FLATTEN
SELECT o.id, f.value::STRING AS tag
FROM orders o,
LATERAL FLATTEN(INPUT => PARSE_JSON(o.tags)) f
```

### TOP vs LIMIT

```sql
-- SQL Server
SELECT TOP 10 * FROM orders ORDER BY created_at DESC

-- Snowflake
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10

-- SQL Server: TOP with PERCENT
SELECT TOP 10 PERCENT * FROM orders

-- Snowflake: use window function
SELECT * FROM orders
QUALIFY ROW_NUMBER() OVER (ORDER BY created_at) <= (SELECT COUNT(*) * 0.10 FROM orders)
```

---

## 8. CTEs & Subqueries

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `WITH cte AS (...)` | -- | `WITH cte AS (...)` |
| Recursive CTE | -- | Recursive CTE (same syntax) |
| `#temp_table` | `{{ config(materialized='ephemeral') }}` | `CREATE TEMPORARY TABLE` |
| `##global_temp` | -- | Not applicable; use permanent/transient tables |
| `@table_variable` | -- | Not applicable; use CTE or temp table |
| `SELECT INTO #temp` | -- | `CREATE TEMPORARY TABLE t AS SELECT ...` |

### CTE syntax (identical)

```sql
-- Works in both SQL Server and Snowflake
WITH customer_orders AS (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
),
ranked AS (
    SELECT *, RANK() OVER (ORDER BY order_count DESC) AS rnk
    FROM customer_orders
)
SELECT * FROM ranked WHERE rnk <= 10
```

### Recursive CTE

```sql
-- SQL Server
WITH hierarchy AS (
    SELECT id, parent_id, name, 0 AS depth
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    SELECT c.id, c.parent_id, c.name, h.depth + 1
    FROM categories c
    INNER JOIN hierarchy h ON c.parent_id = h.id
)
SELECT * FROM hierarchy
OPTION (MAXRECURSION 100)

-- Snowflake: same, but use maxrecursion differently
WITH RECURSIVE hierarchy AS (
    SELECT id, parent_id, name, 0 AS depth
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    SELECT c.id, c.parent_id, c.name, h.depth + 1
    FROM categories c
    INNER JOIN hierarchy h ON c.parent_id = h.id
)
SELECT * FROM hierarchy
-- Note: Snowflake adds RECURSIVE keyword and has no OPTION (MAXRECURSION).
-- Default limit is 100 iterations. Adjust via session parameter if needed.
```

### Temp tables in dbt

```sql
-- Instead of SQL Server temp tables, use dbt model materializations:

-- Ephemeral (CTE, not persisted — replaces #temp for intermediate calcs)
{{ config(materialized='ephemeral') }}

-- View (lightweight, always fresh)
{{ config(materialized='view') }}

-- Table (persisted, replaces SELECT INTO)
{{ config(materialized='table') }}

-- Incremental (replaces MERGE / append patterns)
{{ config(materialized='incremental', unique_key='id') }}
```

---

## 9. Table & Schema Patterns

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `IDENTITY(1,1)` | `{{ dbt_utils.generate_surrogate_key(['col1','col2']) }}` | `AUTOINCREMENT` or `IDENTITY(1,1)` |
| `NEWID()` | `{{ dbt_utils.generate_surrogate_key([...]) }}` | `UUID_STRING()` |
| `@@ROWCOUNT` | -- | Use result scanning or `RESULT_SCAN()` |
| `SCOPE_IDENTITY()` | -- | Not applicable in dbt; use surrogate keys |
| `NOLOCK` hint | -- | Not applicable (Snowflake MVCC handles this) |
| `WITH (INDEX = ...)` | -- | Not applicable (Snowflake has automatic micro-partitioning) |
| `TRUNCATE TABLE` | -- | `TRUNCATE TABLE` |
| `schema.table` | `{{ ref('model') }}` or `{{ source('src', 'table') }}` | `database.schema.table` |
| `MERGE ... WHEN MATCHED` | `{{ config(materialized='incremental') }}` | `MERGE INTO ... USING ...` |

### MERGE / UPSERT pattern

```sql
-- SQL Server
MERGE target AS t
USING source AS s ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.val = s.val
WHEN NOT MATCHED THEN INSERT (id, val) VALUES (s.id, s.val);

-- dbt incremental model (preferred)
{{ config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge'
) }}

SELECT id, val, updated_at
FROM {{ source('raw', 'data') }}
{% if is_incremental() %}
WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}

-- Snowflake native MERGE (if not using dbt)
MERGE INTO target t
USING source s ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.val = s.val
WHEN NOT MATCHED THEN INSERT (id, val) VALUES (s.id, s.val);
```

### Three-part naming

```sql
-- SQL Server
SELECT * FROM [database].[schema].[table]

-- Snowflake
SELECT * FROM database.schema.table

-- dbt (preferred — abstracts this away)
SELECT * FROM {{ ref('model_name') }}
SELECT * FROM {{ source('source_name', 'table_name') }}
```

---

## 10. Stored Procedures & Control Flow

| SQL Server | dbt / dbt_utils | Snowflake Native |
|---|---|---|
| `CREATE PROCEDURE` | dbt macro + `run-operation` | `CREATE PROCEDURE` (Snowflake Scripting, JavaScript, or Python) |
| `IF ... ELSE` | `{% if ... %} {% else %} {% endif %}` | `IF ... THEN ... ELSE ... END IF;` (in scripting) |
| `WHILE` | `{% for item in items %}` | `WHILE ... DO ... END WHILE;` (in scripting) |
| `TRY ... CATCH` | `{{ exceptions.raise_compiler_error() }}` | `BEGIN ... EXCEPTION ... END;` (in scripting) |
| `EXEC sp_name` | `dbt run-operation macro_name` | `CALL procedure_name()` |
| `CURSOR` | Avoid; use set-based logic or dbt Jinja loops | Avoid; use set-based logic |
| Dynamic SQL (`EXEC(@sql)`) | Jinja templating `{{ }}` | `EXECUTE IMMEDIATE` |
| `PRINT` | `{{ print('message') }}` or `{{ log('message', info=true) }}` | `SYSTEM$LOG('INFO', 'message')` |
| `RAISERROR` | `{{ exceptions.raise_compiler_error('msg') }}` | `RAISE` (in scripting) |

### Converting a stored procedure to dbt

```sql
-- SQL Server stored procedure
CREATE PROCEDURE dbo.refresh_summary AS
BEGIN
    TRUNCATE TABLE summary;
    INSERT INTO summary
    SELECT region, SUM(amount) AS total
    FROM orders
    GROUP BY region;
END

-- dbt model: models/summary.sql (replaces the entire procedure)
{{ config(materialized='table') }}

SELECT
    region,
    SUM(amount) AS total
FROM {{ ref('orders') }}
GROUP BY region
```

### Dynamic SQL / parameterized logic

```sql
-- SQL Server
DECLARE @col VARCHAR(50) = 'revenue'
EXEC('SELECT ' + @col + ' FROM sales')

-- dbt: use Jinja
{% set col = 'revenue' %}
SELECT {{ col }} FROM {{ ref('sales') }}

-- dbt: macro with parameters
{% macro get_column(column_name) %}
    SELECT {{ column_name }} FROM {{ ref('sales') }}
{% endmacro %}
```

---

## 11. dbt-Specific Patterns

These don't have SQL Server equivalents — they're patterns to adopt in the new dbt workflow.

### Model references

```sql
-- Always use ref() for models within your project
SELECT * FROM {{ ref('stg_orders') }}

-- Use source() for raw/external tables
SELECT * FROM {{ source('snowflake_raw', 'orders') }}
```

### Materializations

| Strategy | Use When | Replaces |
|---|---|---|
| `view` | Light transforms, always-fresh data | SQL Server views |
| `table` | Heavy transforms, queried often | `SELECT INTO`, permanent tables |
| `incremental` | Large tables, append/merge patterns | MERGE statements, nightly ETL procs |
| `ephemeral` | Intermediate calcs, reused in one place | #temp tables, CTEs in procs |

### Common dbt_utils macros

```sql
-- Surrogate keys (replaces IDENTITY + business key logic)
{{ dbt_utils.generate_surrogate_key(['customer_id', 'order_date']) }}

-- Pivot (replaces dynamic PIVOT queries)
{{ dbt_utils.pivot('status', dbt_utils.get_column_values(ref('orders'), 'status')) }}

-- Unpivot
{{ dbt_utils.unpivot(
    relation=ref('wide_table'),
    cast_to='varchar',
    exclude=['id'],
    field_name='metric',
    value_name='value'
) }}

-- Star (select all columns from a relation)
{{ dbt_utils.star(from=ref('customers'), except=['_loaded_at']) }}

-- Date spine (generate a series of dates — replaces recursive CTE date tables)
{{ dbt_utils.date_spine(
    datepart="day",
    start_date="cast('2020-01-01' as date)",
    end_date="cast(current_date() as date)"
) }}

-- Get column values (for dynamic SQL patterns)
{% set statuses = dbt_utils.get_column_values(
    table=ref('orders'),
    column='status'
) %}
```

### Incremental model patterns

```sql
-- Replaces SQL Server MERGE or nightly truncate-and-reload
{{ config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns'
) }}

SELECT
    order_id,
    customer_id,
    amount,
    updated_at
FROM {{ source('raw', 'orders') }}

{% if is_incremental() %}
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
```

---

## 12. Key Behavioral Differences

### NULL concatenation

```sql
-- SQL Server: NULL + 'text' = NULL (by default with CONCAT_NULL_YIELDS_NULL ON)
SELECT 'Hello ' + NULL + 'World'  -- Result: NULL

-- Snowflake: || operator also returns NULL
SELECT 'Hello ' || NULL || 'World'  -- Result: NULL

-- Safe approach for both: use CONCAT() which treats NULL as empty string
-- SQL Server:
SELECT CONCAT('Hello ', NULL, 'World')  -- Result: 'Hello World'
-- Snowflake:
SELECT CONCAT('Hello ', NULL, 'World')  -- Result: 'Hello World'
```

### Case sensitivity

```sql
-- SQL Server: case-insensitive by default (depends on collation)
SELECT * FROM users WHERE name = 'john'  -- matches 'John', 'JOHN', etc.

-- Snowflake: case-sensitive by default
SELECT * FROM users WHERE name = 'john'  -- only matches 'john'

-- Snowflake: use ILIKE or LOWER() for case-insensitive matching
SELECT * FROM users WHERE name ILIKE 'john'
SELECT * FROM users WHERE LOWER(name) = 'john'

-- Snowflake: identifiers are uppercased unless double-quoted
-- CREATE TABLE MyTable → stored as MYTABLE
-- CREATE TABLE "MyTable" → stored as MyTable
```

### Integer division

```sql
-- SQL Server: integer / integer = integer (truncates)
SELECT 5 / 2  -- Result: 2

-- Snowflake: integer / integer = decimal (preserves precision)
SELECT 5 / 2  -- Result: 2.500000

-- If you need integer division in Snowflake:
SELECT FLOOR(5 / 2)  -- Result: 2
SELECT DIV0(5, 2)     -- Result: 2 (also handles divide by zero)
```

### Division by zero

```sql
-- SQL Server: raises an error (unless ANSI_WARNINGS is OFF)
SELECT 10 / 0  -- Error: Divide by zero

-- Snowflake: also raises an error by default
SELECT 10 / 0  -- Error: Division by zero

-- Snowflake: use DIV0 or DIV0NULL for safe division
SELECT DIV0(10, 0)      -- Result: 0
SELECT DIV0NULL(10, 0)  -- Result: NULL
```

### Boolean type

```sql
-- SQL Server: no native BOOLEAN, uses BIT (0/1)
DECLARE @flag BIT = 1

-- Snowflake: native BOOLEAN type
SELECT TRUE, FALSE
SELECT * FROM orders WHERE is_active  -- no need for = 1
```

### Semi-structured data (JSON)

```sql
-- SQL Server: OPENJSON / JSON_VALUE / JSON_QUERY
SELECT JSON_VALUE(data, '$.name') FROM events
SELECT j.* FROM events CROSS APPLY OPENJSON(data) j

-- Snowflake: native VARIANT type + dot notation
SELECT data:name::STRING FROM events                          -- dot notation
SELECT PARSE_JSON(data_string):name::STRING FROM events       -- if stored as string
SELECT f.value:field::STRING FROM events, LATERAL FLATTEN(INPUT => data:items) f
```

### Empty string vs NULL

```sql
-- SQL Server: '' (empty string) and NULL are distinct
SELECT CASE WHEN '' = '' THEN 'equal' END  -- Result: 'equal'
SELECT CASE WHEN '' IS NULL THEN 'null' END  -- Result: NULL (not null)

-- Snowflake: same behavior, '' and NULL are distinct
-- However, be careful with LENGTH():
SELECT LENGTH('')  -- Snowflake: 0
SELECT LENGTH(NULL) -- Snowflake: NULL
```

### GETDATE() timezone behavior

```sql
-- SQL Server: GETDATE() returns server's local time
-- GETUTCDATE() returns UTC

-- Snowflake: CURRENT_TIMESTAMP() returns UTC by default
-- The session timezone can be changed:
ALTER SESSION SET TIMEZONE = 'America/Chicago';
-- Now CURRENT_TIMESTAMP() returns in that timezone
```
