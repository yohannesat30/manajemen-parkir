import streamlit as st
import random
from datetime import datetime, timedelta
import pandas as pd
import os

# ===============================
#     DATA MODEL (LINKED LIST)
# ===============================
class Node:
    """Representasi satu kendaraan (Node) dalam Linked List parkir."""
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        
        try:
            time_obj = datetime.strptime(waktu_masuk, "%H:%M").time()
            self.waktu_masuk = datetime.combine(datetime.now().date(), time_obj)
        except ValueError:
            self.waktu_masuk = datetime.now()

        # Data ini diinisialisasi kosong dan akan diisi saat checkout
        self.waktu_keluar = None 
        self.durasi_parkir = None
        self.biaya_parkir = 0
        self.metode_bayar = None
        self.next = None

    def hit_biaya(self, durasi, jenis):
        """Menghitung biaya parkir berdasarkan durasi yang sudah pasti."""
        # total_seconds() // 3600 menghitung total jam bulat ke bawah
        jam_parkir = int(durasi.total_seconds() // 3600)
        
        # Hitung jam yang dikenakan biaya: (Pembulatan ke atas)
        jam = jam_parkir
        if durasi.total_seconds() % 3600 > 0:
            jam += 1
        jam = max(1, jam)
        
        # Logika Biaya: Jam pertama + (Jam sisanya * Tarif berikutnya)
        if jenis == "Mobil":
            # Tarif: Rp 5.000 (jam 1) + Rp 3.000 (jam berikutnya)
            return 5000 + (jam - 1) * 3000
        
        # Untuk Motor
        # Tarif: Rp 3.000 (jam 1) + Rp 2.000 (jam berikutnya)
        return 3000 + (jam - 1) * 2000

class DataParkir:
    """Manajemen data parkir menggunakan struktur Linked List."""
    def __init__(self):
        self.head = None
        
    # --- Operasi Linked List Dasar ---
    def add(self, nomor_polisi, jenis, waktu):
        # Cek duplikasi
        if self.search(nomor_polisi):
            return False
            
        node = Node(nomor_polisi, jenis, waktu)
        if not self.head:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node
        return True

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
        """Mengubah list Node menjadi Pandas DataFrame."""
        return pd.DataFrame([
            {
                "Nomor Polisi": d.nomor_polisi,
                "Jenis": d.jenis_kendaraan,
                "Masuk": d.waktu_masuk.strftime("%H:%M"),
                "Keluar": d.waktu_keluar.strftime("%H:%M") if d.waktu_keluar else "BELUM KELUAR",
                "Durasi": str(d.durasi_parkir).split('.')[0] if d.durasi_parkir else "-",
                "Biaya (Rp)": d.biaya_parkir if d.biaya_parkir else "-",
                "Metode Bayar": d.metode_bayar if d.metode_bayar else "PARKIR"
            }
            for d in data_list
        ])

    # ===============================
    #       Metode Checkout
    # ===============================
    def checkout(self, nomor_polisi, waktu_keluar_str, metode_bayar):
        node = self.search(nomor_polisi)
        if not node:
            return None 

        try:
            # 1. Tentukan Waktu Keluar
            time_obj_keluar = datetime.strptime(waktu_keluar_str, "%H:%M").time()
            waktu_keluar = datetime.combine(datetime.now().date(), time_obj_keluar) 

            # Handle kasus parkir melewati tengah malam
            if waktu_keluar < node.waktu_masuk:
                 waktu_keluar += timedelta(days=1)
            
            # 2. Hitung Durasi dan Biaya
            node.waktu_keluar = waktu_keluar
            node.durasi_parkir = node.waktu_keluar - node.waktu_masuk
            node.biaya_parkir = node.hit_biaya(node.durasi_parkir, node.jenis_kendaraan) 
            node.metode_bayar = metode_bayar
            
            # 3. Simpan Data Checkout untuk ditampilkan
            data_checkout = {
                "nopol": node.nomor_polisi,
                "jenis": node.jenis_kendaraan,
                "masuk": node.waktu_masuk.strftime("%H:%M"),
                "keluar": node.waktu_keluar.strftime("%H:%M"),
                "durasi": str(node.durasi_parkir).split('.')[0],
                "biaya": node.biaya_parkir,
                "bayar": node.metode_bayar
            }

            # 4. Hapus Node dari Linked List (Kendaraan sudah keluar)
            self.delete(nomor_polisi)
            
            return data_checkout
            
        except ValueError:
            return "Format waktu salah"

    # ===============================
    #       File Handling
    # ===============================
    def save_to_file(self, filename="data_parkir.csv"):
        """Menyimpan data parkir (yang masih ada) ke file CSV."""
        data_list = self.all_data()
        if data_list:
            df = self.to_df(data_list)
            df.to_csv(filename, index=False)
        elif os.path.exists(filename):
            os.remove(filename)

    def check_long_park(self):
        """Mengecek kendaraan yang parkir lebih dari 24 jam."""
        long_park = []
        batas_24_jam = timedelta(hours=24)
        for d in self.all_data():
            if not d.waktu_keluar:
                durasi_saat_ini = datetime.now() - d.waktu_masuk
                if durasi_saat_ini > batas_24_jam:
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

# ===============================
#         INPUT DATA (MASUK)
# ===============================
st.subheader("➕ Input Kendaraan Masuk")
col1, col2, col3 = st.columns(3)
with col1:
    inp_nopol = st.text_input("Nomor Polisi", key="nopol_input").upper()
with col2:
    inp_jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"], key="jenis_input")
with col3:
    default_time = datetime.now().strftime("%H:%M")
    inp_waktu = st.text_input("Waktu Masuk (HH:MM)", default_time, key="waktu_input")

if st.button("Tambah Data (MASUK)"):
    if inp_nopol and inp_waktu:
        try:
            datetime.strptime(inp_waktu, "%H:%M")
            if parkir.add(inp_nopol, inp_jenis, inp_waktu):
                parkir.save_to_file()
                st.success(f"Data parkir untuk **{inp_nopol}** dicatat!")
                st.rerun() 
            else:
                st.warning(f"Nomor Polisi **{inp_nopol}** sudah ada di area parkir.")
            
        except ValueError:
            st.error("Format Waktu Masuk harus HH:MM (contoh: 08:00).")
    else:
        st.error("Nomor polisi dan Waktu Masuk wajib diisi.")
        
# --- Fitur CARI Kendaraan (DIJAGA) ---
st.subheader("🔍 Cari Data Kendaraan Parkir")
search_key = st.text_input("Masukkan Nomor Polisi untuk Dicari").upper()

if st.button("Cari Kendaraan", key="btn_cari"):
    result = parkir.search(search_key)
    if result:
        # Hitung estimasi durasi dan biaya saat ini untuk ditampilkan
        durasi_estimasi = datetime.now() - result.waktu_masuk
        biaya_estimasi = result.hit_biaya(durasi_estimasi, result.jenis_kendaraan)
        
        st.info(
            f"**Nomor Polisi:** {result.nomor_polisi}\n"
            f"**Jenis:** {result.jenis_kendaraan}\n"
            f"**Waktu Masuk:** {result.waktu_masuk.strftime('%H:%M')}\n"
            f"**Durasi Estimasi Saat Ini:** {str(durasi_estimasi).split('.')[0]}\n"
            f"**Estimasi Biaya Saat Ini:** Rp {biaya_estimasi:,.0f}"
        )
    else:
        st.warning(f"Kendaraan dengan Nomor Polisi **{search_key}** tidak ditemukan di area parkir.")

# ===============================
#        CHECKOUT / KELUAR
# ===============================
st.subheader("🏁 Kendaraan Keluar (Checkout)")
co_col1, co_col2, co_col3 = st.columns(3)

with co_col1:
    co_nopol = st.text_input("Nomor Polisi Checkout").upper()
with co_col2:
    co_waktu = st.text_input("Waktu Keluar (HH:MM)", datetime.now().strftime("%H:%M"))
with co_col3:
    co_bayar = st.selectbox("Metode Pembayaran", ["Tunai", "E-wallet", "Kartu"])

if st.button("Proses Checkout"):
    if not co_nopol:
        st.error("Nomor polisi wajib diisi.")
    else:
        checkout_result = parkir.checkout(co_nopol, co_waktu, co_bayar)
        
        if checkout_result == "Format waktu salah":
            st.error("Format Waktu Keluar harus HH:MM.")
        elif not checkout_result:
            st.warning(f"Kendaraan dengan Nomor Polisi **{co_nopol}** tidak ditemukan atau sudah keluar.")
        else:
            # Tampilkan ringkasan pembayaran
            st.success(f"Checkout berhasil untuk {checkout_result['nopol']}!")
            st.metric("Total Biaya Parkir", f"Rp {checkout_result['biaya']:,.0f}")
            st.info(
                f"*Jenis:* {checkout_result.get('jenis', '-')}\n"
                f"*Durasi:* {checkout_result['durasi']}\n"
                f"*Waktu Masuk:* {checkout_result['masuk']}\n"
                f"*Waktu Keluar:* {checkout_result['keluar']}\n"
                f"*Dibayar Dengan:* **{checkout_result['bayar']}**"
            )
            parkir.save_to_file() 
            st.rerun()

# ===============================
#        TABEL DATA
# ===============================
st.subheader("📋 Data Kendaraan yang Masih Parkir")
data = parkir.all_data()
df = parkir.to_df(data)

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Area parkir saat ini kosong.")

# ===============================
#           KPI SUMMARY
# ===============================
st.subheader("📊 Statistik Parkir Saat Ini")
if data:
    jml_mobil = len([d for d in data if d.jenis_kendaraan == "Mobil"])
    jml_motor = len([d for d in data if d.jenis_kendaraan == "Motor"])
    colA, colB = st.columns(2)
    colA.metric("Jumlah Mobil Parkir", jml_mobil)
    colB.metric("Jumlah Motor Parkir", jml_motor)
else:
    st.info("Tidak ada kendaraan yang sedang parkir.")

# ===============================
#     Kendaraan parkir lama > 24 jam
# ===============================
long_park = parkir.check_long_park()
if long_park:
    st.subheader("⚠️ Kendaraan Parkir Lama (> 24 jam)")
    st.warning("Kendaraan berikut telah parkir lebih dari 24 jam.")
    
    long_park_data = []
    for d in long_park:
        durasi_saat_ini = datetime.now() - d.waktu_masuk
        long_park_data.append({
            "Nomor Polisi": d.nomor_polisi,
            "Jenis": d.jenis_kendaraan,
            "Masuk": d.waktu_masuk.strftime("%H:%M"),
            "Durasi Saat Ini": str(durasi_saat_ini).split('.')[0]
        })
    st.table(pd.DataFrame(long_park_data))
