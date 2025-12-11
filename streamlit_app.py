import streamlit as st
import json 
from datetime import datetime, timedelta
import pandas as pd
import os 
from dateutil.parser import parse

# Nama file untuk menyimpan data
FILE_PARKIR = 'parking_data.json'

# ===============================
#       DATA MODEL (LINKED LIST & OOP Lanjutan)
# ===============================

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
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk_dt):
        super().__init__(nomor_polisi, jenis_kendaraan)
        
        # Waktu masuk sekarang disimpan sebagai objek datetime, bukan string waktu saja
        self.waktu_masuk = waktu_masuk_dt

        # Properti ini diinisialisasi None dan diisi saat proses checkout/pembayaran
        self.waktu_keluar = None 
        self.durasi_parkir = None 
        self.biaya_parkir = 0
        
        self.status_pembayaran = "Parkir Aktif" # Status baru
        self.metode_bayar = None 
        
        self.next = None

    def get_tarif_dasar(self):
        if self.jenis_kendaraan == "Mobil":
            return 5000
        return 3000

    def hit_biaya(self, durasi_parkir):
        """Menghitung biaya parkir berdasarkan durasi."""
        
        # Pastikan durasi adalah timedelta sebelum menghitung
        if not isinstance(durasi_parkir, timedelta):
             return 0

        total_seconds = durasi_parkir.total_seconds()
        
        # Hitung jam total (Pembulatan ke atas ke jam terdekat)
        # Contoh: 1 jam 1 menit dihitung 2 jam.
        jam_total = int(total_seconds // 3600)
        if total_seconds % 3600 > 0:
            jam_total += 1
        
        jam_total = max(1, jam_total) # Minimal 1 jam
        
        tarif_dasar = self.get_tarif_dasar() 
        tarif_per_jam_berikutnya = 0
        
        if self.jenis_kendaraan == "Mobil":
            tarif_per_jam_berikutnya = 3000
        else:
            tarif_per_jam_berikutnya = 2000
        
        # Biaya = Tarif Jam Pertama + (Jam Total - 1) * Tarif Per Jam Berikutnya
        biaya = tarif_dasar + (jam_total - 1) * tarif_per_jam_berikutnya
        return biaya
        
    def to_dict(self):
        """Fungsi pembantu untuk konversi ke Dictionary untuk File Handling (JSON)."""
        return {
            "nomor_polisi": self.nomor_polisi,
            "jenis_kendaraan": self.jenis_kendaraan,
            # Simpan waktu lengkap (date dan time) untuk perhitungan yang akurat
            "waktu_masuk": self.waktu_masuk.isoformat(), 
            "waktu_keluar": self.waktu_keluar.isoformat() if self.waktu_keluar else None,
            "biaya_parkir": self.biaya_parkir,
            "status_pembayaran": self.status_pembayaran,
            "metode_bayar": self.metode_bayar
        }

    # Method baru untuk memproses checkout
    def checkout(self, waktu_keluar, metode_bayar):
        """Mengisi data keluar dan menghitung biaya parkir."""
        if self.status_pembayaran == "Parkir Aktif":
            self.waktu_keluar = waktu_keluar
            self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
            self.biaya_parkir = self.hit_biaya(self.durasi_parkir)
            self.status_pembayaran = "Lunas"
            self.metode_bayar = metode_bayar
            return True
        return False


class DataParkir:
    """Class utama untuk mengelola data parkir menggunakan Linked List."""
    def __init__(self):
        self.head = None
        self.load_data()

    # File Handling (Load Data)
    def load_data(self):
        """Memuat data dari FILE_PARKIR (JSON)."""
        if os.path.exists(FILE_PARKIR):
            try:
                with open(FILE_PARKIR, 'r') as f:
                    data_list = json.load(f)
                    for data in data_list:
                        # Parsing waktu masuk (wajib ada)
                        waktu_masuk_dt = parse(data['waktu_masuk'])
                        node = Node(data['nomor_polisi'], data['jenis_kendaraan'], waktu_masuk_dt)
                        
                        # Memuat properti yang mungkin sudah diisi (Lunas)
                        node.status_pembayaran = data.get('status_pembayaran', "Parkir Aktif")
                        node.biaya_parkir = data.get('biaya_parkir', 0)
                        node.metode_bayar = data.get('metode_bayar', None)
                        
                        waktu_keluar_iso = data.get('waktu_keluar')
                        if waktu_keluar_iso:
                            node.waktu_keluar = parse(waktu_keluar_iso)
                            node.durasi_parkir = node.waktu_keluar - node.waktu_masuk
                        
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

    # Method Linked List (Add)
    def add(self, nomor_polisi, jenis, waktu_masuk_str):
        if self.search(nomor_polisi, status="Aktif"):
            return False # Kendaraan masih aktif

        try:
            # Menggunakan parse untuk membaca waktu masuk penuh (date dan time)
            waktu_masuk_dt = parse(waktu_masuk_str)
        except:
            return False # Format waktu salah
            
        node = Node(nomor_polisi, jenis, waktu_masuk_dt)
        if not self.head:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node
            
        self.save_data()
        return True

    # Method Linked List (Search)
    def search(self, nomor_polisi, status=None):
        cur = self.head
        while cur:
            if cur.nomor_polisi == nomor_polisi:
                if status == "Aktif" and cur.status_pembayaran == "Parkir Aktif":
                    return cur
                elif status is None: # Cari semua status
                    return cur
            cur = cur.next
        return None
    
    # Method untuk Pembayaran/Checkout
    def checkout_kendaraan(self, nomor_polisi, waktu_keluar_str, metode):
        node = self.search(nomor_polisi, status="Aktif")
        
        if node and node.status_pembayaran == "Parkir Aktif":
            try:
                waktu_keluar_dt = parse(waktu_keluar_str)
            except:
                return "Format Waktu Keluar Salah"

            if waktu_keluar_dt < node.waktu_masuk:
                return "Waktu Keluar Lebih Awal dari Waktu Masuk"

            if node.checkout(waktu_keluar_dt, metode):
                self.save_data() 
                return node
            else:
                return "Gagal Checkout"
        return "Kendaraan Tidak Aktif"

    # Method Linked List (Delete)
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
                # Format waktu yang lebih lengkap
                "Masuk": d.waktu_masuk.strftime("%Y-%m-%d %H:%M"),
                "Keluar": d.waktu_keluar.strftime("%Y-%m-%d %H:%M") if d.waktu_keluar else "N/A",
                "Durasi": str(d.durasi_parkir).split('.')[0] if d.durasi_parkir else "Aktif",
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
st.title("🏢 Sistem Manajemen Data Parkir (Real-Time)")

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
#       FITUR RESET DATA 
# ===============================

st.subheader("🗑️ Kelola Data Persisten")

if st.button("Hapus Semua Data Parkir (Reset File)", help="Menghapus semua data, termasuk yang Lunas/Aktif, yang tersimpan di file parking_data.json."):
    if os.path.exists(FILE_PARKIR):
        os.remove(FILE_PARKIR)
    st.session_state.parkir = DataParkir() 
    st.success("Semua data parkir berhasil dihapus! Aplikasi direset.")
    st.rerun() 


# ===============================
#       INPUT KENDARAAN MASUK
# ===============================

st.subheader("➕ 1. Input Kendaraan Masuk")

col1, col2, col3 = st.columns(3)

with col1:
    inp_nopol = st.text_input("Nomor Polisi", key="inp_nopol_add").strip().upper()
with col2:
    inp_jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"], key="inp_jenis_add")
with col3:
    now_dt = datetime.now().strftime("%Y-%m-%d %H:%M") 
    inp_waktu = st.text_input("Waktu Masuk (YYYY-MM-DD HH:MM)", now_dt, key="inp_waktu_add").strip()

if st.button("Tambah Kendaraan Masuk"):
    if inp_nopol and inp_waktu:
        if parkir.add(inp_nopol, inp_jenis, inp_waktu):
            st.success(f"Kendaraan **{inp_nopol}** ({inp_jenis}) Masuk pada **{inp_waktu}**. Status: Parkir Aktif.")
        else:
            st.warning(f"Nomor Polisi **{inp_nopol}** sudah ada dalam status Parkir Aktif atau format waktu salah.")
    else:
        st.error("Nomor polisi dan Waktu Masuk wajib diisi.")


# ===============================
#       CHECKOUT KENDARAAN KELUAR (STEP 2: Pembayaran & Checkout)
# ===============================

st.subheader("💳 2. Checkout & Pembayaran Kendaraan Keluar")

col_bayar1, col_bayar2, col_bayar3 = st.columns(3)

with col_bayar1:
    bayar_nopol = st.text_input("Nomor Polisi Kendaraan Keluar", key="bayar_nopol").strip().upper()
    
    # Tampilkan estimasi biaya jika nopol aktif ditemukan
    node_aktif = parkir.search(bayar_nopol, status="Aktif")
    if node_aktif:
        st.info(f"Kendaraan ditemukan. Masuk: {node_aktif.waktu_masuk.strftime('%H:%M')}")
        
with col_bayar2:
    now_dt_out = datetime.now().strftime("%Y-%m-%d %H:%M") 
    bayar_waktu_keluar = st.text_input("Waktu Keluar (YYYY-MM-DD HH:MM)", now_dt_out, key="bayar_waktu_keluar").strip()
    
with col_bayar3:
    bayar_metode = st.selectbox("Metode Pembayaran", list(METODE_PEMBAYARAN.keys()), key="bayar_metode")
    st.write(" ")
    
    if st.button("Proses Checkout"):
        if not bayar_nopol:
            st.error("Nomor Polisi wajib diisi untuk pembayaran.")
        else:
            result = parkir.checkout_kendaraan(bayar_nopol, bayar_waktu_keluar, bayar_metode)
            
            if isinstance(result, str):
                st.error(f"Gagal Checkout: {result}")
            else:
                st.success(
                    f"Checkout Berhasil! **{result.nomor_polisi}** Lunas.\n\n"
                    f"Durasi: **{str(result.durasi_parkir).split('.')[0]}**\n"
                    f"Total Biaya: **Rp {result.biaya_parkir:,}** ({result.metode_bayar})"
                )
                st.balloons()


# ===============================
#       SEARCH / DELETE (DATA LUNAS)
# ===============================

st.subheader("🔍 Cari atau Hapus Data Historis (Lunas)")

search_key = st.text_input("Cari semua data berdasarkan Nomor Polisi", key="search_nopol")

col_s1, col_s2 = st.columns(2)

with col_s1:
    if st.button("Cari Data"):
        result = parkir.search(search_key.strip().upper(), status=None) # Cari semua status
        if result:
            durasi_display = str(result.durasi_parkir).split('.')[0] if result.durasi_parkir else "Aktif"
            st.info(
                f"### **Data Ditemukan!**\n\n"
                f"*Nomor Polisi:* **{result.nomor_polisi}**\n"
                f"*Jenis:* {result.jenis_kendaraan}\n"
                f"*Masuk:* {result.waktu_masuk.strftime('%Y-%m-%d %H:%M')}\n"
                f"*Keluar:* {result.waktu_keluar.strftime('%Y-%m-%d %H:%M') if result.waktu_keluar else 'N/A'}\n"
                f"*Durasi:* {durasi_display}\n"
                f"*Biaya:* **Rp {result.biaya_parkir:,}**\n"
                f"*Status Bayar:* **{result.status_pembayaran}**\n"
                f"*Metode Bayar:* {result.metode_bayar if result.metode_bayar else '-'}"
            )
        else:
            st.warning("Data tidak ditemukan.")

with col_s2:
    if st.button("Hapus Data Historis Permanen"):
        nopol_hapus = search_key.strip().upper()
        if parkir.delete(nopol_hapus):
            st.success(f"Data **{nopol_hapus}** berhasil dihapus dan **disimpan**!")
        else:
            st.error("Nomor polisi tidak ditemukan.")


# --- Visual Separator ---
st.markdown("---")


# ===============================
#       TABEL DATA
# ===============================

st.subheader("📋 Data Parkir Kendaraan")

data = park
