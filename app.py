```python
import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime

# =========================================================
# CẤU HÌNH STREAMLIT
# =========================================================

st.set_page_config(
    page_title="Customer Complaint Radar",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# THÔNG TIN MYSQL AIVEN
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

</style>
""", unsafe_allow_html=True)


# =========================================================
# KẾT NỐI MYSQL
# =========================================================

def get_connection():

    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=20,
        ssl={
            "check_hostname": False
        }
    )


# =========================================================
# KHỞI TẠO DATABASE
# =========================================================

def init_database():

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INT AUTO_INCREMENT PRIMARY KEY,

                complaint_code VARCHAR(20) NOT NULL UNIQUE,

                created_at DA_
```
