import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image

# =========================================================
# CẤU HÌNH TRANG
# =========================================================

st.set_page_config(
    page_title="Customer Complaint Radar",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    padding-bottom: 2rem;
}

.header-box {
    background: linear-gradient(135deg, #0f4c81, #1976d2);
    padding: 25px;
    border-radius: 15px;
    color: white;
    margin-bottom: 25px;
}

.header-title {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 5px;
}

.header-subtitle {
    font-size: 16px;
    opacity: 0.9;
}

.card {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    margin-bottom: 15px;
}

.metric-card {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}

.metric-number {
    font-size: 30px;
    font-weight: 700;
    color: #0f4c81;
}

.metric-label {
    color: #666;
    font-size: 14px;
}

.alert-high {
    background-color: #fff3cd;
    border-left: 5px solid #ff9800;
    padding: 15px;
    border-radius: 8px;
}

.alert-critical {
    background-color: #f8d7da;
    border-left: 5px solid #dc3545;
    padding: 15px;
    border-radius: 8px;
}

.alert-low {
    background-color: #d1ecf1;
    border-left: 5px solid #17a2b8;
    padding: 15px;
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# KHỞI TẠO DỮ LIỆU
# =========================================================

if "complaints" not in st.session_state:

    st.session_state.complaints = pd.DataFrame([
        {
            "Mã phản hồi": "CB001",
            "Thời gian": "28/09/2026 08:30",
            "Họ tên": "Nguyễn Văn A",
            "Email": "nguyenvana@gmail.com",
            "Dịch vụ": "Khách sạn",
            "Mức hài lòng": 2,
            "Loại vấn đề": "Phòng nghỉ",
            "Mức cảnh báo": "Cao",
            "Nội dung": "Phòng chưa được vệ sinh sạch sẽ khi nhận phòng.",
            "Trạng thái": "Chưa xử lý"
        },
        {
            "Mã phản hồi": "CB002",
            "Thời gian": "28/09/2026 09:15",
            "Họ tên": "Trần Thị B",
            "Email": "tranthib@gmail.com",
            "Dịch vụ": "Tour du lịch",
            "Mức hài lòng": 4,
            "Loại vấn đề": "Lịch trình",
            "Mức cảnh báo": "Thấp",
            "Nội dung": "Lịch trình khá tốt nhưng thời gian tham quan hơi ngắn.",
            "Trạng thái": "Đã tiếp nhận"
        },
        {
            "Mã phản hồi": "CB003",
            "Thời gian": "28/09/2026 10:20",
            "Họ tên": "Lê Văn C",
            "Email": "levanc@gmail.com",
            "Dịch vụ": "Vận chuyển",
            "Mức hài lòng": 1,
            "Loại vấn đề": "Xe đưa đón",
            "Mức cảnh báo": "Khẩn cấp",
            "Nội dung": "Xe đón khách đến trễ hơn một giờ và không có thông báo trước.",
            "Trạng thái": "Đang xử lý"
        }
    ])


# =========================================================
# HÀM PHÂN LOẠI VẤN ĐỀ
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
# HÀM XÁC ĐỊNH MỨC CẢNH BÁO
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
        "không có",
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
# SIDEBAR
# =========================================================

with st.sidebar:

    st.image("VT3.jpg", use_container_width=True)

    st.markdown("## 🚨 Customer Complaint Radar")

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

    st.caption("© 2026 Customer Complaint Radar")


# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="header-box">

<div class="header-title">
🚨 CUSTOMER COMPLAINT RADAR
</div>

<div class="header-subtitle">
Hệ thống phân tích và cảnh báo vấn đề chất lượng dịch vụ từ phản hồi khách hàng
</div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# TRANG TỔNG QUAN
# =========================================================

if page == "🏠 Tổng quan":

    df = st.session_state.complaints

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
                <div class="metric-label">Tổng phản hồi</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{critical}</div>
                <div class="metric-label">Khẩn cấp</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{high}</div>
                <div class="metric-label">Mức cao</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{unresolved}</div>
                <div class="metric-label">Chưa xử lý</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 📌 Tình hình phản hồi gần đây")

    col1, col2 = st.columns(2)

    with col1:

        issue_count = (
            df["Loại vấn đề"]
            .value_counts()
            .reset_index()
        )

        issue_count.columns = [
            "Loại vấn đề",
            "Số lượng"
        ]

        st.bar_chart(
            issue_count.set_index("Loại vấn đề")
        )

    with col2:

        alert_count = (
            df["Mức cảnh báo"]
            .value_counts()
            .reset_index()
        )

        alert_count.columns = [
            "Mức cảnh báo",
            "Số lượng"
        ]

        st.bar_chart(
            alert_count.set_index("Mức cảnh báo")
        )

    st.markdown("### 🚨 Phản hồi cần chú ý")

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

        st.success("Hiện chưa có phản hồi mức cảnh báo cao.")


# =========================================================
# GỬI PHẢN HỒI
# =========================================================

elif page == "📝 Gửi phản hồi":

    st.subheader("📝 Gửi phản hồi / khiếu nại")

    st.info(
        "Ý kiến của bạn giúp doanh nghiệp phát hiện "
        "và cải thiện chất lượng dịch vụ."
    )

    with st.form("feedback_form"):

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Họ và tên *",
                placeholder="Nhập họ tên"
            )

            email = st.text_input(
                "Email *",
                placeholder="example@gmail.com"
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
                min_value=1,
                max_value=5,
                value=3
            )

            st.write(
                f"⭐ Mức đánh giá: **{satisfaction}/5**"
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
                "Hãy mô tả vấn đề hoặc trải nghiệm "
                "của bạn..."
            )
        )

        submitted = st.form_submit_button(
            "📤 Gửi phản hồi",
            use_container_width=True
        )

    if submitted:

        if not name or not email or not content:

            st.error(
                "Vui lòng nhập đầy đủ thông tin bắt buộc."
            )

        else:

            issue = classify_issue(content)

            alert = calculate_alert(
                content,
                satisfaction
            )

            new_id = (
                f"CB{len(st.session_state.complaints)+1:03d}"
            )

            new_row = {
                "Mã phản hồi": new_id,
                "Thời gian": datetime.now().strftime(
                    "%d/%m/%Y %H:%M"
                ),
                "Họ tên": name,
                "Email": email,
                "Dịch vụ": service,
                "Mức hài lòng": satisfaction,
                "Loại vấn đề": issue,
                "Mức cảnh báo": alert,
                "Nội dung": content,
                "Trạng thái": "Chưa xử lý"
            }

            st.session_state.complaints = pd.concat(
                [
                    st.session_state.complaints,
                    pd.DataFrame([new_row])
                ],
                ignore_index=True
            )

            st.success(
                f"Phản hồi đã được ghi nhận với mã **{new_id}**."
            )

            st.write(
                f"**Vấn đề được hệ thống phân loại:** {issue}"
            )

            if alert == "Khẩn cấp":

                st.error(
                    "🚨 CẢNH BÁO KHẨN CẤP: "
                    "Phản hồi có mức độ nghiêm trọng cao "
                    "và cần được doanh nghiệp xử lý sớm."
                )

            elif alert == "Cao":

                st.warning(
                    "⚠️ CẢNH BÁO MỨC CAO: "
                    "Phản hồi cần được ưu tiên kiểm tra."
                )

            elif alert == "Trung bình":

                st.info(
                    "ℹ️ Phản hồi cần được theo dõi."
                )

            else:

                st.success(
                    "Phản hồi đã được ghi nhận."
                )


# =========================================================
# TRA CỨU PHẢN HỒI
# =========================================================

elif page == "🔎 Tra cứu phản hồi":

    st.subheader("🔎 Tra cứu phản hồi")

    df = st.session_state.complaints.copy()

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Tìm kiếm",
            placeholder="Mã, tên hoặc nội dung..."
        )

    with col2:

        service_filter = st.selectbox(
            "Dịch vụ",
            ["Tất cả"] +
            sorted(df["Dịch vụ"].unique().tolist())
        )

    with col3:

        status_filter = st.selectbox(
            "Trạng thái",
            ["Tất cả"] +
            sorted(df["Trạng thái"].unique().tolist())
        )

    if search:

        search_lower = search.lower()

        df = df[
            df.apply(
                lambda row:
                search_lower in str(row.values).lower(),
                axis=1
            )
        ]

    if service_filter != "Tất cả":

        df = df[
            df["Dịch vụ"] == service_filter
        ]

    if status_filter != "Tất cả":

        df = df[
            df["Trạng thái"] == status_filter
        ]

    st.write(
        f"**Tìm thấy {len(df)} phản hồi**"
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# CẢNH BÁO CHẤT LƯỢNG
# =========================================================

elif page == "🚨 Cảnh báo chất lượng":

    st.subheader("🚨 Trung tâm cảnh báo chất lượng")

    df = st.session_state.complaints

    critical_df = df[
        df["Mức cảnh báo"] == "Khẩn cấp"
    ]

    high_df = df[
        df["Mức cảnh báo"] == "Cao"
    ]

    if len(critical_df) > 0:

        st.error(
            f"🚨 Có **{len(critical_df)}** phản hồi "
            "đang ở mức KHẨN CẤP."
        )

        for _, row in critical_df.iterrows():

            st.markdown(
                f"""
                <div class="alert-critical">

                <b>🚨 {row['Mã phản hồi']} -
                {row['Loại vấn đề']}</b>

                <br><br>

                <b>Dịch vụ:</b> {row['Dịch vụ']}

                <br>

                <b>Khách hàng:</b> {row['Họ tên']}

                <br>

                <b>Nội dung:</b> {row['Nội dung']}

                <br><br>

                <b>Trạng thái:</b> {row['Trạng thái']}

                </div>
                """,
                unsafe_allow_html=True
            )

            st.write("")

    if len(high_df) > 0:

        st.warning(
            f"⚠️ Có **{len(high_df)}** phản hồi "
            "ở mức cảnh báo CAO."
        )

        st.dataframe(
            high_df[
                [
                    "Mã phản hồi",
                    "Dịch vụ",
                    "Loại vấn đề",
                    "Mức hài lòng",
                    "Trạng thái"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    if len(critical_df) == 0 and len(high_df) == 0:

        st.success(
            "✅ Hiện tại chưa phát hiện phản hồi "
            "có mức cảnh báo cao."
        )


# =========================================================
# PHÂN TÍCH DỮ LIỆU
# =========================================================

elif page == "📊 Phân tích dữ liệu":

    st.subheader("📊 Phân tích chất lượng dịch vụ")

    df = st.session_state.complaints

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### ⭐ Mức độ hài lòng")

        satisfaction = (
            df["Mức hài lòng"]
            .value_counts()
            .sort_index()
        )

        st.bar_chart(satisfaction)

    with col2:

        st.markdown("### 📌 Loại vấn đề")

        issue = (
            df["Loại vấn đề"]
            .value_counts()
        )

        st.bar_chart(issue)

    st.markdown("### 🏨 Chất lượng theo từng dịch vụ")

    service_analysis = (
        df.groupby("Dịch vụ")
        .agg(
            Số_phản_hồi=("Mã phản hồi", "count"),
            Điểm_hài_lòng=("Mức hài lòng", "mean")
        )
        .reset_index()
    )

    service_analysis["Điểm_hài_lòng"] = (
        service_analysis["Điểm_hài_lòng"]
        .round(2)
    )

    st.dataframe(
        service_analysis,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 🚨 Phân bố mức cảnh báo")

    alert_analysis = (
        df["Mức cảnh báo"]
        .value_counts()
        .reset_index()
    )

    alert_analysis.columns = [
        "Mức cảnh báo",
        "Số lượng"
    ]

    st.dataframe(
        alert_analysis,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 📥 Xuất dữ liệu")

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="📥 Tải dữ liệu phản hồi CSV",
        data=csv,
        file_name="customer_complaints.csv",
        mime="text/csv"
    )
