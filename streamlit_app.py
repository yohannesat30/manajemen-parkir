import streamlit as st
import random
import string
import json 
from datetime import datetime, timedelta
import pandas as pd
import os 

# Nama file untuk menyimpan data
FILE_PARKIR = 'parking_data.json'

# ===============================
#       DATA MODEL (LINKED LIST & OOP Lanjutan)
# ===============================

# ... (Class Kendaraan, Class Node, Class DataParkir tetap sama seperti sebelumnya) ...
# [Bagian ini dipertahankan karena berisi logika inti dan OOP]

class Kendaraan:
    """Kelas dasar untuk kendaraan, mendemonstrasikan Basic OOP."""
    def __init__(self, nomor_polisi, jenis_kendaraan):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        self._tarif_dasar = 0
    
    def get_tarif_dasar(self):
        """Method untuk mendapatkan tarif dasar, bisa di-override."""
        return self._tarif_dasar

class Node(Kendaraan):
    """Representasi data parkir, menggunakan Linked List Node."""
    # Override constructor
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk_str):
        super().__init__(nomor_polisi, jenis_kendaraan)
        
        self.waktu_masuk = datetime.strptime(waktu_masuk_str, "%H:%M")

        lama = random.randint(30, 720)  
        self.waktu_keluar = self.waktu_masuk + timedelta(minutes=lama)
        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        
        self.biaya_parkir = self.hit_biaya()
        self.status_pembayaran = "Belum Bayar" 
        self.metode_bayar = None 
        
        self.next = None

    def get_tarif_dasar(self):
        if self.jenis_kendaraan == "Mobil":
            return 5000
        return 3000

    def hit_biaya(self):
        """Menghitung biaya parkir berdasarkan durasi dan jenis kendaraan."""
        jam_total = int(self.durasi_parkir.total_seconds() // 3600)
        jam_total = max(1, jam_total)
        
        tarif_dasar = self.get_tarif_dasar() 
        tarif_per_jam_berikutnya = 0
        
        if self.jenis_kendaraan == "Mobil":
            tarif_per_jam_berikutnya = 3000
        else:
            tarif_per_jam_berikutnya = 2000
        
        biaya = tarif_dasar + (jam_total - 1) * tarif_per_jam_berikutnya
        return biaya
        
    def to_dict(self):
        """Fungsi pembantu untuk konversi ke Dictionary untuk File Handling (JSON)."""
        return {
            "nomor_polisi": self.nomor_polisi,
            "jenis_kendaraan": self.jenis_kendaraan,
            "waktu_masuk": self.waktu_masuk.strftime("%H:%M"),
            "waktu_keluar": self.waktu_keluar.strftime("%H:%M"),
            "status_pembayaran": self.status_pembayaran,
            "metode_bayar": self.metode_bayar
        }


class DataParkir:
    """Class utama untuk mengelola data parkir menggunakan Linked List."""
    def __init__(self):
        self.head = None
        self.load_data()

    # File Handling (Load Data)
    def load_data(self):
        """Memuat data dari FILE_PARKIR (JSON) saat aplikasi dimulai."""
        if os.path.exists(FILE_PARKIR):
            try:
                with open(FILE_PARKIR, 'r') as f:
                    data_list = json.load(f)
                    for data in data_list:
                        node = Node(data['nomor_polisi'], data['jenis_kendaraan'], data['waktu_masuk'])
                        node.waktu_keluar = datetime.strptime(data['waktu_keluar'], "%H:%M")
                        node.durasi_parkir = node.waktu_keluar - node.waktu_masuk
                        node.biaya_parkir = node.hit_biaya() 
                        node.status_pembayaran = data['status_pembayaran']
                        node.metode_bayar = data['metode_bayar']
                        
                        if not self.head:
                            self.head = node
                        else:
                            cur = self.head
                            while cur.next:
                                cur = cur.next
                            cur.next = node
            except json.JSONDecodeError:
                st.warning("Gagal memuat data parkir (file JSON rusak).")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memuat data: {e}")

    # File Handling (Save Data)
    def save_data(self):
        """Menyimpan data Linked List ke FILE_PARKIR (JSON)."""
        data_to_save = [d.to_dict() for d in self.all_data()]
        try:
            with open(FILE_PARKIR, 'w') as f:
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            st.error(f"Gagal menyimpan data ke file: {e}")

    def add(self, nomor_polisi, jenis, waktu):
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
            
        self.save_data()
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
            self.save_data()
            return True

        cur = self.head
        while cur.next:
            if cur.next.nomor_polisi == nomor_polisi:
                cur.next = cur.next.next
                self.save_data()
                return True
            cur = cur.next
        return False
        
    def bayar(self, nomor_polisi, metode):
        node = self.search(nomor_polisi)
        if node and node.status_pembayaran == "Belum Bayar":
            node.status_pembayaran = "Lunas"
            node.metode_bayar = metode
            self.save_data() 
            return True
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
                "Durasi": str(d.durasi_parkir).split('.')[0],
                "Biaya (Rp)": f"Rp {d.biaya_parkir:,}",
                "Pembayaran": d.status_pembayaran,
                "Metode": d.metode_bayar if d.metode_bayar else "-"
            }
            for d in data_list
        ])


# ===============================
#       STREAMLIT UI
# ===============================

st.set_page_config(page_title="Manajemen Parkir Bisnis", layout="wide")
st.title("🏢 Sistem Manajemen Data Parkir")

# Init Session
if "parkir" not in st.session_state:
    st.session_state.parkir = DataParkir()

parkir = st.session_state.parkir

METODE_PEMBAYARAN = {
    "Tunai": "Cash", 
    "QRIS": "Digital Payment", 
    "Debit/Kredit": "Card Payment"
}

# ===============================
#       FITUR RESET DATA (PENAMBAHAN BARU)
# ===============================
# 

st.subheader("🗑️ Kelola Data Persisten")

if st.button("Hapus Semua Data Parkir (Reset File)", help="Ini akan menghapus semua data yang tersimpan di memori dan file parking_data.json."):
    if os.path.exists(FILE_PARKIR):
        os.remove(FILE_PARKIR)
    # Mereset session state dan Linked List
    st.session_state.parkir = DataParkir() 
    st.success("Semua data parkir berhasil dihapus! Aplikasi direset.")
    st.rerun() # Memuat ulang aplikasi untuk tampilan yang bersih


# ===============================
#       INPUT DATA
# ===============================

st.subheader("➕ Input Kendaraan Masuk")

col1, col2, col3 = st.columns(3)

with col1:
    inp_nopol = st.text_input("Nomor Polisi", key="inp_nopol_add")
with col2:
    inp_jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"], key="inp_jenis_add")
with col3:
    now_time = datetime.now().strftime("%H:%M") 
    inp_waktu = st.text_input("Waktu Masuk (HH:MM)", now_time, key="inp_waktu_add")

if st.button("Tambah Data Kendaraan Masuk"):
    if inp_nopol:
        if parkir.add(inp_nopol.strip().upper(), inp_jenis, inp_waktu.strip()):
            st.success(f"Data parkir untuk **{inp_nopol.strip().upper()}** ditambahkan dan **disimpan**!")
        else:
            st.warning(f"Nomor Polisi **{inp_nopol.strip().upper()}** sudah ada!")
    else:
        st.error("Nomor polisi wajib diisi.")


# ===============================
#       PEMBAYARAN
# ===============================

st.subheader("💳 Pembayaran Kendaraan Keluar")

col_bayar1, col_bayar2, col_bayar3 = st.columns(3)

with col_bayar1:
    bayar_nopol = st.text_input("Nomor Polisi Kendaraan Keluar", key="bayar_nopol")
with col_bayar2:
    bayar_metode = st.selectbox("Metode Pembayaran", list(
