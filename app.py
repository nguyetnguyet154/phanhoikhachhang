import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime
import re
import io


# =========================================================
# CẤU HÌNH TRANG
# =========================================================

st.set_page_config(
    page_title="CUSTOMER COMPLAINT RADAR",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main-title {
    font-size: 36px;
    font-weight: 800;
    color: #0f4c5c;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 17px;
    color: #666;
    margin-bottom: 25px;
}

.card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    margin-bottom: 15px;
}

.metric-box {
    background-color: #ffffff;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    text-align: center;
}

.metric-number {
    font-size: 30px;
    font-weight: bold;
    color: #0f4c5c;
}

.metric-label {
    color: #666;
    font-size: 14px;
}

.alert-critical {
    background-color: #ffe5e5;
    border-left: 6px solid #d00000;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
}

.alert-high {
    background-color: #fff0df;
    border-left: 6px solid #ff7800;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
}

.alert-medium {
    background-color: #fff9d9;
    border-left: 6px solid #e0b000;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
}

.alert-low {
    background-color: #e8f7ec;
    border-left: 6px solid #2e8b57;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
}

.small-text {
    color: #777;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# KẾT NỐI AIVEN MYSQL
# =========================================================

@st.cache_resource
def get_connection():

    cfg = st.secrets["mysql"]

    connection = pymysql.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        ssl={}
    )

    return connection


# =========================================================
# KIỂM TRA KẾT NỐI
# =========================================================

def test_connection():

    try:

        conn = get_connection()

        with conn.cursor() as cursor:

            cursor.execute("SELECT 1 AS test")
            result = cursor.fetchone()

        return result is not None

    except Exception as e:

        st.error("Không thể kết nối Aiven MySQL.")
        st.code(str(e))

        return False


# =========================================================
# TẠO DATABASE TABLE
# =========================================================

def init_database():

    conn = get_connection()

    sql = """
    CREATE TABLE IF NOT EXISTS complaints (

        id INT AUTO_INCREMENT PRIMARY KEY,

        complaint_code VARCHAR(30) UNIQUE NOT NULL,

        customer_name VARCHAR(150) NOT NULL,

        customer_email VARCHAR(150),

        service_type VARCHAR(100) NOT NULL,

        satisfaction INT NOT NULL,

        feedback TEXT NOT NULL,

        issue_type VARCHAR(100),

        severity VARCHAR(30),

        status VARCHAR(30) DEFAULT 'Chưa xử lý',

        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP

    )
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    """

    try:

        with conn.cursor() as cursor:

            cursor.execute(sql)

        conn.commit()

    except Exception as e:

        conn.rollback()
        raise e


# =========================================================
# MÃ PHẢN HỒI
# =========================================================

def generate_complaint_code():

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT id FROM complaints ORDER BY id DESC LIMIT 1"
            )

            result = cursor.fetchone()

        if result:

            next_id = result["id"] + 1

        else:

            next_id = 1

        return f"CR-{datetime.now().strftime('%Y%m%d')}-{next_id:04d}"

    except Exception:

        return f"CR-{datetime.now().strftime('%Y%m%d%H%M%S')}"


# =========================================================
# PHÂN LOẠI VẤN ĐỀ
# =========================================================

def classify_issue(feedback, service_type):

    text = (
        str(feedback).lower()
        + " "
        + str(service_type).lower()
    )

    categories = {

        "Chất lượng dịch vụ": [
            "dịch vụ",
            "phục vụ",
            "phục vụ chậm",
            "không chuyên nghiệp",
            "thái độ",
            "nhân viên",
            "staff",
            "service"
        ],

        "Lịch trình / Tour": [
            "tour",
            "lịch trình",
            "lịch",
            "điểm đến",
            "tham quan",
            "hướng dẫn viên",
            "hdv",
            "guide",
            "trễ giờ",
            "thời gian"
        ],

        "Khách sạn / Lưu trú": [
            "khách sạn",
            "phòng",
            "phòng ngủ",
            "resort",
            "check in",
            "check-in",
            "check out",
            "điều hòa",
            "máy lạnh",
            "vệ sinh phòng"
        ],

        "Vận chuyển": [
            "xe",
            "tài xế",
            "bus",
            "ô tô",
            "phương tiện",
            "đón",
            "đưa",
            "trễ chuyến",
            "chuyến bay",
            "máy bay"
        ],

        "Ăn uống": [
            "đồ ăn",
            "món ăn",
            "thức ăn",
            "nhà hàng",
            "bữa ăn",
            "buffet",
            "ăn uống",
            "thực phẩm"
        ],

        "Chi phí / Thanh toán": [
            "giá",
            "chi phí",
            "tiền",
            "thanh toán",
            "hóa đơn",
            "phí",
            "đắt",
            "hoàn tiền",
            "refund"
        ],

        "Sự kiện / Teambuilding": [
            "teambuilding",
            "team building",
            "sự kiện",
            "event",
            "mc",
            "trò chơi",
            "game",
            "âm thanh",
            "sân khấu",
            "gala",
            "chương trình"
        ]

    }

    best_category = "Khác"
    best_score = 0

    for category, keywords in categories.items():

        score = 0

        for keyword in keywords:

            if keyword in text:

                score += 1

        if score > best_score:

            best_score = score
            best_category = category

    return best_category


# =========================================================
# XÁC ĐỊNH MỨC ĐỘ CẢNH BÁO
# =========================================================

def calculate_severity(satisfaction, feedback):

    text = str(feedback).lower()

    critical_keywords = [
        "ngộ độc",
        "tai nạn",
        "bị thương",
        "thương tích",
        "mất an toàn",
        "lừa đảo",
        "gian lận",
        "đe dọa",
        "khẩn cấp",
        "nguy hiểm"
    ]

    high_keywords = [
        "rất tệ",
        "quá tệ",
        "thất vọng",
        "không bao giờ",
        "sẽ không quay lại",
        "yêu cầu hoàn tiền",
        "hoàn tiền",
        "khiếu nại",
        "bức xúc",
        "tệ",
        "phàn nàn"
    ]

    medium_keywords = [
        "không hài lòng",
        "chậm",
        "thiếu",
        "sai",
        "không tốt",
        "bất tiện",
        "vấn đề",
        "không ổn"
    ]

    if any(keyword in text for keyword in critical_keywords):

        return "Khẩn cấp"

    if satisfaction <= 2:

        return "Cao"

    if any(keyword in text for keyword in high_keywords):

        return "Cao"

    if satisfaction == 3:

        return "Trung bình"

    if any(keyword in text for keyword in medium_keywords):

        return "Trung bình"

    return "Thấp"


# =========================================================
# THÊM PHẢN HỒI
# =========================================================

def insert_complaint(
    customer_name,
    customer_email,
    service_type,
    satisfaction,
    feedback
):

    conn = get_connection()

    complaint_code = generate_complaint_code()

    issue_type = classify_issue(
        feedback,
        service_type
    )

    severity = calculate_severity(
        satisfaction,
        feedback
    )

    sql = """
    INSERT INTO complaints
    (
        complaint_code,
        customer_name,
        customer_email,
        service_type,
        satisfaction,
        feedback,
        issue_type,
        severity,
        status
    )
    VALUES
    (
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        'Chưa xử lý'
    )
    """

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                sql,
                (
                    complaint_code,
                    customer_name,
                    customer_email,
                    service_type,
                    satisfaction,
                    feedback,
                    issue_type,
                    severity
                )
            )

        conn.commit()

        return complaint_code, issue_type, severity

    except Exception as e:

        conn.rollback()

        raise e


# =========================================================
# LẤY TOÀN BỘ DỮ LIỆU
# =========================================================

def get_complaints():

    conn = get_connection()

    sql = """
    SELECT
        id,
        complaint_code,
        customer_name,
        customer_email,
        service_type,
        satisfaction,
        feedback,
        issue_type,
        severity,
        status,
        created_at,
        updated_at
    FROM complaints
    ORDER BY created_at DESC
    """

    try:

        with conn.cursor() as cursor:

            cursor.execute(sql)

            data = cursor.fetchall()

        return pd.DataFrame(data)

    except Exception as e:

        st.error(f"Lỗi lấy dữ liệu: {e}")

        return pd.DataFrame()


# =========================================================
# CẬP NHẬT TRẠNG THÁI
# =========================================================

def update_status(complaint_id, new_status):

    conn = get_connection()

    sql = """
    UPDATE complaints
    SET
        status = %s,
        updated_at = NOW()
    WHERE id = %s
    """

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                sql,
                (new_status, complaint_id)
            )

        conn.commit()

        return True

    except Exception as e:

        conn.rollback()

        st.error(f"Lỗi cập nhật: {e}")

        return False


# =========================================================
# KHỞI TẠO DATABASE
# =========================================================

try:

    init_database()

except Exception as e:

    st.error("❌ Không thể khởi tạo cơ sở dữ liệu Aiven MySQL.")

    st.code(str(e))

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    try:

        st.image(
            "VT3.jpg",
            use_container_width=True
        )

    except Exception:

        st.markdown("## 🚨 CUSTOMER COMPLAINT RADAR")

    st.markdown("---")

    st.markdown(
        "### 🚨 CUSTOMER COMPLAINT RADAR"
    )

    st.caption(
        "Hệ thống phân tích và cảnh báo "
        "vấn đề chất lượng dịch vụ từ phản hồi khách hàng."
    )

    st.markdown("---")

    menu = st.radio(
        "MENU",
        [
            "🏠 Tổng quan",
            "📝 Gửi phản hồi",
            "🔎 Tra cứu phản hồi",
            "🚨 Cảnh báo chất lượng",
            "📊 Phân tích dữ liệu",
            "⚙️ Kiểm tra hệ thống"
        ]
    )

    st.markdown("---")

    st.caption(
        "TADIVIVU TRAVEL\n\n"
        "Customer Service Intelligence"
    )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🚨 CUSTOMER COMPLAINT RADAR</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Xây dựng hệ thống phân tích và cảnh báo vấn đề chất lượng dịch vụ từ phản hồi khách hàng'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# LOAD DATA
# =========================================================

df = get_complaints()


# =========================================================
# TRANG TỔNG QUAN
# =========================================================

if menu == "🏠 Tổng quan":

    st.subheader("📌 Tổng quan chất lượng dịch vụ")

    if df.empty:

        st.info(
            "Chưa có dữ liệu phản hồi khách hàng. "
            "Hãy vào mục **Gửi phản hồi** để tạo dữ liệu."
        )

    else:

        total = len(df)

        unresolved = len(
            df[df["status"] == "Chưa xử lý"]
        )

        high_alert = len(
            df[
                df["severity"].isin(
                    ["Cao", "Khẩn cấp"]
                )
            ]
        )

        average_rating = round(
            df["satisfaction"].mean(),
            2
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-number">{total}</div>
                    <div class="metric-label">Tổng phản hồi</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-number">{unresolved}</div>
                    <div class="metric-label">Chưa xử lý</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-number">{high_alert}</div>
                    <div class="metric-label">Cảnh báo cao</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col4:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-number">{average_rating}/5</div>
                    <div class="metric-label">Điểm hài lòng TB</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("📊 Phân bố mức độ cảnh báo")

            severity_count = (
                df["severity"]
                .value_counts()
                .reindex(
                    [
                        "Khẩn cấp",
                        "Cao",
                        "Trung bình",
                        "Thấp"
                    ],
                    fill_value=0
                )
            )

            st.bar_chart(severity_count)

        with col2:

            st.subheader("📂 Nhóm vấn đề")

            issue_count = (
                df["issue_type"]
                .value_counts()
            )

            st.bar_chart(issue_count)

        st.markdown("---")

        st.subheader("🕐 Phản hồi gần đây")

        recent = df.head(10).copy()

        display_columns = [
            "complaint_code",
            "customer_name",
            "service_type",
            "satisfaction",
            "issue_type",
            "severity",
            "status",
            "created_at"
        ]

        st.dataframe(
            recent[display_columns],
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# GỬI PHẢN HỒI
# =========================================================

elif menu == "📝 Gửi phản hồi":

    st.subheader("📝 Gửi phản hồi khách hàng")

    st.info(
        "Thông tin phản hồi sẽ được hệ thống tự động "
        "phân loại vấn đề và xác định mức độ cảnh báo."
    )

    with st.form("feedback_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:

            customer_name = st.text_input(
                "Họ và tên *",
                placeholder="Nhập họ tên khách hàng"
            )

        with col2:

            customer_email = st.text_input(
                "Email",
                placeholder="example@email.com"
            )

        service_type = st.selectbox(
            "Loại dịch vụ *",
            [
                "Tour du lịch",
                "Teambuilding",
                "Sự kiện",
                "Khách sạn / Resort",
                "Vận chuyển",
                "Vé máy bay",
                "Visa",
                "Dịch vụ khác"
            ]
        )

        satisfaction = st.slider(
            "Mức độ hài lòng",
            min_value=1,
            max_value=5,
            value=5,
            help="1 = Rất không hài lòng, 5 = Rất hài lòng"
        )

        satisfaction_text = {
            1: "😡 Rất không hài lòng",
            2: "😞 Không hài lòng",
            3: "😐 Bình thường",
            4: "🙂 Hài lòng",
            5: "😄 Rất hài lòng"
        }

        st.write(
            f"Đánh giá: **{satisfaction_text[satisfaction]}**"
        )

        feedback = st.text_area(
            "Nội dung phản hồi *",
            placeholder=(
                "Ví dụ: Nhân viên phục vụ chậm, "
                "lịch trình tour bị trễ..."
            ),
            height=180
        )

        submitted = st.form_submit_button(
            "🚀 GỬI PHẢN HỒI",
            use_container_width=True
        )

    if submitted:

        if not customer_name.strip():

            st.error("Vui lòng nhập họ tên khách hàng.")

        elif not feedback.strip():

            st.error("Vui lòng nhập nội dung phản hồi.")

        elif customer_email and not re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            customer_email
        ):

            st.error("Email không hợp lệ.")

        else:

            try:

                code, issue, severity = insert_complaint(
                    customer_name.strip(),
                    customer_email.strip(),
                    service_type,
                    satisfaction,
                    feedback.strip()
                )

                st.success(
                    f"Đã ghi nhận phản hồi thành công! "
                    f"Mã phản hồi: **{code}**"
                )

                st.markdown("### 🤖 Kết quả phân tích tự động")

                col1, col2 = st.columns(2)

                with col1:

                    st.info(
                        f"📂 Nhóm vấn đề: **{issue}**"
                    )

                with col2:

                    if severity == "Khẩn cấp":

                        st.error(
                            f"🚨 Mức cảnh báo: **{severity}**"
                        )

                    elif severity == "Cao":

                        st.warning(
                            f"⚠️ Mức cảnh báo: **{severity}**"
                        )

                    elif severity == "Trung bình":

                        st.warning(
                            f"🟡 Mức cảnh báo: **{severity}**"
                        )

                    else:

                        st.success(
                            f"🟢 Mức cảnh báo: **{severity}**"
                        )

            except Exception as e:

                st.error(
                    "Không thể lưu phản hồi vào cơ sở dữ liệu."
                )

                st.code(str(e))


# =========================================================
# TRA CỨU PHẢN HỒI
# =========================================================

elif menu == "🔎 Tra cứu phản hồi":

    st.subheader("🔎 Tra cứu phản hồi khách hàng")

    if df.empty:

        st.info("Chưa có dữ liệu.")

    else:

        col1, col2, col3 = st.columns(3)

        with col1:

            search = st.text_input(
                "🔍 Tìm kiếm",
                placeholder="Tên, mã phản hồi, nội dung..."
            )

        with col2:

            severity_filter = st.selectbox(
                "Mức cảnh báo",
                [
                    "Tất cả",
                    "Khẩn cấp",
                    "Cao",
                    "Trung bình",
                    "Thấp"
                ]
            )

        with col3:

            status_filter = st.selectbox(
                "Trạng thái",
                [
                    "Tất cả",
                    "Chưa xử lý",
                    "Đang xử lý",
                    "Đã xử lý"
                ]
            )

        filtered = df.copy()

        if search:

            search = search.lower()

            mask = (
                filtered.astype(str)
                .apply(
                    lambda row:
                    row.str.lower().str.contains(
                        search,
                        na=False
                    ).any(),
                    axis=1
                )
            )

            filtered = filtered[mask]

        if severity_filter != "Tất cả":

            filtered = filtered[
                filtered["severity"] == severity_filter
            ]

        if status_filter != "Tất cả":

            filtered = filtered[
                filtered["status"] == status_filter
            ]

        st.write(
            f"**Tìm thấy {len(filtered)} phản hồi**"
        )

        if filtered.empty:

            st.warning("Không tìm thấy dữ liệu phù hợp.")

        else:

            st.dataframe(
                filtered[
                    [
                        "complaint_code",
                        "customer_name",
                        "customer_email",
                        "service_type",
                        "satisfaction",
                        "feedback",
                        "issue_type",
                        "severity",
                        "status",
                        "created_at"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# CẢNH BÁO CHẤT LƯỢNG
# =========================================================

elif menu == "🚨 Cảnh báo chất lượng":

    st.subheader("🚨 Trung tâm cảnh báo chất lượng")

    if df.empty:

        st.success(
            "Hiện chưa có phản hồi nào cần cảnh báo."
        )

    else:

        alerts = df[
            df["severity"].isin(
                ["Khẩn cấp", "Cao", "Trung bình"]
            )
        ].copy()

        if alerts.empty:

            st.success(
                "🎉 Hiện không có cảnh báo chất lượng."
            )

        else:

            st.write(
                f"Có **{len(alerts)}** phản hồi cần theo dõi."
            )

            for _, row in alerts.iterrows():

                severity = row["severity"]

                if severity == "Khẩn cấp":

                    css_class = "alert-critical"
                    icon = "🚨"

                elif severity == "Cao":

                    css_class = "alert-high"
                    icon = "🔴"

                else:

                    css_class = "alert-medium"
                    icon = "🟡"

                st.markdown(
                    f"""
                    <div class="{css_class}">
                        <strong>{icon} {severity}</strong><br>
                        <b>Mã:</b> {row["complaint_code"]}<br>
                        <b>Khách hàng:</b> {row["customer_name"]}<br>
                        <b>Dịch vụ:</b> {row["service_type"]}<br>
                        <b>Vấn đề:</b> {row["issue_type"]}<br>
                        <b>Mức hài lòng:</b> {row["satisfaction"]}/5<br>
                        <b>Nội dung:</b> {row["feedback"]}<br>
                        <b>Trạng thái:</b> {row["status"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                col1, col2 = st.columns([3, 1])

                with col1:

                    new_status = st.selectbox(
                        "Cập nhật trạng thái",
                        [
                            "Chưa xử lý",
                            "Đang xử lý",
                            "Đã xử lý"
                        ],
                        index=[
                            "Chưa xử lý",
                            "Đang xử lý",
                            "Đã xử lý"
                        ].index(row["status"])
                        if row["status"]
                        in [
                            "Chưa xử lý",
                            "Đang xử lý",
                            "Đã xử lý"
                        ]
                        else 0,
                        key=f"status_{row['id']}"
                    )

                with col2:

                    if st.button(
                        "💾 Cập nhật",
                        key=f"update_{row['id']}"
                    ):

                        if update_status(
                            row["id"],
                            new_status
                        ):

                            st.success(
                                "Đã cập nhật trạng thái."
                            )

                            st.rerun()

                st.markdown("---")


# =========================================================
# PHÂN TÍCH DỮ LIỆU
# =========================================================

elif menu == "📊 Phân tích dữ liệu":

    st.subheader("📊 Phân tích chất lượng dịch vụ")

    if df.empty:

        st.info(
            "Chưa có dữ liệu để phân tích."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("### ⭐ Mức độ hài lòng")

            rating = (
                df["satisfaction"]
                .value_counts()
                .sort_index()
            )

            st.bar_chart(rating)

        with col2:

            st.markdown("### 🚨 Mức độ cảnh báo")

            severity = (
                df["severity"]
                .value_counts()
            )

            st.bar_chart(severity)

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("### 📂 Vấn đề thường gặp")

            issue = (
                df["issue_type"]
                .value_counts()
                .head(10)
            )

            st.bar_chart(issue)

        with col2:

            st.markdown("### 🏨 Phản hồi theo dịch vụ")

            service = (
                df["service_type"]
                .value_counts()
            )

            st.bar_chart(service)

        st.markdown("---")

        st.subheader("📈 Chỉ số chất lượng")

        total = len(df)

        satisfied = len(
            df[
                df["satisfaction"] >= 4
            ]
        )

        high_alert = len(
            df[
                df["severity"].isin(
                    ["Cao", "Khẩn cấp"]
                )
            ]
        )

        satisfaction_rate = (
            satisfied / total * 100
            if total > 0
            else 0
        )

        alert_rate = (
            high_alert / total * 100
            if total > 0
            else 0
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Tỷ lệ khách hài lòng",
                f"{satisfaction_rate:.1f}%"
            )

        with col2:

            st.metric(
                "Tỷ lệ cảnh báo cao",
                f"{alert_rate:.1f}%"
            )

        with col3:

            st.metric(
                "Điểm hài lòng trung bình",
                f"{df['satisfaction'].mean():.2f}/5"
            )

        st.markdown("---")

        st.subheader("📥 Xuất dữ liệu")

        csv = df.to_csv(
            index=False,
            encoding="utf-8-sig"
        )

        st.download_button(
            label="⬇️ Tải dữ liệu CSV",
            data=csv,
            file_name=(
                f"customer_complaints_"
                f"{datetime.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv",
            use_container_width=True
        )


# =========================================================
# KIỂM TRA HỆ THỐNG
# =========================================================

elif menu == "⚙️ Kiểm tra hệ thống":

    st.subheader("⚙️ Kiểm tra hệ thống")

    st.markdown(
        """
        <div class="card">
            <h3>🔌 Aiven MySQL</h3>
            <p>
            Kiểm tra kết nối giữa Streamlit và cơ sở dữ liệu Aiven.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🔄 KIỂM TRA KẾT NỐI",
        use_container_width=True
    ):

        try:

            if test_connection():

                st.success(
                    "✅ Kết nối Aiven MySQL thành công!"
                )

                st.write(
                    "Database: **defaultdb**"
                )

                st.write(
                    f"Số phản hồi hiện tại: **{len(df)}**"
                )

        except Exception as e:

            st.error(
                "❌ Kết nối thất bại."
            )

            st.code(str(e))

    st.markdown("---")

    st.subheader("🗄️ Thông tin cơ sở dữ liệu")

    try:

        cfg = st.secrets["mysql"]

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Host:** `{cfg['host']}`"
            )

            st.write(
                f"**Port:** `{cfg['port']}`"
            )

        with col2:

            st.write(
                f"**User:** `{cfg['user']}`"
            )

            st.write(
                f"**Database:** `{cfg['database']}`"
            )

        st.success(
            "🔐 Password đang được lấy từ Streamlit Secrets."
        )

    except Exception as e:

        st.error(
            "Không tìm thấy cấu hình Streamlit Secrets."
        )

        st.code(str(e))


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "CUSTOMER COMPLAINT RADAR © 2026 | "
    "Hệ thống hỗ trợ phân tích và cảnh báo chất lượng dịch vụ"
)
