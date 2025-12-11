import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd

# ===============================
#         STREAMLIT UI + MENU
# ===============================

st.set_page_config(page_title="Manajemen Parkir Pelanggan", layout="wide")

# Sidebar Menu
menu = st.sidebar.radio(
    "📌 Menu",
    ["Dashboard", "Input Kendaraan", "Pencarian & Pembayaran", "Data Parkir"]
)

st.title("🏢 Sistem Manajemen Data Parkir (Enhanced)")("🏢 Sistem Manajemen Data Parkir (Enhanced)")

# Init Session
if "parkir" not in st.session_state:
    st.session_state.parkir = DataParkir()

parkir = st.session_state.parkir

# ===============================
#  Generate Data Simulasi
# ===============================


def generate_data():
    jenis = ["Mobil", "Motor"]
    metode = ["Cash", "QRIS", "Debit", "E-Wallet"]
    for _ in range(20):
        nomor = f"B {random.randint(1000,9999)} {''.join(random.choices(string.ascii_uppercase, k=3))}"
        j = random.choice(jenis)
        w = f"{random.randint(6,22)}:{random.randint(0,59):02d}"
        m = random.choice(metode)
        parkir.add(nomor, j, w, m)


if st.button("Generate Data Parkir (Simulasi Bisnis)"):
    generate_data()
    st.success("Data simulasi berhasil dibuat!")

# ===============================
# Input Kendaraan Masuk
# ===============================

st.subheader("➕ Input Kendaraan Masuk")
col1, col2, col3, col4 = st.columns(4)

with col1:
    inp_nopol = st.text_input("Nomor Polisi")
with col2:
    inp_jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"])
with col3:
    inp_waktu = st.text_input("Waktu Masuk (HH:MM)", "08:00")
with col4:
    inp_metode = st.selectbox("Metode Pembayaran", ["Cash", "QRIS", "Debit", "E-Wallet"])

if st.button("Tambah Data"):
    if inp_nopol:
        parkir.add(inp_nopol, inp_jenis, inp_waktu, inp_metode)
        st.success("Data parkir berhasil ditambahkan!")
    else:
        st.error("Nomor polisi wajib diisi!")

# ===============================
# Search / Delete / Update Payment
# ===============================

st.subheader("🔍 Cari, Hapus, atau Proses Pembayaran")
search_key = st.text_input("Cari berdasarkan Nomor Polisi")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("Cari"):
        result = parkir.search(search_key)
        if result:
            st.info(f"**Nomor Polisi:** {result.nomor_polisi}\n"
                    f"**Jenis:** {result.jenis_kendaraan}\n"
                    f"**Metode Pembayaran:** {result.metode_bayar}\n"
                    f"**Status:** {result.status_bayar}\n"
                    f"**Masuk:** {result.waktu_masuk.strftime('%H:%M')}\n"
                    f"**Keluar:** {result.waktu_keluar.strftime('%H:%M')}\n"
                    f"**Durasi:** {result.durasi_parkir}\n"
                    f"**Biaya:** Rp {result.biaya_parkir:,}")
        else:
            st.warning("Data tidak ditemukan.")

with c2:
    if st.button("Hapus"):
        if parkir.delete(search_key):
            st.success("Data berhasil dihapus!")
        else:
            st.error("Nomor polisi tidak ditemukan.")

with c3:
    if st.button("Proses Pembayaran"):
        result = parkir.search(search_key)
        if result:
            result.status_bayar = "Sudah Dibayar"
            st.success(f"Pembayaran untuk {result.nomor_polisi} berhasil diproses!")
        else:
            st.error("Data tidak ditemukan.")

# ===============================
# Tabel Data
# ===============================

st.subheader("📋 Data Parkir Kendaraan")
data = parkir.all_data()
df = parkir.to_df(data)

st.dataframe(df, use_container_width=True)

# ===============================
# Statistik Bisnis
# ===============================

st.subheader("📊 KPI Parkir")
total_pendapatan = sum([d.biaya_parkir for d in data])
jml_mobil = len([d for d in data if d.jenis_kendaraan == "Mobil"])
jml_motor = len([d for d in data if d.jenis_kendaraan == "Motor"])
jml_belum_bayar = len([d for d in data if d.status_bayar == "Belum Dibayar"])
jml_sudah_bayar = len([d for d in data if d.status_bayar == "Sudah Dibayar"])

colA, colB, colC, colD = st.columns(4)
colA.metric("Total Pendapatan", f"Rp {total_pendapatan:,}")
colB.metric("Jumlah Mobil", jml_mobil)
colC.metric("Jumlah Motor", jml_motor)
colD.metric("Transaksi Lunas", jml_sudah_bayar)



