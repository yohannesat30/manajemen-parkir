import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd

# -----------------------------
# CLASS DEFINITIONS
# -----------------------------

class Node:
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        self.waktu_masuk = datetime.strptime(waktu_masuk, "%H:%M")
        
        # Generate waktu keluar acak
        random_minutes = random.randint(1, 1440)
        self.waktu_keluar = self.waktu_masuk + timedelta(minutes=random_minutes)
        
        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        self.biaya_parkir = self.calculate_biaya_parkir()
        self.next = None

    def calculate_biaya_parkir(self):
        hours = int(self.durasi_parkir.total_seconds() // 3600)
        hours = max(1, hours)  # minimal satu jam

        if self.jenis_kendaraan == "Mobil":
            return 5000 + (hours - 1) * 1000
        else:
            return 3000 + (hours - 1) * 1000


class DataParkir:
    def __init__(self):
        self.head = None

    def add_data(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
        new_node = Node(nomor_polisi, jenis_kendaraan, waktu_masuk)

        if not self.head:
            self.head = new_node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = new_node

    def delete_data(self, nomor_polisi):
        if not self.head:
            return False
        
        if self.head.nomor_polisi == nomor_polisi:
            self.head = self.head.next
            return True

        cur = self.head
        while cur.next:
            if cur.next.nomor_polisi == nomor_polisi:
                cur.next = cur.next.next
                return True
            cur = cur.next

        return False

    def search_data(self, nomor_polisi):
        cur = self.head
        while cur:
            if cur.nomor_polisi == nomor_polisi:
                return cur
            cur = cur.next
        return None

    def update_data(self, nomor_lama, nomor_baru, jenis, waktu):
        cur = self.head
        while cur:
            if cur.nomor_polisi == nomor_lama:
                cur.nomor_polisi = nomor_baru
                cur.jenis_kendaraan = jenis
                cur.waktu_masuk = datetime.strptime(waktu, "%H:%M")
                cur.waktu_keluar = cur.waktu_masuk + timedelta(minutes=random.randint(1, 1440))
                cur.durasi_parkir = cur.waktu_keluar - cur.waktu_masuk
                cur.biaya_parkir = cur.calculate_biaya_parkir()
                return True
            cur = cur.next
        return False

    def get_data(self):
        data = []
        cur = self.head
        while cur:
            data.append(cur)
            cur = cur.next
        return data

    def to_dataframe(self, data_list):
        df = pd.DataFrame([
            {
                "Nomor Polisi": d.nomor_polisi,
                "Jenis Kendaraan": d.jenis_kendaraan,
                "Waktu Masuk": d.waktu_masuk.strftime("%H:%M"),
                "Waktu Keluar": d.waktu_keluar.strftime("%H:%M"),
                "Durasi Parkir": str(d.durasi_parkir),
                "Biaya Parkir": d.biaya_parkir
            }
            for d in data_list
        ])
        return df


# ---------------------------------
# STREAMLIT APP START
# ---------------------------------
st.title("🚗 Sistem Manajemen Data Parkir (Streamlit)")

# Session state
if "data_parkir" not in st.session_state:
    st.session_state.data_parkir = DataParkir()

parking_data = st.session_state.data_parkir

# -----------------------------
# Random Data
# -----------------------------
def generate_random_data():
    jenis_list = ["Mobil", "Motor"]
    for _ in range(20):
        nomor = f"B {random.randint(1000,9999)} {''.join(random.choices(string.ascii_uppercase, k=3))}"
        jenis = random.choice(jenis_list)
        waktu = f"{random.randint(6,23)}:{random.randint(0,59):02d}"
        parking_data.add_data(nomor, jenis, waktu)

if st.button("Generate 20 Random Data"):
    generate_random_data()
    st.success("Random data berhasil ditambahkan.")

# -----------------------------
# Add/Edit Data
# -----------------------------
st.subheader("➕ Tambah Data Parkir")

col1, col2, col3 = st.columns(3)

with col1:
    nomor_polisi = st.text_input("Nomor Polisi")
with col2:
    jenis_kendaraan = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"])
with col3:
    waktu_masuk = st.text_input("Waktu Masuk (HH:MM)", "08:00")

if st.button("Add Data"):
    parking_data.add_data(nomor_polisi, jenis_kendaraan, waktu_masuk)
    st.success("Data berhasil ditambahkan.")

# -----------------------------
# Search / Update / Delete
# -----------------------------
st.subheader("🔍 Cari / Update / Hapus Data")

search_key = st.text_input("Cari Nomor Polisi")

if st.button("Search"):
    result = parking_data.search_data(search_key)
    if result:
        st.info(f"""
        **Nomor Polisi:** {result.nomor_polisi}  
        **Jenis Kendaraan:** {result.jenis_kendaraan}  
        **Waktu Masuk:** {result.waktu_masuk.strftime('%H:%M')}  
        **Waktu Keluar:** {result.waktu_keluar.strftime('%H:%M')}  
        **Durasi Parkir:** {result.durasi_parkir}  
        **Biaya Parkir:** Rp {result.biaya_parkir}
        """)
    else:
        st.error("Data tidak ditemukan.")

if st.button("Delete"):
    if parking_data.delete_data(search_key):
        st.success("Data berhasil dihapus.")
    else:
        st.error("Data tidak ditemukan.")

# -----------------------------
# Filter + Sort
# -----------------------------
st.subheader("📋 Data Parkir")

filter_opt = st.selectbox("Filter Jenis Kendaraan", ["Semua", "Mobil", "Motor"])
sort_opt = st.selectbox("Sort Durasi", ["Ascending", "Descending"])

data_list = parking_data.get_data()

# Filter
if filter_opt != "Semua":
    data_list = [d for d in data_list if d.jenis_kendaraan == filter_opt]

# Sort
data_list = sorted(data_list, key=lambda x: x.durasi_parkir, reverse=(sort_opt == "Descending"))

# Display Table
df = parking_data.to_dataframe(data_list)
st.dataframe(df, use_container_width=True)
