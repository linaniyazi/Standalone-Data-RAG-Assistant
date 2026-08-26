-- 1. Top category by total sales
SELECT Category, SUM(Sales) AS total_sales
FROM orders
GROUP BY Category
ORDER BY total_sales DESC;

-- 2. Average profit per region
SELECT Region, AVG(Profit) AS avg_profit
FROM orders
GROUP BY Region;

-- 3. Sub-category with the biggest loss
SELECT "Sub-Category", SUM(Profit) AS total_profit
FROM orders
GROUP BY "Sub-Category"
ORDER BY total_profit ASC;

-- 4. Number of orders per segment
SELECT Segment, COUNT(DISTINCT "Order ID") AS order_count
FROM orders
GROUP BY Segment;

-- 5. Highest sale value per region
SELECT Region, MAX(Sales) AS max_sales
FROM orders
GROUP BY Region;

-- 6. Lowest sale value per region
SELECT Region, MIN(Sales) AS min_sales
FROM orders
GROUP BY Region;

-- 7. Average sales per region
SELECT Region, AVG(Sales) AS avg_sales
FROM orders
GROUP BY Region;

-- 8. Record count per city
SELECT City, COUNT(*) AS record_count
FROM orders
GROUP BY City;

-- 9. Record count per country
SELECT Country, COUNT(*) AS record_count
FROM orders
GROUP BY Country;

-- 10. Region with the highest total profit
SELECT Region, SUM(Profit) AS total_profit
FROM orders
GROUP BY Region
ORDER BY total_profit DESC;