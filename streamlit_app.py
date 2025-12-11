import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd

# ===============================
#     DATA MODEL (LINKED LIST)
# ===============================
class Node:
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        self.waktu_masuk = datetime.strptime(waktu_masuk, "%H:%M")

        # Random waktu keluar (simulasi bisnis parkir)
        lama = random.randint(30, 720)  # 30 menit – 12 jam
        self.waktu_keluar = self.waktu_masuk + timedelta(minutes=lama)

        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        self.biaya_parkir = self.hit_biaya()
        self.next = None

    def hit_biaya(self):
        jam = int(self.durasi_parkir.total_seconds() // 3600)
        jam = max(1, jam)

        if self.jenis_kendaraan == "Mobil":
            return 5000 + (jam - 1) * 3000
        return 3000 + (jam - 1) * 2000


class DataParkir:
    def __init__(self):
        self.head = None

    def add(self, nomor_polisi, jenis, waktu):
        node = Node(nomor_polisi, jenis, waktu)
        if not self.head:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node

    def search(self, nomor_polisi):
        cur = self.head
        while cur:
            if cur.nomor_polisi == nomor_polisi:
                return cur
            cur = cur.next
        return None

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

    def all_data(self):
        data = []
        cur = self.head
        while cur:
            data.append(cur)
            cur = cur.next
        return data

    def to_df(self, data_list):
        return pd.DataFrame([
            {
                "Nomor Polisi": d.nomor_polisi,
                "Jenis": d.jenis_kendaraan,
                "Masuk": d.waktu_masuk.strftime("%H:%M"),
                "Keluar": d.waktu_keluar.strftime("%H:%M"),
                "Durasi": str(d.durasi_parkir),
                "Biaya (Rp)": d.biaya_parkir
            }
            for d in data_list
        ])


# ===============================
#         STREAMLIT UI
# ===============================

st.set_page_config(page_title="Manajemen Parkir Bisnis", layout="wide")
st.title("🏢 Sistem Manajemen Data Parkir")

# Init Session
if "parkir" not in st.session_state:
    st.session_state.parkir = DataParkir()

parkir = st.session_state.parkir


# ===============================
#    Generate Sample Data
# ===============================

def generate_data():
    jenis = ["Mobil", "Motor"]
    for _ in range(20):
        nomor = f"B {random.randint(1000,9999)} {''.join(random.choices(string.ascii_uppercase, k=3))}"
        j = random.choice(jenis)
        w = f"{random.randint(6,22)}:{random.randint(0,59):02d}"
        parkir.add(nomor, j, w)

if st.button("Generate Data Parkir (Simulasi Bisnis)"):
    generate_data()
    st.success("Data simulasi berhasil ditambahkan!")


# ===============================
#         INPUT DATA
# ===============================

st.subheader("➕ Input Kendaraan Masuk")

col1, col2, col3 = st.columns(3)

with col1:
    inp_nopol = st.text_input("Nomor Polisi")
with col2:
    inp_jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"])
with col3:
    inp_waktu = st.text_input("Waktu Masuk (HH:MM)", "08:00")

if st.button("Tambah Data"):
    if inp_nopol:
        parkir.add(inp_nopol, inp_jenis, inp_waktu)
        st.success("Data parkir ditambahkan!")
    else:
        st.error("Nomor polisi wajib diisi.")


# ===============================
#        SEARCH / DELETE
# ===============================

st.subheader("🔍 Cari atau Hapus Data Parkir")

search_key = st.text_input("Cari berdasarkan Nomor Polisi")

c1, c2 = st.columns(2)

with c1:
    if st.button("Cari"):
        result = parkir.search(search_key)
        if result:
            st.info(
                f"**Nomor Polisi:** {result.nomor_polisi}\n"
                f"**Jenis:** {result.jenis_kendaraan}\n"
                f"**Masuk:** {result.waktu_masuk.strftime('%H:%M')}\n"
                f"**Keluar:** {result.waktu_keluar.strftime('%H:%M')}\n"
                f"**Durasi:** {result.durasi_parkir}\n"
                f"**Biaya:** Rp {result.biaya_parkir:,}"
            )
        else:
            st.warning("Data tidak ditemukan.")

with c2:
    if st.button("Hapus"):
        if parkir.delete(search_key):
            st.success("Data berhasil dihapus!")
        else:
            st.error("Nomor polisi tidak ditemukan.")


# ===============================
#        TABEL DATA
# ===============================

st.subheader("📋 Data Parkir Kendaraan")

data = parkir.all_data()
df = parkir.to_df(data)

st.dataframe(df, use_container_width=True)


# ===============================
#           KPI SUMMARY
# ===============================

st.subheader("📊 Statistik Bisnis Parkir")

total_pendapatan = sum([d.biaya_parkir for d in data])
jml_mobil = len([d for d in data if d.jenis_kendaraan == "Mobil"])
jml_motor = len([d for d in data if d.jenis_kendaraan == "Motor"])

colA, colB, colC = st.columns(3)

colA.metric("Total Pendapatan", f"Rp {total_pendapatan:,}")
colB.metric("Jumlah Mobil", jml_mobil)
colC.metric("Jumlah Motor", jml_motor)

