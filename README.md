# F&B Chain Revenue Dashboard

Phân tích doanh thu của một chuỗi nhà hàng 3 chi nhánh (~50.000 đơn trong 180 ngày) bằng **PostgreSQL** và **Power BI**, nhằm trả lời 2 câu hỏi kinh doanh: *khách đến vào lúc nào* và *món nào thực sự sinh lời*.

![Tổng quan dashboard](images/dashboard.jpg)

## Kết quả tổng quan

| Doanh thu | Số đơn | AOV (giá trị TB/đơn) | Biên lợi nhuận gộp |
|---|---|---|---|
| **8,17 tỷ** | **50.000** | **163.445 đ** | **≈ 51%** |

## Insight chính

### 1. Khoảng 71% doanh thu đến từ 2 khung giờ cao điểm

![Heatmap số đơn theo thứ và giờ](images/heatmap.jpg)

- **Quan sát:** khung trưa **11–14h chiếm 37,8%** doanh thu và khung tối **18–21h chiếm 33,5%**. Đỉnh rơi vào 12h và 19h. Thứ 7 và Chủ nhật đông hơn ngày thường ở mọi khung giờ.
- **Ý nghĩa:** gần 3/4 doanh thu dồn vào khoảng 6 tiếng mỗi ngày. Nếu bếp và nhân sự không theo kịp ở các khung này, chuỗi mất khách đúng lúc khách đông nhất.
- **Đề xuất:**
  - Xếp ca nhân sự theo heatmap: tăng người từ 10h30 và 17h30, giảm người ở khung 14–17h.
  - Sơ chế và chuẩn bị sẵn các món bán chạy trước 11h và 18h để rút ngắn thời gian ra món.
  - Chạy khuyến mãi khung thấp điểm (14–17h, ví dụ combo đồ uống + tráng miệng) để tận dụng công suất bếp đang rảnh.

### 2. Combo cơm gà bán chạy nhất nhưng biên lợi nhuận thấp nhất

![Doanh thu và biên lợi nhuận theo món](images/scatter.jpg)

- **Quan sát:** Combo cơm gà dẫn đầu cả về số lượng (**≈ 20.000 phần**) lẫn doanh thu (**≈ 1,1 tỷ, 13% tổng doanh thu**), nhưng biên lợi nhuận chỉ **20%**, thấp nhất menu và thấp hơn nhiều so với mức trung bình ~51%. Ngược lại, đồ uống như trà sữa, trà đào, cà phê có biên **65–73%**.
- **Ý nghĩa:** món bán chạy nhất đang kéo biên lợi nhuận chung xuống. Nhưng đây có thể là món **kéo khách**, nên không nên bỏ.
- **Đề xuất:**
  - Tăng giá combo 3–5 nghìn đồng, hoặc điều chỉnh thành phần để giảm giá vốn mà không giảm cảm nhận của khách.
  - Đưa một đồ uống biên lợi nhuận cao vào combo (upsell), để nâng biên lợi nhuận của cả đơn.
  - Bước phân tích tiếp theo: so sánh AOV và biên lợi nhuận của **các đơn có Combo cơm gà** với các đơn không có, để xác định món này có thực sự kéo theo các món khác hay không.

### Insight phụ
- **Chi nhánh Quận 1** chiếm **≈ 50%** doanh thu, nhưng AOV và biên lợi nhuận của cả 3 chi nhánh gần như bằng nhau (~163k, ~51%). Khác biệt đến từ **lượng khách**, không phải từ hành vi mua.

## Công nghệ

- **PostgreSQL**: lưu trữ dữ liệu, viết 8 query phân tích (JOIN, GROUP BY, CTE, window function `LAG`, `SUM() OVER ()`, `CASE WHEN`)
- **Python** (`psycopg2`, `python-dotenv`): sinh dữ liệu giả lập và nạp hàng loạt vào DB
- **Power BI**: mô hình dữ liệu (star schema), measure DAX, dashboard

## Dữ liệu

Dữ liệu được **giả lập** bằng `seed.py`, dùng random có trọng số để giống thực tế:
- Trọng số theo **giờ** (cao điểm trưa và tối) và theo **ngày** (cuối tuần đông hơn)
- Trọng số theo **món** (độ phổ biến khác nhau) và theo **chi nhánh** (5 : 3 : 2)
- 3 kênh bán: tại chỗ, mang đi, giao hàng
- `random.seed(42)` để mỗi lần chạy ra cùng một bộ dữ liệu

| Bảng | Một dòng là | Cột chính |
|---|---|---|
| `branches` | 1 chi nhánh | branch_id, branch_name, district, opened_date |
| `menu` | 1 món | item_id, item_name, category, price, cost |
| `orders` | 1 hóa đơn | order_id, branch_id, order_time, channel |
| `order_items` | 1 món trong hóa đơn | order_id, item_id, quantity, unit_price, unit_cost |

`order_items` lưu `unit_price` và `unit_cost` **tại thời điểm bán**, nên doanh thu quá khứ không bị thay đổi khi menu đổi giá.

## Các query phân tích (`queries.sql`)

1. KPI tổng quan: doanh thu, số đơn, AOV
2. Tăng trưởng doanh thu theo tháng (`LAG`)
3. Doanh thu theo ngày
4. Heatmap số đơn theo thứ × giờ
5. Top 10 món bán chạy
6. Doanh thu và biên lợi nhuận từng món
7. So sánh chi nhánh
8. Tỷ trọng doanh thu theo khung giờ (`SUM() OVER ()`)

> Lưu ý: tháng 5 và tháng 11/2026 không đủ ngày (dữ liệu từ 22/05 đến 17/11), nên tăng trưởng của 2 tháng này không phản ánh xu hướng thật.

## Cách chạy

Yêu cầu: PostgreSQL, Python 3.10+, Power BI Desktop.

```bash
# 1. Tạo database và bảng
createdb fnb
psql -d fnb -f schema.sql

# 2. Cài thư viện
pip install psycopg2-binary python-dotenv

# 3. Tạo file .env ở thư mục gốc
#    DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/fnb

# 4. Sinh dữ liệu
python seed.py
```

Sau đó chạy `queries.sql` trong pgAdmin/psql, hoặc mở `fnb_dashboard.pbix` bằng Power BI Desktop và cập nhật thông tin kết nối.

## Cấu trúc thư mục

```
fnb-dashboard/
├── schema.sql           # Tạo 4 bảng
├── seed.py              # Sinh và nạp dữ liệu giả lập
├── queries.sql          # 8 query phân tích
├── fnb_dashboard.pbix   # File Power BI
└── images/              # Ảnh chụp dashboard
```
