import streamlit as st
from datetime import datetime, timedelta
import random
import string
from tabulate import tabulate

# -----------------------------
# CLASS DEFINITIONS
# -----------------------------
class Node:
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        self.waktu_masuk = datetime.strptime(waktu_masuk, "%H:%M")
        random_minutes = random.randint(1, 1440)
        self.waktu_keluar = self.waktu_masuk + timedelta(minutes=random_minutes)
        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        self.biaya_parkir = self.calculate_biaya_parkir()
        self.next = None

    def calculate_biaya_parkir(self):
        hours = self.durasi_parkir.total_seconds() // 3600
        hours = max(1, hours)  # minimal 1 jam
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

    def update_data(self, nomor_lama, nomor, jenis, waktu):
        cur = self.head
        while cur:
            if cur.nomor_polisi == nomor_lama:
                cur.nomor_polisi = nomor
                cur.jenis_kendaraan = jenis
                cur.waktu_masuk = datetime.strptime(waktu, "%H:%M")
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

    def show_table(self, data_list):
        rows = []
        for i, d in enumerate(data_list, 1):
            rows.append([
                i,
                d.nomor_polisi,
                d.jenis_kendaraan,
                d.waktu_masuk.strftime("%H:%M"),
                d.waktu_keluar.strftime("%H:%M"),
                str(d.durasi_parkir),
                d.biaya_parkir
            ])
        headers = ["No", "Nomor Polisi", "Jenis", "Masuk", "Keluar", "Durasi", "Biaya"]
        return tabulate(rows, headers, tablefmt="grid")


# ---------------------------------
# STREAMLIT APP STARTS HERE
# ---------------------------------

st.title("🚗 Sistem Data Parkir (Streamlit Version)")

# Simpan data di session_state
if "data_parkir" not in st.session_state:
    st.session_state.data_parkir = DataParkir()

parking_data = st.session_state.data_parkir

# -----------------------------
# Generate Random Data Button
# -----------------------------
def generate_random_data():
    jenis_kendaraan = ["Mobil", "Motor"]
    for _ in range(20):
        nomor = f"B {random.randint(1000,9999)} {''.join(random.choices(string.ascii_uppercase,k=3))}"
        jenis = random.choice(jenis_kendaraan)
        waktu = f"{random.randint(6,23)}:{random.randint(0,59):02d}"
        parking_data.add_data(nomor, jenis, waktu)

if st.button("Generate Random Data (20 Random Records)"):
    generate_random_data()
    st.success("Random data berhasil ditambahkan.")

# -----------------------------
# Input Form
# -----------------------------
st.subheader("➕ Tambah / Update Data Parkir")

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
# Search & Update
# -----------------------------
st.subheader("🔍 Cari / Update / Hapus Data")

search_key = st.text_input("Cari berdasarkan Nomor Polisi")

if st.button("Search"):
    data = parking_data.search_data(search_key)
    if data:
        st.info(f"""
        **Nomor Polisi:** {data.nomor_polisi}  
        **Jenis Kendaraan:** {data.jenis_kendaraan}  
        **Waktu Masuk:** {data.waktu_masuk.strftime('%H:%M')}  
        **Waktu Keluar:** {data.waktu_keluar.strftime('%H:%M')}  
        **Durasi Parkir:** {data.durasi_parkir}  
        **Biaya:** {data.biaya_parkir}
        """)
    else:
        st.error("Data tidak ditemukan.")

if st.button("Delete"):
    if parking_data.delete_data(search_key):
        st.success("Data berhasil dihapus.")
    else:
        st.error("Data tidak ditemukan.")

# -----------------------------
# Filter dan Sort
# -----------------------------
st.subheader("📋 Tabel Data")

filter_opt = st.selectbox("Filter jenis kendaraan", ["Semua", "Mobil", "Motor"])
sort_opt = st.selectbox("Sort by Durasi", ["Ascending", "Descending"])

data_list = parking_data.get_data()

# Filter
if filter_opt != "Semua":
    data_list = [d for d in data_list if d.jenis_kendaraan == filter_opt]

# Sort
data_list = sorted(data_list, key=lambda x: x.durasi_parkir, reverse=(sort_opt == "Descending"))

# Display Table
st.text(parking_data.show_table(data_list))


