import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd

# ================================================================
#                    MODEL DATA (LINKED LIST)
# ================================================================

class Node:
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        self.waktu_masuk = datetime.strptime(waktu_masuk, "%H:%M")

        random_minutes = random.randint(30, 720)  # durasi parkir realistis 30 menit - 12 jam
        self.waktu_keluar = self.waktu_masuk + timedelta(minutes=random_minutes)

        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        self.biaya_parkir = self.calculate_biaya_parkir()
        self.next = None

    def calculate_biaya_parkir(self):
        """Simulasi tarif parkir bisnis:
        Mobil: 5.000 jam pertama, 3.000/jam berikutnya
        Motor: 3.000 jam pertama, 2.000/jam berikutnya
        """
        jam = int(self.durasi_parkir.total_seconds() // 3600)
        jam = max(1, jam)

        if self.jenis_kendaraan == "Mobil":
            return 5000 + (jam - 1) * 3000
        
        return 3000 + (jam - 1) * 2000


class DataParkir:
    def __init__(self):
        self.head = None

    def add(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
        new_node = Node(nomor_polisi, jenis_kendaraan, waktu_masuk)
        if not self.head:
            self.head = new_node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = new_node

    def delete(self, nomor_polisi):
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

    def search(self, nomor_polisi):
        cur = self.head
        while cur:
            if cur.nomor_polisi == nomor_polisi:
                return cur
            cur = cur.next
        return None

    def get_all(self):
        data = []
        cur = self.head
        while cur:
            data.append(cur)
            cur = cur.next
        return data

    def to_dataframe(self, data_list):
        return pd.DataFrame([
            {
                "Nomor Polisi": d.nomor_polisi,
                "Jenis": d.jenis_kendaraan,
                "Masuk": d.waktu_masuk.strftime("%H:%M"),
                "Keluar": d.waktu_keluar.strftime("%H:%M"),
                "Durasi": str(d.durasi_parkir),
                "Biaya (Rp)": d.biaya_parkir,
            }
            for d in data_list
        ])


# ================================================================
#                    STREAMLIT BUSINESS UI
# ================================================================

st.set_page_config(page_title="Manajemen Parkir Bisnis", layout="wide")
st.title("🏢 Manajemen Data Parkir — Dashboard Bisnis")

# Initialize session state
if "parkir" not in st.session_state:
    st.session_state.parkir = DataParkir()

parkir = st.session_state.parkir


# ================================================================
#                    GEN RANDOM BUSINESS DATA
# ================================================================

def generate_business_data():
    jenis_list = ["Mobil", "Motor"]
    for _ in range(30):
        nomor = f"B {random.randint(1000,9999)} {''.join(random.choices(string.ascii_uppercase, k=3))}"
        jenis = random.choice(jenis_list)
        waktu = f"{random.randint(6,22)}:{random.randint(0,59):02d}"
        parkir.add(nomor, jenis, waktu)

if st.button("Generate Sample Data Operasional"):
    generate_business_data()
    st.success("✔ Data operasional (simulasi) berhasil dibuat!")


# ================================================================
#                    INPUT FORM (ADD RECORD)
# ================================================================

st.subheader("➕ Input Kendaraan Masuk")

col1, col2, col3 = st.columns(3)

with col1:
    nomor_input = st.text_input("Nomor Polisi (contoh: B 1234 ABC)")
with col2:
    jenis_input = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"])
with col3:
    waktu_input = st.text_input("Waktu Masuk (HH:MM)", "08:00")

if st.button("Tambah Data Parkir"):
    parkir.add(nomor_input, jenis_input, waktu_input)
    st.success("Data parkir berhasil ditambahkan!")


# ================================================================
#                    SEARCH / DELETE DATA
# ================================================================

st.subheader("🔍 Cari / Hapus Data Kendaraan")

search_key = st.text_input("Cari berdasarkan Nomor Polisi")

colA, colB = st.columns(2)

with colA:
    if st.button("Cari Data"):
        result = parkir.search(search_key)
        if result:
            st.info(
                f"""
                **Nomor Polisi:** {result.nomor_polisi}  
                **Jenis:** {result.jenis_kendaraan}  
                **Masuk:** {result.waktu_masuk.strftime('%H:%M')}  
                **Keluar:** {result.waktu_keluar.strftime('%H:%M')}  
                **Durasi:** {result.durasi_parkir}  
                **Biaya:** Rp {result.biaya_parkir:,}  
                """
            )
        else:
            st.error("⚠ Data tidak ditemukan.")

with colB:
    if st.button("Hapus Data"):
        if parkir.delete(search_key):
            st.success("✔ Data berhasil dihapus.")
        else:
            st.error("⚠ Nomor polisi tidak ditemukan.")


# ================================================================
#                    FILTER & SORT + TABLE
# ================================================================

st.subheader("📋 Data Kendaraan Parkir")

filter_jenis = st.selectbox("Filter Jenis Kendaraan", ["Semua", "Mobil", "M]()_
