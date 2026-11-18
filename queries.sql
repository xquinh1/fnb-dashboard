-- 1. kpi (revenue, total_orders, aov)
select
	sum(quantity*unit_price) as revenue,
	count(distinct order_id) as total_orders,
	round(sum(quantity*unit_price)/count(distinct order_id), 0) as aov
from order_items;


-- 2. Tăng trưởng doanh thu theo tháng (MoM) bằng LAG
-- Lưu ý: tháng đầu và tháng cuối không đủ ngày nên số liệu thấp hơn thực tế
WITH monthly AS (
	SELECT
		DATE_TRUNC('month', o.order_time)::date AS month,
		SUM(oi.quantity * oi.unit_price) AS revenue
	FROM orders o
	JOIN order_items oi ON oi.order_id = o.order_id
	GROUP BY 1
)
SELECT
	month,
	revenue,
	LAG(revenue) OVER (ORDER BY month) AS prev_revenue,
	ROUND(
		(revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0
		/ LAG(revenue) OVER (ORDER BY month), 1
	) AS growth_pct
FROM monthly
ORDER BY month;


-- 3. Doanh thu và số đơn theo ngày
SELECT
	o.order_time::date AS order_date,
	COUNT(DISTINCT o.order_id) AS total_orders,
	SUM(oi.quantity * oi.unit_price) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY 1
ORDER BY 1;


-- 4. Heatmap số đơn theo giờ x thứ (ISODOW: 1 = Thứ 2 ... 7 = Chủ nhật)
SELECT
	EXTRACT(ISODOW FROM order_time)::int AS weekday,
	EXTRACT(HOUR FROM order_time)::int AS hour,
	COUNT(*) AS total_orders
FROM orders
GROUP BY 1, 2
ORDER BY 1, 2;


-- 5. Top 10 món bán chạy (theo số lượng)
SELECT
	m.item_name,
	m.category,
	SUM(oi.quantity) AS qty_sold,
	SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN menu m ON m.item_id = oi.item_id
GROUP BY m.item_id, m.item_name, m.category
ORDER BY qty_sold DESC
LIMIT 10;


-- 6. Doanh thu vs biên lợi nhuận từng món
SELECT
	m.item_name,
	m.category,
	SUM(oi.quantity * oi.unit_price) AS revenue,
	SUM(oi.quantity * (oi.unit_price - oi.unit_cost)) AS gross_profit,
	ROUND(
		SUM(oi.quantity * (oi.unit_price - oi.unit_cost)) * 100.0
		/ SUM(oi.quantity * oi.unit_price), 1
	) AS margin_pct
FROM order_items oi
JOIN menu m ON m.item_id = oi.item_id
GROUP BY m.item_id, m.item_name, m.category
ORDER BY revenue DESC;


-- 7. So sánh chi nhánh
SELECT
	b.branch_name,
	COUNT(DISTINCT o.order_id) AS total_orders,
	SUM(oi.quantity * oi.unit_price) AS revenue,
	ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 0) AS aov,
	ROUND(
		SUM(oi.quantity * (oi.unit_price - oi.unit_cost)) * 100.0
		/ SUM(oi.quantity * oi.unit_price), 1
	) AS margin_pct
FROM branches b
JOIN orders o ON o.branch_id = b.branch_id
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY b.branch_id, b.branch_name
ORDER BY revenue DESC;


-- 8. Tỷ trọng doanh thu theo khung giờ
WITH slot_revenue AS (
	SELECT
		CASE
			WHEN EXTRACT(HOUR FROM o.order_time) < 11 THEN '1. Sáng (8-11h)'
			WHEN EXTRACT(HOUR FROM o.order_time) < 14 THEN '2. Trưa (11-14h)'
			WHEN EXTRACT(HOUR FROM o.order_time) < 18 THEN '3. Chiều (14-18h)'
			WHEN EXTRACT(HOUR FROM o.order_time) < 21 THEN '4. Tối (18-21h)'
			ELSE '5. Khuya (21h+)'
		END AS time_slot,
		SUM(oi.quantity * oi.unit_price) AS revenue
	FROM orders o
	JOIN order_items oi ON oi.order_id = o.order_id
	GROUP BY 1
)
SELECT
	time_slot,
	revenue,
	ROUND(revenue * 100.0 / SUM(revenue) OVER (), 1) AS share_pct
FROM slot_revenue
ORDER BY time_slot;
