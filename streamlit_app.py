import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd

# ===============================
#   MODEL & MANAGER
# ===============================
class VehicleRecord:
    """Representasi satu entri kendaraan parkir."""
    def __init__(self, nomor_polisi: str, jenis_kendaraan: str, waktu_masuk: str):
        self.nomor_polisi = nomor_polisi.strip().upper()
        self.jenis_kendaraan = jenis_kendaraan
        try:
            # Waktu masuk diparsing dari string format yang konsisten
            self.waktu_masuk = datetime.strptime(waktu_masuk, "%Y-%m-%d %H:%M")
        except:
            # Fallback jika parsing gagal
            self.waktu_masuk = datetime.now() 
            
        self.waktu_keluar = None
        self.durasi_parkir = None
        self.biaya_parkir = None
        self.paid = False
        self.payment_method = None
        self.payment_time = None

    def set_exit_now(self):
        """Mengatur waktu keluar sebagai waktu saat ini dan menghitung biaya."""
        self.waktu_keluar = datetime.now()
        self._calc_durasi_biaya()

    def _calc_durasi_biaya(self):
        """Kalkulasi durasi dan biaya parkir berdasarkan aturan tarif."""
        if not self.waktu_keluar:
            return
        
        dur = self.waktu_keluar - self.waktu_masuk
        self.durasi_parkir = dur
        
        # Hitung Jam Pembulatan ke atas (minimal 1 jam)
        total_seconds = dur.total_seconds()
        # Pembulatan ke atas: total_seconds / 3600, lalu di-ceil
        jam = int((total_seconds + 3599) // 3600) 
        jam = max(1, jam) 
        
        # Kalkulasi Biaya Parkir: Tarif Dasar + (Jam Tambahan * Tarif Per Jam)
        if self.jenis_kendaraan == "Mobil":
            # Jam pertama Rp 5000, jam berikutnya Rp 3000
            self.biaya_parkir = 5000 + (jam - 1) * 3000
        else: # Motor
            # Jam pertama Rp 3000, jam berikutnya Rp 2000
            self.biaya_parkir = 3000 + (jam - 1) * 2000

    def mark_paid(self, method: str):
        """Menandai record telah dibayar."""
        self.paid = True
        self.payment_method = method
        self.payment_time = datetime.now()

    def as_dict(self):
        """Mengembalikan data record sebagai dictionary untuk DataFrame/Display."""
        return {
            "Nomor Polisi": self.nomor_polisi,
            "Jenis": self.jenis_kendaraan,
            "Masuk": self.waktu_masuk.strftime("%Y-%m-%d %H:%M"),
            "Keluar": self.waktu_keluar.strftime("%Y-%m-%d %H:%M") if self.waktu_keluar else "",
            "Durasi": str(self.durasi_parkir).split('.')[0] if self.durasi_parkir else "", # Tampilkan tanpa microdetik
            "Biaya (Rp)": self.biaya_parkir or 0,
            "Paid": self.paid,
            "Payment Method": self.payment_method or ""
        }

class ParkingManager:
    """Mengelola semua record kendaraan parkir."""
    def __init__(self):
        self._records = []
        # Menggunakan dictionary untuk pencarian cepat berdasarkan Nomor Polisi
        self._index = {} 

    def add(self, nomor_polisi, jenis, waktu):
        """Menambahkan record kendaraan baru."""
        # Cek duplikasi: jika nopol sudah ada DAN belum keluar (waktu_keluar masih None), tolak.
        if nomor_polisi in self._index and not self._index[nomor_polisi].waktu_keluar:
             raise ValueError(f"Kendaraan dengan nopol {nomor_polisi} masih tercatat di dalam.")
             
        rec = VehicleRecord(nomor_polisi, jenis, waktu)
        self._records.append(rec)
        self._index[nomor_polisi] = rec
        return rec

    def get(self, nomor_polisi):
        """Mencari record berdasarkan Nomor Polisi."""
        return self._index.get(nomor_polisi.strip().upper())

    def delete(self, nomor_polisi):
        """Menghapus record berdasarkan Nomor Polisi."""
        rec = self.get(nomor_polisi)
        if not rec:
            return False
        # Hapus berdasarkan objek
        self._records.remove(rec) 
        # Hapus dari index
        del self._index[rec.nomor_polisi] 
        return True

    def to_dataframe(self):
        """Mengubah semua record menjadi Pandas DataFrame."""
        return pd.DataFrame([r.as_dict() for r in self._records]).sort_values(by="Masuk", ascending=False)


    def overdue_records(self, hours=24):
        """Mencari kendaraan yang parkir lebih dari X jam dan belum keluar."""
        now = datetime.now()
        out = []
        for r in self._records:
            # Hanya cek yang masih di dalam
            if r.waktu_keluar:
                continue
                
            dur = now - r.waktu_masuk
            if dur.total_seconds() > hours * 3600:
                # Membuat objek sementara untuk menghitung biaya saat ini (tanpa mengubah status asli)
                temp_rec = VehicleRecord(r.nomor_polisi, r.jenis_kendaraan, r.waktu_masuk.strftime("%Y-%m-%d %H:%M"))
                temp_rec.set_exit_now() 
                out.append(temp_rec)
        return out

    def statistics_today(self):
        """Menghitung statistik harian (pendapatan, jumlah masuk)."""
        today = datetime.now().date()
        masuk_hari_ini = [r for r in self._records if r.waktu_masuk.date() == today]
        bayar_hari_ini = [r for r in self._records if r.payment_time and r.payment_time.date() == today]
        
        total_pendapatan = sum([r.biaya_parkir or 0 for r in bayar_hari_ini])
        
        return {
            "pendapatan": total_pendapatan,
            "mobil": len([r for r in masuk_hari_ini if r.jenis_kendaraan == "Mobil"]), 
            "motor": len([r for r in masuk_hari_ini if r.jenis_kendaraan == "Motor"]), 
            "transaksi": len(bayar_hari_ini)
        }

# ===============================
#       STREAMLIT UI
# ===============================
st.set_page_config(page_title="Sistem Parkir Outlet", layout="wide")
st.title("🏢 Sistem Manajemen Data Parkir Outlet Bisnis")

# Inisialisasi ParkingManager di session_state
if "manager" not in st.session_state:
    st.session_state.manager = ParkingManager()
manager = st.session_state.manager

# -------------------------------
# Dashboard
# -------------------------------
st.header("📊 Dashboard Parkir")

stats = manager.statistics_today()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pendapatan Hari Ini", f"Rp {stats['pendapatan']:,.0f}")
c2.metric("Mobil Masuk Hari Ini", stats["mobil"])
c3.metric("Motor Masuk Hari Ini", stats["motor"])
c4.metric("Transaksi Selesai Hari Ini", stats["transaksi"])

st.subheader("📋 Daftar Kendaraan Saat Ini (Status Masuk)")
df = manager.to_dataframe()
# Hanya tampilkan yang belum keluar
df_masuk = df[df['Keluar'] == ""].copy()
df_masuk.drop(columns=['Keluar', 'Durasi', 'Biaya (Rp)', 'Paid', 'Payment Method'], inplace=True)
st.dataframe(df_masuk, use_container_width=True, hide_index=True)


# -------------------------------
# Kendaraan parkir >24 jam (yang masih di dalam)
# -------------------------------
st.subheader("⚠️ Kendaraan Parkir > 24 Jam (Belum Checkout)")
over = manager.overdue_records()
if over:
    st.warning(f"🚨 {len(over)} kendaraan parkir lebih dari 24 jam.")
    st.dataframe(pd.DataFrame([r.as_dict() for r in over]), use_container_width=True, hide_index=True)
else:
    st.success("👍 Tidak ada kendaraan yang parkir lebih dari 24 jam.")

# -------------------------------
# Input kendaraan masuk 
# -------------------------------
st.header("➕ Input Kendaraan Masuk")
with st.form("input_form"):
    st.subheader("Data Kendaraan")
    nopol = st.text_input("Nomor Polisi (Contoh: B1234ABC)", key="input_nopol_fix").upper() 
    jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"], key="input_jenis_fix")
    
    st.subheader("Waktu Masuk")
    col_tanggal, col_waktu = st.columns(2)
    with col_tanggal:
        tanggal = st.date_input("Tanggal Masuk", date.today(), key="input_tanggal_fix")
    with col_waktu:
        waktu_manual = st.time_input("Jam & Menit Masuk", value=datetime.now().time(), key="input_waktu_fix")

    # Menggabungkan tanggal dan waktu manual secara runut dan konsisten
    waktu_masuk_final = datetime.combine(tanggal, waktu_manual)
    st.info(f"Waktu Masuk yang akan disimpan: **{waktu_masuk
