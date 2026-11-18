-- Schema cho dashboard doanh thu chuỗi F&B
-- Thứ tự tạo bảng: bảng được tham chiếu (branches, menu) phải có trước

CREATE TABLE IF NOT EXISTS branches (
    branch_id    SERIAL PRIMARY KEY,
    branch_name  VARCHAR(100) NOT NULL,
    district     VARCHAR(100),
    opened_date  DATE
);

CREATE TABLE IF NOT EXISTS menu (
    item_id      SERIAL PRIMARY KEY,
    item_name    VARCHAR(100) NOT NULL,
    category     VARCHAR(50),
    price        NUMERIC(12,2) NOT NULL,  -- giá bán
    cost         NUMERIC(12,2) NOT NULL   -- giá vốn
);

-- 1 dòng = 1 hóa đơn
CREATE TABLE IF NOT EXISTS orders (
    order_id     SERIAL PRIMARY KEY,
    branch_id    INT NOT NULL REFERENCES branches(branch_id),
    order_time   TIMESTAMP NOT NULL,
    channel      VARCHAR(20)              -- dine_in, takeaway, delivery
);

-- 1 dòng = 1 món trong hóa đơn
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id      INT NOT NULL REFERENCES orders(order_id),
    item_id       INT NOT NULL REFERENCES menu(item_id),
    quantity      INT NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(12,2) NOT NULL, -- giá tại thời điểm bán
    unit_cost     NUMERIC(12,2) NOT NULL  -- giá vốn tại thời điểm bán
);
