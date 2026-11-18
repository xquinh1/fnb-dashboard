import os
import random
import sys
from datetime import datetime, timedelta

import psycopg2
from dotenv import load_dotenv

N_ORDERS = 50000
DAYS = 180
random.seed(42)  # cố định để mỗi lần chạy ra cùng một bộ dữ liệu

# (branch_name, district, opened_date)
BRANCHES = [
    ("Chi nhánh Quận 1", "Quận 1, Hồ Chí Minh", "2022-03-15"),
    ("Chi nhánh Cầu Giấy", "Cầu Giấy, Hà Nội", "2023-01-10"),
    ("Chi nhánh Hải Châu", "Hải Châu, Đà Nẵng", "2023-08-20"),
]
BRANCH_WEIGHTS = [5, 3, 2]

# (item_name, category, price, cost, trọng số độ phổ biến)
MENU = [
    ("Combo cơm gà", "Cơm", 55000, 44000, 14),
    ("Cơm sườn nướng", "Cơm", 60000, 33000, 9),
    ("Cơm bò lúc lắc", "Cơm", 75000, 42000, 6),
    ("Phở bò", "Phở/Bún", 65000, 30000, 10),
    ("Bún chả", "Phở/Bún", 60000, 28000, 7),
    ("Bún bò Huế", "Phở/Bún", 60000, 29000, 6),
    ("Mì xào hải sản", "Mì", 70000, 38000, 4),
    ("Gỏi cuốn", "Khai vị", 35000, 14000, 5),
    ("Chả giò", "Khai vị", 40000, 15000, 5),
    ("Salad trộn", "Khai vị", 45000, 18000, 3),
    ("Trà đào", "Đồ uống", 30000, 8000, 9),
    ("Trà sữa trân châu", "Đồ uống", 35000, 11000, 10),
    ("Cà phê sữa", "Đồ uống", 25000, 7000, 11),
    ("Nước cam ép", "Đồ uống", 35000, 14000, 5),
    ("Sinh tố bơ", "Đồ uống", 40000, 17000, 4),
    ("Chè khúc bạch", "Tráng miệng", 30000, 12000, 3),
    ("Bánh flan", "Tráng miệng", 20000, 6000, 4),
    ("Kem dừa", "Tráng miệng", 35000, 13000, 2),
]
MENU_WEIGHTS = [m[4] for m in MENU]

CHANNELS = ["dine_in", "takeaway", "delivery"]
CHANNEL_WEIGHTS = [5, 2, 3]

HOUR_WEIGHTS = {
    8: 2, 9: 2, 10: 3, 11: 10, 12: 12, 13: 6, 14: 2,
    15: 2, 16: 3, 17: 5, 18: 9, 19: 10, 20: 6, 21: 2,
}
HOURS = list(HOUR_WEIGHTS)
HOUR_W = list(HOUR_WEIGHTS.values())


def random_datetime(today: datetime) -> datetime:
    while True:
        d = today - timedelta(days=random.randint(1, DAYS))
        weekend = d.weekday() >= 5
        if weekend or random.random() < 0.7:  # ngày thường bị loại 30% -> cuối tuần đông hơn
            h = random.choices(HOURS, weights=HOUR_W)[0]
            return d.replace(hour=h, minute=random.randint(0, 59), second=random.randint(0, 59))


def main() -> None:
    load_dotenv()
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("DATABASE_URL is not set")

    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    # Xóa dữ liệu cũ và reset SERIAL về 1 -> chạy lại bao nhiêu lần cũng được
    cur.execute("TRUNCATE order_items, orders, menu, branches RESTART IDENTITY CASCADE")

    cur.executemany(
        "INSERT INTO branches(branch_name, district, opened_date) VALUES (%s, %s, %s)",
        BRANCHES,
    )
    cur.executemany(
        "INSERT INTO menu(item_name, category, price, cost) VALUES (%s, %s, %s, %s)",
        [(n, c, p, k) for n, c, p, k, _ in MENU],
    )

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    o_id, o_branch, o_time, o_channel = [], [], [], []
    i_id, i_order, i_item, i_qty, i_price, i_cost = [], [], [], [], [], []
    order_item_id = 1

    for oid in range(1, N_ORDERS + 1):
        branch_id = random.choices(range(1, len(BRANCHES) + 1), weights=BRANCH_WEIGHTS)[0]
        ts = random_datetime(today).strftime("%Y-%m-%d %H:%M:%S")
        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
        picked = set()
        for _ in range(random.randint(1, 4)):
            mi = random.choices(range(len(MENU)), weights=MENU_WEIGHTS)[0]
            if mi in picked:
                continue
            picked.add(mi)
            i_id.append(order_item_id)
            i_order.append(oid)
            i_item.append(mi + 1)  # item_id trong DB bắt đầu từ 1
            i_qty.append(random.randint(1, 2))
            i_price.append(MENU[mi][2])
            i_cost.append(MENU[mi][3])
            order_item_id += 1
        o_id.append(oid)
        o_branch.append(branch_id)
        o_time.append(ts)
        o_channel.append(channel)

    cur.execute(
        """INSERT INTO orders(order_id, branch_id, order_time, channel)
           SELECT * FROM unnest(%s::int[], %s::int[], %s::timestamp[], %s::varchar[])""",
        (o_id, o_branch, o_time, o_channel),
    )

    chunk = 20000
    for s in range(0, len(i_id), chunk):
        e = s + chunk
        cur.execute(
            """INSERT INTO order_items(order_item_id, order_id, item_id, quantity, unit_price, unit_cost)
               SELECT * FROM unnest(%s::int[], %s::int[], %s::int[], %s::int[], %s::numeric[], %s::numeric[])""",
            (i_id[s:e], i_order[s:e], i_item[s:e], i_qty[s:e], i_price[s:e], i_cost[s:e]),
        )

    # Tự chèn id nên phải đẩy sequence của SERIAL lên theo, nếu không lần INSERT sau sẽ trùng khóa
    cur.execute("SELECT setval(pg_get_serial_sequence('orders', 'order_id'), (SELECT MAX(order_id) FROM orders))")
    cur.execute("SELECT setval(pg_get_serial_sequence('order_items', 'order_item_id'), (SELECT MAX(order_item_id) FROM order_items))")

    conn.commit()

    cur.execute("SELECT (SELECT COUNT(*) FROM orders), (SELECT COUNT(*) FROM order_items)")
    orders, items = cur.fetchone()
    print(f"Xong: {orders} orders, {items} order_items")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
