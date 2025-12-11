import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd

# =======================================================
#   MODEL: VehicleRecord & ParkingManager
# =======================================================
class VehicleRecord:
    def __init__(self, nomor_polisi: str, jenis_kendaraan: str, waktu_masuk: str):
        self.nomor_polisi = nomor_polisi.strip()
        self.jenis_kendaraan = jenis_kendaraan

        # Parsing waktu masuk (format HH:MM)
        try:
            hh, mm = map(int, waktu_masuk.split(":"))
            now = datetime.now()
            self.waktu_masuk = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            # Jika waktu masuk terlihat masa depan, asumsikan kemarin
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

    # ==================================================
    #            STATISTIK HARIAN (PERBAIKAN)
    # ==================================================
    def statistics_today(self):
        today = datetime.now().date()

        masuk_hari_ini = [r for r in self._records if r.waktu_masuk.date() == today]
        bayar_hari_ini = [r for r in self._records
                          if r.payment_time and r.payment_time.date() == today]

        total_pendapatan = sum([r.biaya_parkir or 0 for r in bayar_hari_ini])

        return {
            "pendapatan": total_pendapatan,
            "mobil": len([r for r in masuk_hari_ini if r.jenis_kendaraan == "Mobil"]),
            "motor": len([r for r in masuk_hari_ini if r.jenis_kendaraan == "Motor"]),
            "transaksi": len(bayar_hari_ini)
        }


# =======================================================
#                  STREAMLIT UI
# =======================================================
st.set_page_config(page_title="Sistem Manajemen Data Parkir Outlet Bisnis", layout="wide")
st.title("🏢 Sistem Manajemen Data Parkir Outlet Bisnis")

if "manager" not in st.session_state:
    st.session_state.manager = ParkingManager()
manager = st.session_state.manager

menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Input Kendaraan", "Cari / Hapus", "Pembayaran (Checkout)"]
)


# =======================================================
#                        Dashboard
# =======================================================
if menu == "Dashboard":
    st.header("📊 Dashboard Parkir Outlet")

    df = manager.to_dataframe()
    st.dataframe(df, use_container_width=True)

    st.subheader("📆 Statistik Harian")
    stats = manager.statistics_today()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pendapatan Hari Ini", f"Rp {stats['pendapatan']:,}")
    c2.metric("Mobil Masuk", stats["mobil"])
    c3.metric("Motor Masuk", stats["motor"])
    c4.metric("Transaksi Selesai", stats["transaksi"])

    st.subheader("⏰ Kendaraan Parkir > 24 Jam")
    over = manager.overdue_records()
    if over:
        st.warning(f"{len(over)} kendaraan parkir lebih dari 24 jam.")
        st.dataframe(pd.DataFrame([r.as_dict() for r in over]), use_container_width=True)
    else:
        st.success("Tidak ada kendaraan yang parkir lebih dari 24 jam.")


# =======================================================
#                    Input Kendaraan
# =======================================================
elif menu == "Input Kendaraan":
    st.header("➕ Input Kendaraan Masuk")

    nopol = st.text_input("Nomor Polisi")
    jenis = st.selectbox("Jenis", ["Mobil", "Motor"])
    waktu = st.text_input("Waktu Masuk (HH:MM)", datetime.now().strftime("%H:%M"))

    if st.button("Tambah"):
        if nopol.strip():
            manager.add(nopol, jenis, waktu)
            st.success("Data berhasil ditambahkan.")
        else:
            st.error("Nomor polisi wajib diisi.")


# =======================================================
#                    Cari / Hapus Kendaraan
# =======================================================
elif menu == "Cari / Hapus":
    st.header("🔍 Cari / Hapus Data Kendaraan")

    key = st.text_input("Masukkan Nomor Polisi")

    if st.button("Cari"):
        r = manager.get(key)
        if r:
            if not r.waktu_keluar:
                r.set_exit_now()
            st.write(r.as_dict())
        else:
            st.error("Data tidak ditemukan.")

    if st.button("Hapus"):
        if manager.delete(key):
            st.success("Data berhasil dihapus.")
        else:
            st.error("Nomor polisi tidak ditemukan.")


# =======================================================
#                       Pembayaran
# =======================================================
elif menu == "Pembayaran (Checkout)":
    st.header("💳 Pembayaran / Checkout")

    key = st.text_input("Nomor Polisi")

    if st.button("Hitung Biaya"):
        r = manager.get(key)
        if not r:
            st.error("Data tidak ditemukan.")
        else:
            r.set_exit_now()
            st.info(f"Durasi: {r.durasi_parkir}")
            st.info(f"Biaya Parkir: Rp {r.biaya_parkir:,}")

            metode = st.selectbox(
                "Metode Pembayaran",
                ["Cash", "Debit", "Credit Card", "QRIS", "E-Money", "E-Wallet (OVO/DANA/GoPay)"]
            )

            if metode == "Cash":
                bayar = st.number_input("Uang Tunai", min_value=0, step=1000)
                if st.button("Bayar (Cash)"):
                    if bayar < r.biaya_parkir:
                        st.error("Uang tidak cukup.")
                    else:
                        kembali = bayar - r.biaya_parkir
                        r.mark_paid("Cash")
                        st.success(f"Pembayaran sukses. Kembalian: Rp {kembali:,}")
            else:
                if st.button("Bayar (Non-Cash)"):
                    r.mark_paid(metode)
                    st.success(f"Pembayaran via {metode} berhasil.")
