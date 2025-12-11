import streamlit as st
from datetime import datetime, timedelta, date, time
import pandas as pd

# ===============================
#   MODEL & MANAGER
# ===============================
class VehicleRecord:
    def __init__(self, nomor_polisi: str, jenis_kendaraan: str, waktu_masuk: str):
        self.nomor_polisi = nomor_polisi.strip()
        self.jenis_kendaraan = jenis_kendaraan
        try:
            dt = datetime.strptime(waktu_masuk, "%Y-%m-%d %H:%M")
            now = datetime.now()
            self.waktu_masuk = dt
            if self.waktu_masuk > now + timedelta(minutes=5):
                self.waktu_masuk -= timedelta(days=1)
        except:
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
        dur = self.waktu_keluar - self.waktu_masuk
        self.durasi_parkir = dur
        jam = int(dur.total_seconds() // 3600)
        jam = max(1, jam)
        if self.jenis_kendaraan == "Mobil":
            self.biaya_parkir = 5000 + (jam - 1) * 3000
        else:
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
        self._records.remove(rec)
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
            akhir = r.waktu_keluar or now
            dur = akhir - r.waktu_masuk
            if dur.total_seconds() > hours * 3600:
                if not r.waktu_keluar:
                    r.set_exit_now()
                out.append(r)
        return out

    def statistics_today(self):
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
#       STREAMLIT UI SEDERHANA
# ===============================
st.set_page_config(page_title="Sistem Parkir Outlet", layout="wide")
st.title("🏢 Sistem Manajemen Data Parkir Outlet Bisnis")

if "manager" not in st.session_state:
    st.session_state.manager = ParkingManager()
manager = st.session_state.manager

# Dashboard
st.header("📊 Dashboard Parkir")
df = manager.to_dataframe()
st.dataframe(df, use_container_width=True)
stats = manager.statistics_today()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pendapatan Hari Ini", f"Rp {stats['pendapatan']:,}")
c2.metric("Mobil Masuk", stats["mobil"])
c3.metric("Motor Masuk", stats["motor"])
c4.metric("Transaksi Selesai", stats["transaksi"])

# Kendaraan parkir >24 jam
st.subheader("⏰ Kendaraan Parkir > 24 Jam")
over = manager.overdue_records()
if over:
    st.warning(f"{len(over)} kendaraan parkir lebih dari 24 jam.")
    st.dataframe(pd.DataFrame([r.as_dict() for r in over]), use_container_width=True)
else:
    st.success("Tidak ada kendaraan yang parkir lebih dari 24 jam.")

# Input kendaraan masuk
st.header("➕ Input Kendaraan Masuk")
nopol = st.text_input("Nomor Polisi")
jenis = st.selectbox("Jenis", ["Mobil", "Motor"])

# Pilih tanggal dan jam manual
tanggal = st.date_input("Tanggal Masuk", date.today())
jam = st.time_input("Jam Masuk", datetime.now().time().replace(second=0, microsecond=0))
waktu_manual = datetime.combine(tanggal, jam)

if st.button("Tambah Kendaraan"):
    if not nopol.strip():
        st.error("Nomor polisi wajib diisi.")
    else:
        try:
            manager.add(nopol, jenis, waktu_manual.strftime("%Y-%m-%d %H:%M"))
            st.success("Data berhasil ditambahkan.")
        except:
            st.error("Terjadi kesalahan saat menambahkan data.")

# Cari / Hapus kendaraan
st.header("🔍 Cari / Hapus Data Kendaraan")
key_search = st.text_input("Nomor Polisi untuk Cari/Hapus")
c1, c2 = st.columns(2)
with c1:
    if st.button("Cari Kendaraan"):
        r = manager.get(key_search)
        if r:
            if not r.waktu_keluar:
                r.set_exit_now()
            st.write(r.as_dict())
        else:
            st.error("Data tidak ditemukan.")
with c2:
    if st.button("Hapus Kendaraan"):
        if manager.delete(key_search):
            st.success("Data berhasil dihapus.")
        else:
            st.error("Nomor polisi tidak ditemukan.")

# Checkout / Pembayaran
st.header("💳 Pembayaran / Checkout")
key_checkout = st.text_input("Nomor Polisi untuk Checkout", key="checkout_key")

if "checkout_plate" not in st.session_state:
    st.session_state.checkout_plate = None
if "checkout_method" not in st.session_state:
    st.session_state.checkout_method = None

if key_checkout:
    rec = manager.get(key_checkout)
    if not rec:
        st.error("Data tidak ditemukan.")
    else:
        if st.button("Hitung Biaya"):
            rec.set_exit_now()
            st.session_state.checkout_plate = key_checkout
            st.info(f"Durasi Parkir: {rec.durasi_parkir}")
            st.info(f"Biaya Parkir: Rp {rec.biaya_parkir:,}")

        if st.session_state.checkout_plate == key_checkout:
            metode = st.selectbox("Metode Pembayaran", ["Cash", "Debit", "Credit Card", "QRIS", "E-Money", "E-Wallet"])
            st.session_state.checkout_method = metode

            if metode == "Cash":
                bayar = st.number_input("Bayar (Tunai)", min_value=0, step=1000)
                if st.button("Bayar (Cash)"):
                    if bayar < rec.biaya_parkir:
                        st.error("Uang tidak cukup.")
                    else:
                        rec.mark_paid("Cash")
                        kembalian = bayar - rec.biaya_parkir
                        st.success(f"Pembayaran berhasil. Kembalian: Rp {kembalian:,}")
                        st.write(rec.as_dict())
                        st.session_state.checkout_plate = None
                        st.session_state.checkout_method = None
            else:
                if st.button("Bayar (Non-Cash)"):
                    rec.mark_paid(metode)
                    st.success(f"Pembayaran berhasil via {metode}.")
                    st.write(rec.as_dict())
                    st.session_state.checkout_plate = None
                    st.session_state.checkout_method = None
