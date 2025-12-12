import streamlit as st
import random
from datetime import datetime, timedelta
import pandas as pd
import os

# ===============================
#     DATA MODEL (LINKED LIST)
# ===============================
class Node:
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        # Mengubah string waktu ("HH:MM") menjadi objek datetime
        self.waktu_masuk = datetime.strptime(waktu_masuk, "%H:%M").replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
        
        # --- Simulasi Parkir: Waktu Keluar & Biaya ---
        # Random waktu keluar (simulasi bisnis parkir)
        lama = random.randint(30, 720)  # 30 menit – 12 jam
        self.waktu_keluar = self.waktu_masuk + timedelta(minutes=lama)
        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        self.biaya_parkir = self.hit_biaya()
        self.metode_bayar = None
        self.next = None

    def hit_biaya(self):
        # Hitung durasi dalam jam, minimal 1 jam.
        # total_seconds() // 3600 menghitung total jam bulat ke bawah
        jam_parkir = int(self.durasi_parkir.total_seconds() // 3600)
        # Jika durasi < 1 jam, dihitung 1 jam
        jam = max(1, jam_parkir + (1 if self.durasi_parkir.total_seconds() % 3600 > 0 else 0))
        
        # Logika Biaya (Jam pertama + Jam berikutnya)
        if self.jenis_kendaraan == "Mobil":
            # 5000 (jam pertama) + (jam sisanya * 3000)
            return 5000 + (jam - 1) * 3000
        # Untuk Motor
        return 3000 + (jam - 1) * 2000

class DataParkir:
    def __init__(self):
        self.head = None
        
    # --- Operasi Linked List Dasar ---
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
                "Durasi": str(d.durasi_parkir).split('.')[0], # Menghilangkan milisecond
                "Biaya (Rp)": d.biaya_parkir,
                "Metode Bayar": d.metode_bayar if d.metode_bayar else "-"
            }
            for d in data_list
        ])

    # ===============================
    #       File Handling
    # ===============================
    def save_to_file(self, filename="data_parkir.csv"):
        # Hanya simpan jika ada data
        data_list = self.all_data()
        if data_list:
            df = self.to_df(data_list)
            df.to_csv(filename, index=False)
        elif os.path.exists(filename):
            # Jika data kosong, hapus file lama (agar tidak memuat data di sesi berikutnya)
            os.remove(filename)

    def load_from_file(self, filename="data_parkir.csv"):
        # Fungsi ini yang menyebabkan data muncul tiba-tiba. 
        # Saya biarkan di sini tapi tidak dipanggil di Streamlit untuk memenuhi permintaan user.
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            for _, row in df.iterrows():
                # Pastikan waktu masuk dibaca sebagai string HH:MM
                self.add(row["Nomor Polisi"], row["Jenis"], row["Masuk"])
                node = self.search(row["Nomor Polisi"])
                node.metode_bayar = row.get("Metode Bayar", None)

    # ===============================
    #    Kendaraan > 24 jam
    # ===============================
    def check_long_park(self):
        long_park = []
        # Tambahkan tanggal hari ini ke durasi 24 jam untuk perbandingan yang lebih baik
        batas_24_jam = timedelta(hours=24)
        for d in self.all_data():
            if d.durasi_parkir > batas_24_jam:
                long_park.append(d)
        return long_park

# ===============================
#         STREAMLIT UI
# ===============================
st.set_page_config(page_title="Manajemen Parkir Bisnis", layout="wide")
st.title("🏢 Sistem Manajemen Data Parkir")


if "parkir" not in st.session_state:
    st.session_state.parkir = DataParkir()
parkir = st.session_state.parkir

# --- DI SINI ANDA MENGHAPUS PEMUATAN DATA OTOMATIS ---
# parkir.load_from_file() 
# Jika baris di atas diaktifkan, data akan dimuat dari CSV setiap refresh.

# ===============================
#         INPUT DATA
# ===============================
st.subheader("➕ Input Kendaraan Masuk")
col1, col2, col3, col4 = st.columns(4)
with col1:
    inp_nopol = st.text_input("Nomor Polisi", key="nopol_input")
with col2:
    inp_jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"], key="jenis_input")
with col3:
    # Waktu masuk default adalah waktu saat ini (untuk kemudahan)
    default_time = datetime.now().strftime("%H:%M")
    inp_waktu = st.text_input("Waktu Masuk (HH:MM)", default_time, key="waktu_input")
with col4:
    inp_bayar = st.selectbox("Metode Bayar", ["-", "Tunai", "E-wallet", "Kartu"], key="bayar_input")

if st.button("Tambah Data"):
    if inp_nopol and inp_waktu:
        try:
            # Pengecekan format waktu
            datetime.strptime(inp_waktu, "%H:%M")
            parkir.add(inp_nopol.upper(), inp_jenis, inp_waktu)
            node = parkir.search(inp_nopol.upper())
            node.metode_bayar = inp_bayar if inp_bayar != "-" else None
            st.success(f"Data parkir untuk **{inp_nopol.upper()}** ditambahkan!")
            parkir.save_to_file()
            # Bersihkan input setelah berhasil
            st.session_state.nopol_input = ""
            st.session_state.waktu_input = datetime.now().strftime("%H:%M")
            st.rerun() # Refresh tampilan data
        except ValueError:
            st.error("Format Waktu Masuk harus HH:MM (contoh: 08:00).")
    else:
        st.error("Nomor polisi dan Waktu Masuk wajib diisi.")

# ===============================
#        SEARCH / DELETE
# ===============================
st.subheader("🔍 Cari atau Hapus Data Parkir")
search_key = st.text_input("Cari berdasarkan Nomor Polisi").upper()
c1, c2 = st.columns(2)
with c1:
    if st.button("Cari Data", key="btn_cari"):
        result = parkir.search(search_key)
        if result:
            st.info(
                f"**Nomor Polisi:** {result.nomor_polisi}\n"
                f"**Jenis:** {result.jenis_kendaraan}\n"
                f"**Masuk:** {result.waktu_masuk.strftime('%H:%M')}\n"
                f"**Keluar (Simulasi):** {result.waktu_keluar.strftime('%H:%M')}\n"
                f"**Durasi:** {str(result.durasi_parkir).split('.')[0]}\n"
                f"**Biaya:** Rp {result.biaya_parkir:,}\n"
                f"**Metode Bayar:** {result.metode_bayar if result.metode_bayar else '-'}"
            )
        else:
            st.warning(f"Data parkir untuk **{search_key}** tidak ditemukan.")
with c2:
    if st.button("Hapus Data", key="btn_hapus"):
        if parkir.delete(search_key):
            st.success(f"Data parkir untuk **{search_key}** berhasil dihapus!")
            parkir.save_to_file()
            st.rerun() # Refresh tampilan data
        else:
            st.error(f"Nomor polisi **{search_key}** tidak ditemukan.")

# ===============================
#        TABEL DATA
# ===============================
st.subheader("📋 Data Parkir Kendaraan Saat Ini")
data = parkir.all_data()
df = parkir.to_df(data)
st.dataframe(df, use_container_width=True, hide_index=True)

# ===============================
#           KPI SUMMARY
# ===============================
st.subheader("📊 Statistik Bisnis Parkir")
if data:
    total_pendapatan = sum([d.biaya_parkir for d in data])
    jml_mobil = len([d for d in data if d.jenis_kendaraan == "Mobil"])
    jml_motor = len([d for d in data if d.jenis_kendaraan == "Motor"])
    colA, colB, colC = st.columns(3)
    colA.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    colB.metric("Jumlah Mobil", jml_mobil)
    colC.metric("Jumlah Motor", jml_motor)
else:
    st.info("Belum ada data parkir yang tercatat.")

# ===============================
#     Kendaraan parkir lama > 24 jam
# ===============================
long_park = parkir.check_long_park()
if long_park:
    st.subheader("⚠️ Kendaraan Parkir Lama (> 24 jam)")
    # Sortir berdasarkan durasi terlama
    long_park.sort(key=lambda x: x.durasi_parkir, reverse=True)
    st.table(parkir.to_df(long_park))
