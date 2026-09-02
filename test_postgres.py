import time
import psycopg2
import streamlit as st

start = time.perf_counter()

conn = psycopg2.connect(
    st.secrets["DATABASE_URL"],
    connect_timeout=5
)

connected = time.perf_counter()

cur = conn.cursor()
cur.execute("SELECT 1;")
cur.fetchone()

finished = time.perf_counter()

print(f"DB 연결 시간: {connected - start:.3f}초")
print(f"쿼리 시간: {finished - connected:.3f}초")
print(f"전체 시간: {finished - start:.3f}초")

cur.close()
conn.close()