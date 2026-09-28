import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime

# =========================================================
# CẤU HÌNH
# =========================================================

st.set_page_config(
    page_title="Customer Complaint Radar",
    page_icon="🚨",
    layout="wide"
)

# =========================================================
# MYSQL AIVEN
# =========================================================

MYSQL_HOST = "mysql-29a6db25-tranthikimnguyet8-df0c.i.aivencloud.com"
MYSQL_PORT = 19586
MYSQL_USER = "avnadmin"
MYSQL_PASSWORD = "AVNS_6y8qIYGcoOj22F0rJKB"
MYSQL_DATABASE = "defaultdb"


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #f7f9fc;
}

.block-container {
    padding-top: 1.5rem;
}

.header-box {
    background: linear-gradient(135deg, #0f4c81, #1976d2);
    padding: 28px;
    border-radius: 15px;
    color: white;
    margin-bottom: 25px;
}

.header-title {
    font-size: 32px;
    font-weight: bold;
}

.header-subtitle {
    font-size: 16px;
    margin-top: 8px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.metric-number {
    font-size: 30px;
    font-weight: bold;
    color: #0f4c81;
}

.metric-label {
    color: #666;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# KẾT NỐI MYSQL
# =========================================================

def get_connection():

    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=20,
        ssl={}
    )

    return connection


# =========================================================
# TẠO BẢNG
# =========================================================

def init_database():

    connection = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        sql = """
        CREATE TABLE IF NOT EXISTS complaints (
            id INT AUTO_INCREMENT PRIMARY KEY,
            complaint_code VARCHAR(20) NOT NULL UNIQUE,
            created_at DATETIME NOT NULL,
            customer_name VARCHAR(150) NOT NULL,
            email VARCHAR(150) NOT NULL,
            service VARCHAR(100) NOT NULL,
            satisfaction INT NOT NULL,
            feedback_type VARCHAR(50),
            issue_type VARCHAR(100),
            alert_level VARCHAR(50),
            content TEXT,
            status VARCHAR(50) DEFAULT 'Chưa xử lý',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        """

        cursor.execute(sql)

        connection.commit()

        cursor.close()
        connection.close()

        return True, ""

    except Exception as e:

        if connection:
            connection.close()

        return False, str(e)


# =========================================================
# TẠO MÃ PHẢN HỒI
# =========================================================

def generate_complaint_code():

    connection = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT COUNT(*) AS total FROM complaints"
        )

        result = cursor.fetchone()

        cursor.close()
        connection.close()

        number = int(result["total"]) + 1

        return f"CB{number:04d}"

    except Exception:

        if connection:
            connection.close()

        return "CB0001"


# =========================================================
# LẤY DỮ LIỆU
# =========================================================

def get_complaints():

    connection = None

    try:

        connection = get_connection()

        sql = """
        SELECT
            id,
            complaint_code AS `Mã phản hồi`,
            created_at AS `Thời gian`,
            customer_name AS `Họ tên`,
            email AS `Email`,
            service AS `Dịch vụ`,
            satisfaction AS `Mức hài lòng`,
            feedback_type AS `Loại phản hồi`,
            issue_type AS `Loại vấn đề`,
            alert_level AS `Mức cảnh báo`,
            content AS `Nội dung`,
            status AS `Trạng thái`,
            updated_at AS `Cập nhật`
        FROM complaints
        ORDER BY created_at DESC
        """

        df = pd.read_sql(sql, connection)

        connection.close()

        return df

    except Exception as e:

        if connection:
            connection.close()

        st.error(f"Lỗi MySQL: {e}")

        return pd.DataFrame()


# =========================================================
# THÊM PHẢN HỒI
# =========================================================

def insert_complaint(
    name,
    email,
    service,
    satisfaction,
    feedback_type,
    issue,
    alert,
    content
):

    connection = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        code = generate_complaint_code()
        now = datetime.now()

        sql = """
        INSERT INTO complaints (
            complaint_code,
            created_at,
            customer_name,
            email,
            service,
            satisfaction,
            feedback_type,
            issue_type,
            alert_level,
            content,
            status,
            updated_at
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """

        values = (
            code,
            now,
            name,
            email,
            service,
            satisfaction,
            feedback_type,
            issue,
            alert,
            content,
            "Chưa xử lý",
            now
        )

        cursor.execute(sql, values)

        connection.commit()

        cursor.close()
        connection.close()

        return True, code

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return False, str(e)


# =========================================================
# CẬP NHẬT TRẠNG THÁI
# =========================================================

def update_status(complaint_id, new_status):

    connection = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        sql = """
        UPDATE complaints
        SET
            status = %s,
            updated_at = %s
        WHERE id = %s
        """

        cursor.execute(
            sql,
            (
                new_status,
                datetime.now(),
                complaint_id
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return True

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        st.error(f"Lỗi cập nhật: {e}")

        return False


# =========================================================
# PHÂN LOẠI VẤN ĐỀ
# =========================================================

def classify_issue(text):

    text = text.lower()

    categories = {

        "Phòng nghỉ": [
            "phòng",
            "vệ sinh",
            "giường",
            "máy lạnh",
            "điều hòa",
            "toilet",
            "nhà vệ sinh",
            "khách sạn"
        ],

        "Nhân viên": [
            "nhân viên",
            "phục vụ",
            "thái độ",
            "ứng xử",
            "hướng dẫn viên",
            "hdv"
        ],

        "Lịch trình": [
            "lịch trình",
            "thời gian",
            "trễ",
            "chậm",
            "điểm tham quan"
        ],

        "Vận chuyển": [
            "xe",
            "tài xế",
            "đưa đón",
            "xe bus",
            "ô tô",
            "máy bay"
        ],

        "Ẩm thực": [
            "đồ ăn",
            "thức ăn",
            "món ăn",
            "nhà hàng",
            "bữa ăn",
            "buffet"
        ],

        "Thanh toán": [
            "thanh toán",
            "giá",
            "chi phí",
            "tiền",
            "hóa đơn",
            "phí"
        ]
    }

    for category, keywords in categories.items():

        for keyword in keywords:

            if keyword in text:
                return category

    return "Khác"


# =========================================================
# XÁC ĐỊNH MỨC CẢNH BÁO
# =========================================================

def calculate_alert(text, satisfaction):

    text = text.lower()

    critical_words = [
        "nguy hiểm",
        "tai nạn",
        "mất đồ",
        "bị mất",
        "ngộ độc",
        "thương tích",
        "đe dọa",
        "không an toàn"
    ]

    high_words = [
        "rất tệ",
        "không hài lòng",
        "quá tệ",
        "trễ hơn",
        "chậm hơn",
        "bẩn",
        "hỏng",
        "sai",
        "kém"
    ]

    for word in critical_words:

        if word in text:
            return "Khẩn cấp"

    if satisfaction <= 1:
        return "Khẩn cấp"

    for word in high_words:

        if word in text:
            return "Cao"

    if satisfaction == 2:
        return "Cao"

    if satisfaction == 3:
        return "Trung bình"

    return "Thấp"


# =========================================================
# KHỞI TẠO DATABASE
# =========================================================

db_ok, db_error = init_database()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    try:
        st.image(
            "VT3.jpg",
            use_container_width=True
        )
    except:
        st.warning("Không tìm thấy VT3.jpg")

    st.markdown(
        "## 🚨 Customer Complaint Radar"
    )

    st.caption(
        "Hệ thống phân tích và cảnh báo "
        "vấn đề chất lượng dịch vụ từ phản hồi khách hàng."
    )

    st.divider()

    page = st.radio(
        "MENU",
        [
            "🏠 Tổng quan",
            "📝 Gửi phản hồi",
            "🔎 Tra cứu phản hồi",
            "🚨 Cảnh báo chất lượng",
            "📊 Phân tích dữ liệu"
        ]
    )

    st.divider()

    if db_ok:
        st.success("🟢 MySQL đang kết nối")
    else:
        st.error("🔴 MySQL chưa kết nối")


# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="header-box">

    <div class="header-title">
        🚨 CUSTOMER COMPLAINT RADAR
    </div>

    <div class="header-subtitle">
        Xây dựng hệ thống phân tích và cảnh báo
        vấn đề chất lượng dịch vụ từ phản hồi khách hàng
    </div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# KIỂM TRA MYSQL
# =========================================================

if not db_ok:

    st.error(
        "Không thể kết nối đến MySQL Aiven."
    )

    st.code(db_error)

    st.stop()


# =========================================================
# TỔNG QUAN
# =========================================================

if page == "🏠 Tổng quan":

    df = get_complaints()

    st.subheader("📊 Tổng quan chất lượng dịch vụ")

    total = len(df)

    critical = len(
        df[df["Mức cảnh báo"] == "Khẩn cấp"]
    )

    high = len(
        df[df["Mức cảnh báo"] == "Cao"]
    )

    unresolved = len(
        df[df["Trạng thái"] != "Đã xử lý"]
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{total}</div>
                <div class="metric-label">
                    Tổng phản hồi
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{critical}</div>
                <div class="metric-label">
                    Khẩn cấp
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{high}</div>
                <div class="metric-label">
                    Mức cao
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{unresolved}</div>
                <div class="metric-label">
                    Chưa xử lý
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 📈 Phân tích")

    if len(df) > 0:

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("#### 📌 Vấn đề thường gặp")

            issue_count = df[
                "Loại vấn đề"
            ].value_counts()

            st.bar_chart(issue_count)

        with col2:

            st.markdown("#### 🚨 Mức cảnh báo")

            alert_count = df[
                "Mức cảnh báo"
            ].value_counts()

            st.bar_chart(alert_count)

    st.markdown(
        "### 🚨 Phản hồi cần ưu tiên"
    )

    warning_df = df[
        df["Mức cảnh báo"].isin(
            ["Khẩn cấp", "Cao"]
        )
    ]

    if len(warning_df) > 0:

        st.dataframe(
            warning_df[
                [
                    "Mã phản hồi",
                    "Thời gian",
                    "Họ tên",
                    "Dịch vụ",
                    "Loại vấn đề",
                    "Mức cảnh báo",
                    "Trạng thái"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "✅ Hiện chưa có phản hồi mức cao."
        )


# =========================================================
# GỬI PHẢN HỒI
# =========================================================

elif page == "📝 Gửi phản hồi":

    st.subheader(
        "📝 Gửi phản hồi / khiếu nại"
    )

    st.info(
        "Phản hồi sẽ được hệ thống phân tích "
        "và lưu trực tiếp vào MySQL."
    )

    with st.form("feedback_form"):

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Họ và tên *"
            )

            email = st.text_input(
                "Email *"
            )

            service = st.selectbox(
                "Dịch vụ đã sử dụng *",
                [
                    "Tour du lịch",
                    "Khách sạn",
                    "Nhà hàng",
                    "Vận chuyển",
                    "Teambuilding",
                    "Sự kiện",
                    "Khác"
                ]
            )

        with col2:

            satisfaction = st.slider(
                "Mức độ hài lòng",
                1,
                5,
                3
            )

            st.write(
                f"⭐ Đánh giá: **{satisfaction}/5**"
            )

            feedback_type = st.selectbox(
                "Loại phản hồi",
                [
                    "Khiếu nại",
                    "Góp ý",
                    "Khen ngợi",
                    "Đề xuất"
                ]
            )

        content = st.text_area(
            "Nội dung phản hồi *",
            height=180,
            placeholder=(
                "Hãy mô tả trải nghiệm "
                "hoặc vấn đề bạn gặp phải..."
            )
        )

        submit = st.form_submit_button(
            "📤 Gửi phản hồi",
            use_container_width=True
        )

    if submit:

        if (
            not name.strip()
            or not email.strip()
            or not content.strip()
        ):

            st.error(
                "Vui lòng nhập đầy đủ thông tin."
            )

        else:

            issue = classify_issue(content)

            alert = calculate_alert(
                content,
                satisfaction
            )

            success, result = insert_complaint(
                name,
                email,
                service,
                satisfaction,
                feedback_type,
                issue,
                alert,
                content
            )

            if success:

                st.success(
                    f"✅ Gửi phản hồi thành công! "
                    f"Mã phản hồi: **{result}**"
                )

                st.write(
                    f"**Loại vấn đề:** {issue}"
                )

                st.write(
                    f"**Mức cảnh báo:** {alert}"
                )

                if alert == "Khẩn cấp":

                    st.error(
                        "🚨 CẢNH BÁO KHẨN CẤP: "
                        "Vấn đề cần được ưu tiên xử lý."
                    )

                elif alert == "Cao":

                    st.warning(
                        "⚠️ CẢNH BÁO MỨC CAO: "
                        "Doanh nghiệp cần kiểm tra sớm."
                    )

            else:

                st.error(
                    f"Không thể lưu phản hồi: {result}"
                )


# =========================================================
# TRA CỨU
# =========================================================

elif page == "🔎 Tra cứu phản hồi":

    st.subheader("🔎 Tra cứu phản hồi")

    df = get_complaints()

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Tìm kiếm",
            placeholder="Mã, họ tên hoặc nội dung..."
        )

    with col2:

        services = ["Tất cả"]

        if len(df) > 0:
            services += sorted(
                df["Dịch vụ"]
                .dropna()
                .unique()
                .tolist()
            )

        service_filter = st.selectbox(
            "Dịch vụ",
            services
        )

    with col3:

        statuses = ["Tất cả"]

        if len(df) > 0:
            statuses += sorted(
                df["Trạng thái"]
                .dropna()
                .unique()
                .tolist()
            )

        status_filter = st.selectbox(
            "Trạng thái",
            statuses
        )

    result = df.copy()

    if search:

        search_lower = search.lower()

        result = result[
            result.apply(
                lambda row:
                search_lower in
                str(row.to_dict()).lower(),
                axis=1
            )
        ]

    if service_filter != "Tất cả":

        result = result[
            result["Dịch vụ"] == service_filter
        ]

    if status_filter != "Tất cả":

        result = result[
            result["Trạng thái"] == status_filter
        ]

    st.write(
        f"**Tìm thấy {len(result)} phản hồi**"
    )

    st.dataframe(
        result[
            [
                "Mã phản hồi",
                "Thời gian",
                "Họ tên",
                "Dịch vụ",
                "Mức hài lòng",
                "Loại vấn đề",
                "Mức cảnh báo",
                "Trạng thái"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# CẢNH BÁO
# =========================================================

elif page == "🚨 Cảnh báo chất lượng":

    st.subheader(
        "🚨 Trung tâm cảnh báo chất lượng"
    )

    df = get_complaints()

    critical_df = df[
        df["Mức cảnh báo"] == "Khẩn cấp"
    ]

    high_df = df[
        df["Mức cảnh báo"] == "Cao"
    ]

    if len(critical_df) > 0:

        st.error(
            f"🚨 Có {len(critical_df)} "
            "phản hồi KHẨN CẤP"
        )

        for _, row in critical_df.iterrows():

            st.error(
                f"""
                🚨 {row['Mã phản hồi']}

                Khách hàng: {row['Họ tên']}

                Dịch vụ: {row['Dịch vụ']}

                Vấn đề: {row['Loại vấn đề']}

                Nội dung: {row['Nội dung']}

                Trạng thái: {row['Trạng thái']}
                """
            )

    if len(high_df) > 0:

        st.warning(
            f"⚠️ Có {len(high_df)} "
            "phản hồi mức CAO"
        )

        st.dataframe(
            high_df[
                [
                    "Mã phản hồi",
                    "Họ tên",
                    "Dịch vụ",
                    "Loại vấn đề",
                    "Mức hài lòng",
                    "Trạng thái"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    if (
        len(critical_df) == 0
        and len(high_df) == 0
    ):

        st.success(
            "✅ Hiện chưa phát hiện "
            "phản hồi mức cao."
        )


# =========================================================
# PHÂN TÍCH DỮ LIỆU
# =========================================================

elif page == "📊 Phân tích dữ liệu":

    st.subheader(
        "📊 Phân tích chất lượng dịch vụ"
    )

    df = get_complaints()

    if len(df) == 0:

        st.info(
            "Chưa có dữ liệu để phân tích."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                "### ⭐ Mức độ hài lòng"
            )

            satisfaction = (
                df["Mức hài lòng"]
                .value_counts()
                .sort_index()
            )

            st.bar_chart(satisfaction)

        with col2:

            st.markdown(
                "### 📌 Vấn đề thường gặp"
            )

            issues = (
                df["Loại vấn đề"]
                .value_counts()
            )

            st.bar_chart(issues)

        st.markdown(
            "### 🏨 Phân tích theo dịch vụ"
        )

        service_analysis = (
            df.groupby("Dịch vụ")
            .agg(
                Số_phản_hồi=(
                    "Mã phản hồi",
                    "count"
                ),
                Điểm_hài_lòng=(
                    "Mức hài lòng",
                    "mean"
                )
            )
            .reset_index()
        )

        service_analysis[
            "Điểm_hài_lòng"
        ] = service_analysis[
            "Điểm_hài_lòng"
        ].round(2)

        st.dataframe(
            service_analysis,
            use_container_width=True,
            hide_index=True
        )

        st.markdown(
            "### 🔄 Cập nhật trạng thái"
        )

        codes = df[
            "Mã phản hồi"
        ].tolist()

        selected_code = st.selectbox(
            "Chọn phản hồi",
            codes
        )

        selected = df[
            df["Mã phản hồi"] == selected_code
        ].iloc[0]

        status_options = [
            "Chưa xử lý",
            "Đã tiếp nhận",
            "Đang xử lý",
            "Đã xử lý",
            "Đã đóng"
        ]

        current_status = selected["Trạng thái"]

        if current_status in status_options:

            default_index = status_options.index(
                current_status
            )

        else:

            default_index = 0

        new_status = st.selectbox(
            "Trạng thái mới",
            status_options,
            index=default_index
        )

        if st.button(
            "💾 Cập nhật trạng thái",
            use_container_width=True
        ):

            success = update_status(
                int(selected["id"]),
                new_status
            )

            if success:

                st.success(
                    "✅ Đã cập nhật trạng thái vào MySQL."
                )

                st.rerun()

        st.markdown(
            "### 📥 Xuất dữ liệu"
        )

        csv = df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "📥 Tải dữ liệu CSV",
            csv,
            "customer_complaints.csv",
            "text/csv",
            use_container_width=True
        )
