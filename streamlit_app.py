import streamlit as st
import random
import string
import json # Tambahan: Untuk File Handling
from datetime import datetime, timedelta
import pandas as pd
import os # Tambahan: Untuk operasi file

# Nama file untuk menyimpan data
FILE_PARKIR = 'parking_data.json'

# ===============================
#       DATA MODEL (LINKED LIST & OOP Lanjutan)
# ===============================

# Kelas Dasar (Parent Class) untuk demonstrasi Inheritance
class Kendaraan:
    """Kelas dasar untuk kendaraan, mendemonstrasikan Basic OOP."""
    def __init__(self, nomor_polisi, jenis_kendaraan):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        self._tarif_dasar = 0  # Contoh variabel yang 'private'
    
    def get_tarif_dasar(self):
        """Method untuk mendapatkan tarif dasar, bisa di-override."""
        return self._tarif_dasar

# Node mewarisi dari Kendaraan (Inheritance)
class Node(Kendaraan):
    """Representasi data parkir, menggunakan Linked List Node."""
    # Override constructor
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk_str):
        # Memanggil constructor Parent Class
        super().__init__(nomor_polisi, jenis_kendaraan)
        
        # Inisialisasi properti waktu
        self.waktu_masuk = datetime.strptime(waktu_masuk_str, "%H:%M")

        # Simulasi Waktu Keluar & Durasi
        lama = random.randint(30, 720)  # 30 menit – 12 jam
        self.waktu_keluar = self.waktu_masuk + timedelta(minutes=lama)
        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        
        # Tambahan untuk data bisnis
        self.biaya_parkir = self.hit_biaya()
        self.status_pembayaran = "Belum Bayar" # Tambahan: Status Pembayaran
        self.metode_bayar = None # Tambahan: Metode Pembayaran
        
        self.next = None

    # Override method dari Parent Class (Polymorphism)
    def get_tarif_dasar(self):
        if self.jenis_kendaraan == "Mobil":
            return 5000
        return 3000

    def hit_biaya(self):
        """Menghitung biaya parkir berdasarkan durasi dan jenis kendaraan."""
        # Menghitung jam penuh (minimal 1 jam)
        jam_total = int(self.durasi_parkir.total_seconds() // 3600)
        jam_total = max(1, jam_total)
        
        tarif_dasar = self.get_tarif_dasar() # Menggunakan Polymorphism
        tarif_per_jam_berikutnya = 0
        
        if self.jenis_kendaraan == "Mobil":
            tarif_per_jam_berikutnya = 3000
        else: # Motor
            tarif_per_jam_berikutnya = 2000
        
        # Tarif: Tarif Dasar (jam pertama) + (Jam total - 1) * Tarif per jam berikutnya
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
        self.load_data() # Tambahan: Memuat data saat inisialisasi

    # Tambahan: File Handling (Load Data)
    def load_data(self):
        """Memuat data dari FILE_PARKIR (JSON) saat aplikasi dimulai."""
        if os.path.exists(FILE_PARKIR):
            try:
                with open(FILE_PARKIR, 'r') as f:
                    data_list = json.load(f)
                    for data in data_list:
                        # Membuat node dari data yang dimuat
                        node = Node(data['nomor_polisi'], data['jenis_kendaraan'], data['waktu_masuk'])
                        # Memperbarui properti yang tidak terhitung otomatis
                        node.waktu_keluar = datetime.strptime(data['waktu_keluar'], "%H:%M")
                        node.durasi_parkir = node.waktu_keluar - node.waktu_masuk
                        node.biaya_parkir = node.hit_biaya() 
                        node.status_pembayaran = data['status_pembayaran']
                        node.metode_bayar = data['metode_bayar']
                        
                        # Menambahkan node ke linked list
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
        # Jika file tidak ada, head tetap None (Linked List kosong)

    # Tambahan: File Handling (Save Data)
    def save_data(self):
        """Menyimpan data Linked List ke FILE_PARKIR (JSON)."""
        data_to_save = [d.to_dict() for d in self.all_data()]
        try:
            with open(FILE_PARKIR, 'w') as f:
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            st.error(f"Gagal menyimpan data ke file: {e}")

    # Method Linked List (Add)
    def add(self, nomor_polisi, jenis, waktu):
        # Pengecekan duplikasi
        if self.search(nomor_polisi):
            return False # Tidak diizinkan menambah data yang sudah ada
            
        node = Node(nomor_polisi, jenis, waktu)
        if not self.head:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node
            
        self.save_data() # Simpan setelah penambahan
        return True

    # Method Linked List (Search)
    def search(self, nomor_polisi):
        cur = self.head
        while cur:
            if cur.nomor_polisi == nomor_polisi:
                return cur
            cur = cur.next
        return None

    # Method Linked List (Delete)
    def delete(self, nomor_polisi):
        if not self.head:
            return False

        if self.head.nomor_polisi == nomor_polisi:
            self.head = self.head.next
            self.save_data() # Simpan setelah penghapusan
            return True

        cur = self.head
        while cur.next:
            if cur.next.nomor_polisi == nomor_polisi:
                cur.next = cur.next.next
                self.save_data() # Simpan setelah penghapusan
                return True
            cur = cur.next
        return False
        
    # Tambahan: Method untuk Pembayaran
    def bayar(self, nomor_polisi, metode):
        node = self.search(nomor_polisi)
        if node and node.status_pembayaran == "Belum Bayar":
            node.status_pembayaran = "Lunas"
            node.metode_bayar = metode
            self.save_data() # Simpan setelah pembayaran
            return True
        return False

    # Method Linked List (All Data)
    def all_data(self):
        data = []
        cur = self.head
        while cur:
            data.append(cur)
            cur = cur.next
        return data

    # Method to DataFrame
    def to_df(self, data_list):
        return pd.DataFrame([
            {
                "Nomor Polisi": d.nomor_polisi,
                "Jenis": d.jenis_kendaraan,
                "Masuk": d.waktu_masuk.strftime("%H:%M"),
                "Keluar": d.waktu_keluar.strftime("%H:%M"),
                "Durasi": str(d.durasi_parkir).split('.')[0], # Durasi tanpa milidetik
                "Biaya (Rp)": f"Rp {d.biaya_parkir:,}",
                "Pembayaran": d.status_pembayaran, # Tambahan
                "Metode": d.metode_bayar if d.metode_bayar else "-" # Tambahan
            }
            for d in data_list
        ])


# ===============================
#       STREAMLIT UI
# ===============================

st.set_page_config(page_title="Manajemen Parkir Bisnis", layout="wide")
st.title("🏢 Sistem Manajemen Data Parkir (Lengkap)")

# Init Session
if "parkir" not in st.session_state:
    st.session_state.parkir = DataParkir()

parkir = st.session_state.parkir

# Tambahan: Dictionary untuk Metode Pembayaran
METODE_PEMBAYARAN = { # Contoh penggunaan Dictionary
    "Tunai": "Cash", 
    "QRIS": "Digital Payment", 
    "Debit/Kredit": "Card Payment"
}


# ===============================
#   Generate Sample Data
# ===============================

def generate_data():
    jenis = ["Mobil", "Motor"]
    for i in range(20):
        # Buat nomor polisi unik
        nomor = f"B {random.randint(1000,9999)} {''.join(random.choices(string.ascii_uppercase, k=3))}"
        j = random.choice(jenis)
        
        # Simulasi waktu (6 pagi hingga 10 malam)
        waktu_jam = random.randint(6, 22)
        waktu_menit = random.randint(0, 59)
        w = f"{waktu_jam:02d}:{waktu_menit:02d}"
        
        # Tambah ke Linked List (jika berhasil)
        parkir.add(nomor, j, w)


with st.expander("⚙️ Simulasi dan Pengaturan"):
    if st.button("Generate Data Parkir (Simulasi Bisnis)"):
        generate_data()
        st.success("Data simulasi berhasil ditambahkan dan disimpan!")
        
    if st.button("Hapus Semua Data (Reset)"):
        if os.path.exists(FILE_PARKIR):
            os.remove(FILE_PARKIR)
        st.session_state.parkir = DataParkir() # Inisialisasi ulang
        parkir = st.session_state.parkir
        st.success("Semua data parkir berhasil dihapus!")


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
    # Waktu masuk default adalah waktu saat ini (untuk bisnis nyata)
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
    bayar_metode = st.selectbox("Metode Pembayaran", list(METODE_PEMBAYARAN.keys()), key="bayar_metode")
with col_bayar3:
    st.write(" ") # Spacer
    st.write(" ") # Spacer
    if st.button("Proses Pembayaran"):
        if not bayar_nopol.strip():
            st.error("Nomor Polisi wajib diisi untuk pembayaran.")
        else:
            nopol_bayar = bayar_nopol.strip().upper()
            node = parkir.search(nopol_bayar)
            if node:
                if node.status_pembayaran == "Lunas":
                    st.warning(f"Nomor Polisi **{nopol_bayar}** sudah lunas.")
                else:
                    if parkir.bayar(nopol_bayar, bayar_metode):
                        st.success(f"Pembayaran **Lunas** untuk **{nopol_bayar}** sebesar **Rp {node.biaya_parkir:,}** dengan metode **{bayar_metode}**.")
                        st.balloons()
                    else:
                        st.error(f"Gagal memproses pembayaran untuk **{nopol_bayar}**.")
            else:
                st.error(f"Nomor Polisi **{nopol_bayar}** tidak ditemukan.")


# ===============================
#       SEARCH / DELETE
# ===============================

st.subheader("🔍 Cari atau Hapus Data Parkir")

search_key = st.text_input("Cari berdasarkan Nomor Polisi", key="search_nopol")

c1, c2 = st.columns(2)

with c1:
    if st.button("Cari Data"):
        result = parkir.search(search_key.strip().upper())
        if result:
            st.info(
                f"### **Data Ditemukan!**\n\n"
                f"*Nomor Polisi:* **{result.nomor_polisi}**\n"
                f"*Jenis:* {result.jenis_kendaraan}\n"
                f"*Masuk:* {result.waktu_masuk.strftime('%H:%M')}\n"
                f"*Keluar:* {result.waktu_keluar.strftime('%H:%M')}\n"
                f"*Durasi:* {str(result.durasi_parkir).split('.')[0]}\n"
                f"*Biaya:* **Rp {result.biaya_parkir:,}**\n"
                f"*Status Bayar:* **{result.status_pembayaran}**\n"
                f"*Metode Bayar:* {result.metode_bayar if result.metode_bayar else '-'}"
            )
        else:
            st.warning("Data tidak ditemukan.")

with c2:
    if st.button("Hapus Data"):
        nopol_hapus = search_key.strip().upper()
        if parkir.delete(nopol_hapus):
            st.success(f"Data **{nopol_hapus}** berhasil dihapus dan **disimpan**!")
        else:
            st.error("Nomor polisi tidak ditemukan.")


# ===============================
#       NOTIFIKASI (Flow Control Lanjut)
# ===============================

st.subheader("⚠️ Notifikasi dan Peringatan")

# Simulasi waktu saat ini untuk perbandingan
waktu_sekarang = datetime.now()
kendaraan_lama = []

# Loop untuk mencari kendaraan yang parkir > 24 jam (simulasi jam 8 pagi di hari yang berbeda)
# Perhatian: Karena waktu keluar disimulasikan, kita hanya bisa membandingkan durasi
DURASI_MAKS = timedelta(hours=24) 

cur = parkir.head
while cur: # Loop melalui Linked List
    if cur.durasi_parkir > DURASI_MAKS:
        kendaraan_lama.append(cur)
    cur = cur.next

if kendaraan_lama:
    st.error(f"🛑 **{len(kendaraan_lama)}** Kendaraan parkir lebih dari {str(DURASI_MAKS).split('.')[0]}!")
    for k in kendaraan_lama:
        st.write(f"- **{k.nomor_polisi}** ({k.jenis_kendaraan}). Durasi: **{str(k.durasi_parkir).split('.')[0]}**.")
else:
    st.success("✅ Tidak ada kendaraan yang parkir lebih dari 24 jam (simulasi).")


# ===============================
#       TABEL DATA
# ===============================

st.subheader("📋 Data Parkir Kendaraan")

data = parkir.all_data()
if data:
    df = parkir.to_df(data)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Belum ada data parkir.")


# ===============================
#           KPI SUMMARY
# ===============================

st.subheader("📊 Statistik Bisnis Parkir")

# Menggunakan List Comprehension untuk perhitungan efisien
total_pendapatan = sum([d.biaya_parkir for d in data if d.status_pembayaran == "Lunas"]) # Hanya hitung yang Lunas
jml_mobil = len([d for d in data if d.jenis_kendaraan == "Mobil"])
jml_motor = len([d for d in data if d.jenis_kendaraan == "Motor"])
jml_lunas = len([d for d in data if d.status_pembayaran == "Lunas"])
jml_belum_bayar = len(data) - jml_lunas

colA, colB, colC, colD, colE = st.columns(5)

colA.metric("Total Kendaraan", len(data))
colB.metric("Jumlah Mobil", jml_mobil)
colC.metric("Jumlah Motor", jml_motor)
colD.metric("Lunas", jml_lunas)
colE.metric("Belum Bayar", jml_belum_bayar)

st.metric("Total Pendapatan (Lunas)", f"Rp {total_pendapatan:,}")
