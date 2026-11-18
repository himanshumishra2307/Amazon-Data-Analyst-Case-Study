/* AMAZON CASE STUDY - SQL ANALYSIS
 * SECTION 1 : DATABASE CHECK*/

-- Connect to amazon_db before running this script.

-- Show Tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Describe customers
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'customers'
ORDER BY ordinal_position;

-- Describe orders
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'orders'
ORDER BY ordinal_position;

-- Describe revenue
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'revenue'
ORDER BY ordinal_position;


/*===========================================================*
 * SECTION 2 : DATA PREVIEW
 *===========================================================*/

SELECT *
FROM customers
LIMIT 10;

SELECT *
FROM orders
LIMIT 10;

SELECT *
FROM revenue
LIMIT 10;


/*===========================================================*
 * SECTION 3 : RECORD COUNTS
 *===========================================================*/

SELECT COUNT(*) AS total_customers
FROM customers;

SELECT COUNT(*) AS total_orders
FROM orders;

SELECT COUNT(*) AS total_payments
FROM revenue;


/*===========================================================*
 * SECTION 4 : NULL CHECK
 *===========================================================*/

SELECT *
FROM customers
WHERE email IS NULL;

SELECT *
FROM orders
WHERE unit_price_usd IS NULL;

SELECT *
FROM revenue
WHERE amount_paid_usd IS NULL;


/*===========================================================*
 * SECTION 5 : BASIC ANALYSIS
 *===========================================================*/

SELECT DISTINCT city
FROM customers;

SELECT DISTINCT membership_tier
FROM customers;

SELECT DISTINCT payment_method
FROM orders;

SELECT DISTINCT order_status
FROM orders;

SELECT DISTINCT payment_status
FROM revenue;


/*===========================================================*
 * SECTION 6 : AGGREGATE FUNCTIONS
 *===========================================================*/

SELECT
    MIN(unit_price_usd) AS minimum_price,
    MAX(unit_price_usd) AS maximum_price,
    AVG(unit_price_usd) AS average_price
FROM orders;

SELECT
    SUM(amount_paid_usd) AS total_revenue
FROM revenue;

SELECT
    AVG(quantity) AS average_quantity
FROM orders;

/*===========================================================*
 * SECTION 7 : GROUP BY
 *===========================================================*/

SELECT
    membership_tier,
    COUNT(*) AS customers
FROM customers
GROUP BY membership_tier;

SELECT
    city,
    COUNT(*) AS customers
FROM customers
GROUP BY city
ORDER BY customers DESC;

SELECT
    payment_status,
    COUNT(*) AS total
FROM revenue
GROUP BY payment_status;

SELECT
    payment_method,
    COUNT(*) AS total_orders
FROM orders
GROUP BY payment_method;


/*===========================================================*
 * SECTION 8 : INNER JOIN
 *===========================================================*/

SELECT
    o.order_id,
    c.customer_name,
    c.city,
    o.product_category,
    o.quantity,
    o.unit_price_usd
FROM orders o
INNER JOIN customers c
ON o.customer_id = c.customer_id;

SELECT
    o.order_id,
    o.product_category,
    r.amount_paid_usd,
    r.payment_status
FROM orders o
INNER JOIN revenue r
ON o.order_id = r.order_id;


/*===========================================================*
 * SECTION 9 : THREE TABLE JOIN
 *===========================================================*/

SELECT
    o.order_id,
    c.customer_name,
    c.city,
    o.product_category,
    o.quantity,
    o.unit_price_usd,
    r.amount_paid_usd,
    r.payment_status
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
JOIN revenue r
ON o.order_id = r.order_id;


/*===========================================================*
 * SECTION 10 : BUSINESS QUESTIONS
 *===========================================================*/

-- Top 10 Customers by Number of Orders
SELECT
    c.customer_name,
    COUNT(*) AS total_orders
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
GROUP BY c.customer_name
ORDER BY total_orders DESC
LIMIT 10;

-- Revenue by City
SELECT
    c.city,
    SUM(r.amount_paid_usd) AS revenue
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
JOIN revenue r
ON o.order_id = r.order_id
GROUP BY c.city
ORDER BY revenue DESC;

-- Revenue by Membership
SELECT
    c.membership_tier,
    SUM(r.amount_paid_usd) AS revenue
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
JOIN revenue r
ON o.order_id = r.order_id
GROUP BY c.membership_tier
ORDER BY revenue DESC;

-- Top Selling Products
SELECT
    product_category,
    SUM(quantity) AS quantity_sold
FROM orders
GROUP BY product_category
ORDER BY quantity_sold DESC
LIMIT 10;

-- Highest Revenue Products
SELECT
    o.product_category,
    SUM(r.amount_paid_usd) AS revenue
FROM orders o
JOIN revenue r
ON o.order_id = r.order_id
GROUP BY o.product_category
ORDER BY revenue DESC
LIMIT 10;

/*===========================================================*
 * SECTION 11 : HAVING
 *===========================================================*/

SELECT
    city,
    COUNT(*) AS customers
FROM customers
GROUP BY city
HAVING COUNT(*) > 20;

SELECT
    product_category,
    SUM(quantity) AS quantity
FROM orders
GROUP BY product_category
HAVING SUM(quantity) > 100;


/*===========================================================*
 * SECTION 12 : CASE WHEN
 *===========================================================*/

SELECT
    customer_name,
    membership_tier,
    CASE
        WHEN membership_tier = 'Gold' THEN 'Premium'
        WHEN membership_tier = 'Silver' THEN 'Regular'
        ELSE 'Basic'
    END AS customer_segment
FROM customers;

SELECT
    product_category,
    unit_price_usd,
    CASE
        WHEN unit_price_usd >= 1000 THEN 'Expensive'
        WHEN unit_price_usd >= 500 THEN 'Medium'
        ELSE 'Budget'
    END AS price_category
FROM orders;


/*===========================================================*
 * SECTION 13 : SUBQUERY
 *===========================================================*/

SELECT *
FROM orders
WHERE unit_price_usd >
(
    SELECT AVG(unit_price_usd)
    FROM orders
);

SELECT *
FROM revenue
WHERE amount_paid_usd >
(
    SELECT AVG(amount_paid_usd)
    FROM revenue
);


/*===========================================================*
 * SECTION 14 : CTE
 *===========================================================*/

WITH revenue_summary AS
(
    SELECT
        o.customer_id,
        SUM(r.amount_paid_usd) AS revenue
    FROM orders o
    JOIN revenue r
    ON o.order_id = r.order_id
    GROUP BY o.customer_id
)

SELECT *
FROM revenue_summary
ORDER BY revenue DESC;


/*===========================================================*
 * SECTION 15 : WINDOW FUNCTIONS
 *===========================================================*/

SELECT
    product_category,
    SUM(quantity) AS quantity_sold,
    RANK() OVER (
        ORDER BY SUM(quantity) DESC
    ) AS product_rank
FROM orders
GROUP BY product_category;

SELECT
    customer_id,
    SUM(amount_paid_usd) AS revenue,
    DENSE_RANK() OVER (
        ORDER BY SUM(amount_paid_usd) DESC
    ) AS revenue_rank
FROM orders o
JOIN revenue r
ON o.order_id = r.order_id
GROUP BY customer_id;


/*===========================================================*
 * SECTION 16 : ROW NUMBER
 *===========================================================*/

SELECT
    customer_name,
    city,
    ROW_NUMBER() OVER (
        PARTITION BY city
        ORDER BY customer_name
    ) AS row_num
FROM customers;


/*===========================================================*
 * SECTION 17 : VIEW
 *===========================================================*/

CREATE OR REPLACE VIEW customer_orders AS
SELECT
    c.customer_name,
    c.city,
    o.product_category,
    o.quantity,
    r.amount_paid_usd
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
JOIN revenue r
ON o.order_id = r.order_id;

SELECT *
FROM customer_orders;


/*===========================================================*
 * SECTION 18 : FINAL KPIs
 *===========================================================*/

SELECT COUNT(*) AS total_customers
FROM customers;

SELECT COUNT(*) AS total_orders
FROM orders;

SELECT SUM(amount_paid_usd) AS total_revenue
FROM revenue;

SELECT AVG(amount_paid_usd) AS average_transaction
FROM revenue;

SELECT MAX(amount_paid_usd) AS highest_transaction
FROM revenue;

SELECT MIN(amount_paid_usd) AS lowest_transaction
FROM revenue;