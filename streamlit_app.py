import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd

# ===============================
#   MODEL & MANAGER
# ===============================
class VehicleRecord:
    def __init__(self, nomor_polisi: str, jenis_kendaraan: str, waktu_masuk: str):
        self.nomor_polisi = nomor_polisi.strip()
        self.jenis_kendaraan = jenis_kendaraan
        try:
            # Tetap parse dari string. Format sudah dijamin dari frontend.
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
        self.waktu_keluar = datetime.now()
        self._calc_durasi_biaya()

    def _calc_durasi_biaya(self):
        if not self.waktu_keluar:
            return
        
        # Kalkulasi Durasi
        dur = self.waktu_keluar - self.waktu_masuk
        self.durasi_parkir = dur
        
        # Hitung Jam Pembulatan ke atas (minimal 1 jam)
        total_seconds = dur.total_seconds()
        # Menggunakan pembulatan ke atas yang aman
        jam = int((total_seconds + 3599) // 3600) 
        jam = max(1, jam) # Minimal 1 jam
        
        # Kalkulasi Biaya Parkir 
        if self.jenis_kendaraan == "Mobil":
            # Jam pertama Rp 5000, jam berikutnya Rp 3000
            self.biaya_parkir = 5000 + (jam - 1) * 3000
        else: # Motor
            # Jam pertama Rp 3000, jam berikutnya Rp 2000
            self.biaya_parkir = 3000 + (jam - 1) * 2000

    def mark_paid(self, method: str):
        self.paid = True
        self.payment_method = method
        self.payment_time = datetime.now()

    def as_dict(self):
        return {
            "Nomor Polisi": self.nomor_polisi,
            "Jenis": self.jenis_kendaraan,
            "Masuk": self.waktu_masuk.strftime("%Y-%m-%d %H:%M"),
            "Keluar": self.waktu_keluar.strftime("%Y-%m-%d %H:%M") if self.waktu_keluar else "",
            "Durasi": str(self.durasi_parkir) if self.durasi_parkir else "",
            "Biaya (Rp)": self.biaya_parkir or 0,
            "Paid": self.paid,
            "Payment Method": self.payment_method or ""
        }

class ParkingManager:
    def __init__(self):
        self._records = []
        self._index = {}

    def add(self, nomor_polisi, jenis, waktu):
        # Cek apakah kendaraan masih di dalam (belum checkout)
        if nomor_polisi in self._index and not self._index[nomor_polisi].waktu_keluar:
             raise ValueError(f"Kendaraan dengan nopol {nomor_polisi} masih tercatat di dalam.")
             
        rec = VehicleRecord(nomor_polisi, jenis, waktu)
        self._records.append(rec)
        self._index[nomor_polisi] = rec
        return rec

    def get(self, nomor_polisi):
        return self._index.get(nomor_polisi)

    def delete(self, nomor_polisi):
        rec = self._index.get(nomor_polisi)
        if not rec:
            return False
        # Menghapus dari list _records
        self._records.remove(rec) 
        # Menghapus dari dictionary _index
        del self._index[nomor_polisi] 
        return True

    def all(self):
        return self._records

    def to_dataframe(self):
        return pd.DataFrame([r.as_dict() for r in self._records])

    def overdue_records(self, hours=24):
        now = datetime.now()
        out = []
        for r in self._records:
            # Hanya cek yang masih di dalam
            if r.waktu_keluar:
                continue
                
            dur = now - r.waktu_masuk
            if dur.total_seconds() > hours * 3600:
                # Kita buat VehicleRecord sementara untuk hitungan biaya saat ini.
                temp_rec = VehicleRecord(r.nomor_polisi, r.jenis_kendaraan, r.waktu_masuk.strftime("%Y-%m-%d %H:%M"))
                temp_rec.set_exit_now() 
                out.append(temp_rec)
        return out

    def statistics_today(self):
        today = datetime.now().date()
        # Masuk hari ini: yang waktu masuknya hari ini
        masuk_hari_ini = [r for r in self._records if r.waktu_masuk.date() == today]
        # Bayar hari ini: yang sudah dibayar DAN waktu bayarnya hari ini
        bayar_hari_ini = [r for r in self._records if r.payment_time and r.payment_time.date() == today]
        
        total_pendapatan = sum([r.biaya_parkir or 0 for r in bayar_hari_ini])
        
        return {
            "pendapatan": total_pendapatan,
            # Perbaikan: menggunakan variabel masuk_hari_ini (tanpa spasi)
            "mobil": len([r for r in masuk_hari_ini if r.jenis_kendaraan == "Mobil"]), 
            # Perbaikan: menggunakan variabel masuk_hari_ini (tanpa spasi)
            "motor": len([r for r in masuk_hari_ini if r.jenis_kendaraan == "Motor"]), 
            "transaksi": len(bayar_hari_ini)
        }

# ===============================
#       STREAMLIT UI
# ===============================
st.set_page_config(page_title="Sistem Parkir Outlet", layout="wide")
st.title("🏢 Sistem Manajemen Data Parkir Outlet Bisnis")

if "manager" not in st.session_state:
    st.session_state.manager = ParkingManager()
manager = st.session_state.manager

# -------------------------------
# Dashboard
# -------------------------------
st.header("📊 Dashboard Parkir")
df = manager.to_dataframe()
st.dataframe(df, use_container_width=True)

stats = manager.statistics_today()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pendapatan Hari Ini", f"Rp {stats['pendapatan']:,.0f}")
c2.metric("Mobil Masuk Hari Ini", stats["mobil"])
c3.metric("Motor Masuk Hari Ini", stats["motor"])
c4.metric("Transaksi Selesai Hari Ini", stats["transaksi"])

# -------------------------------
# Kendaraan parkir >24 jam (yang masih di dalam)
# -------------------------------
st.subheader("⏰ Kendaraan Parkir > 24 Jam (Masih di dalam)")
over = manager.overdue_records()
if over:
    st.warning(f"{len(over)} kendaraan parkir lebih dari 24 jam.")
    st.dataframe(pd.DataFrame([r.as_dict() for r in over]), use_container_width=True)
else:
    st.success("Tidak ada kendaraan yang parkir lebih dari 24 jam.")

# -------------------------------
# Input kendaraan masuk 
# -------------------------------
st.header("➕ Input Kendaraan Masuk")
with st.form("input_form"):
    nopol = st.text_input("Nomor Polisi", key="input_nopol").upper() # Uppercase untuk konsistensi
    jenis = st.selectbox("Jenis", ["Mobil", "Motor"], key="input_jenis")
    
    col_tanggal, col_waktu = st.columns(2)
    with col_tanggal:
        tanggal = st.date_input("Tanggal Masuk", date.today(), key="input_tanggal")
    with col_waktu:
        waktu_manual = st.time_input("Jam & Menit Masuk", value=datetime.now().time(), key="input_waktu")

    # Menggabungkan tanggal dan waktu manual
    waktu_masuk_final = datetime.combine(tanggal, waktu_manual)
    st.info(f"Waktu Masuk yang akan disimpan: **{waktu_masuk_final.strftime('%Y-%m-%d %H:%M')}**")
    
    submitted = st.form_submit_button("Tambah Kendaraan")
    
    if submitted:
        if not nopol.strip():
            st.error("Nomor polisi wajib diisi.")
        else:
            try:
                # Kirim string waktu yang sudah pasti sesuai input user
                manager.add(nopol, jenis, waktu_masuk_final.strftime("%Y-%m-%d %H:%d"))
                st.success(f"Data kendaraan **{nopol}** berhasil ditambahkan pada {waktu_masuk_final.strftime('%Y-%m-%d %H:%M')}.")
            except ValueError as ve:
                 st.error(str(ve))
            except Exception as e:
                st.error(f"Terjadi kesalahan saat menambahkan data: {e}")

# -------------------------------
# Cari / Hapus kendaraan
# -------------------------------
st.header("🔍 Cari / Hapus Data Kendaraan")
key_search = st.text_input("Nomor Polisi untuk Cari/Hapus", key="search_delete_key").upper() # Uppercase untuk konsistensi
c1, c2 = st.columns(2)
with c1:
    if st.button("Cari Kendaraan", key="button_search"):
        r = manager.get(key_search)
        if r:
            # Hitung biaya/durasi saat ini jika belum keluar
            if not r.waktu_keluar:
                # Buat objek sementara untuk menampilkan perhitungan saat ini tanpa mengubah data asli
                temp_rec = VehicleRecord(r.nomor_polisi, r.jenis_kendaraan, r.waktu_masuk.strftime("%Y-%m-%d %H:%M"))
                temp_rec.set_exit_now() 
                st.info(f"Ditemukan! Status: **Belum Keluar**. Perkiraan Biaya/Durasi saat ini:")
                st.json(temp_rec.as_dict())
            else:
                 st.info("Ditemukan! Status: **Sudah Keluar/Bayar**.")
                 st.json(r.as_dict())
        else:
            st.error("Data tidak ditemukan.")
with c2:
    if st.button("Hapus Kendaraan", key="button_delete"):
        if manager.delete(key_search):
            st.success(f"Data **{key_search}** berhasil dihapus.")
        else:
            st.error("Nomor polisi tidak ditemukan.")

# -------------------------------
# Checkout / Pembayaran
# -------------------------------
st.header("💳 Pembayaran / Checkout")
key_checkout = st.text_input("Nomor Polisi untuk Checkout", key="checkout_plate_input").upper() # Uppercase untuk konsistensi

if "checkout_rec" not in st.session_state:
    st.session_state.checkout_rec = None

if key_checkout:
    rec = manager.get(key_checkout)
    if not rec:
        st.error("Data tidak ditemukan.")
    elif rec.paid:
         st.success(f"Kendaraan **{key_checkout}** sudah dibayar pada {rec.payment_time.strftime('%Y-%m-%d %H:%M')} dengan metode {rec.payment_method}.")
    else:
        # Tampilkan tombol Hitung Biaya
        if st.button("Hitung Biaya Parkir Sekarang"):
            rec.set_exit_now()
            st.session_state.checkout_rec = rec
            st.info(f"Durasi Parkir: **{rec.durasi_parkir}**")
            st.info(f"Biaya Parkir: **Rp {rec.biaya_parkir:,.0f}**")
        
        # Tampilkan form pembayaran setelah biaya dihitung
        if st.session_state.checkout_rec and st.session_state.checkout_rec.nomor_polisi == key_checkout:
            rec_to_pay = st.session_state.checkout_rec
            
            st.subheader(f"Total Biaya: Rp {rec_to_pay.biaya_parkir:,.0f}")
            metode = st.selectbox("Metode Pembayaran", ["Cash", "Debit", "Credit Card", "QRIS", "E-Money", "E-Wallet"], key="checkout_method_select")
            
            if metode == "Cash":
                bayar = st.number_input("Bayar (Tunai)", min_value=rec_to_pay.biaya_parkir, step=1000, key="checkout_cash_input")
                
                if st.button("Bayar Tunai (Cash)", key="button_pay_cash"):
                    if bayar < rec_to_pay.biaya_parkir:
                        st.error("Uang tidak cukup.")
                    else:
                        rec_to_pay.mark_paid("Cash")
                        kembalian = bayar - rec_to_pay.biaya_parkir
                        st.success(f"Pembayaran berhasil. Kembalian: **Rp {kembalian:,.0f}**")
                        st.json(rec_to_pay.as_dict())
                        st.session_state.checkout_rec = None
            else:
                if st.button(f"Bayar Non-Tunai ({metode})", key="button_pay_noncash"):
                    rec_to_pay.mark_paid(metode)
                    st.success(f"Pembayaran berhasil via **{metode}**.")
                    st.json(rec_to_pay.as_dict())
                    st.session_state.checkout_rec = None
