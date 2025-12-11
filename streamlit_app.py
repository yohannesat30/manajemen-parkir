import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO

# ===============================
#   MODEL: VehicleRecord & Manager
# ===============================
class VehicleRecord:
    def __init__(self, nomor_polisi: str, jenis_kendaraan: str, waktu_masuk: str):
        self.nomor_polisi = nomor_polisi.strip()
        self.jenis_kendaraan = jenis_kendaraan

        try:
            hh, mm = map(int, waktu_masuk.split(":"))
            now = datetime.now()
            self.waktu_masuk = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
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
        self._calc()

    def set_exit_at(self, dt):
        self.waktu_keluar = dt
        self._calc()

    def _calc(self):
        if not self.waktu_keluar:
            return
        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        jam = int(self.durasi_parkir.total_seconds() // 3600)
        jam = max(1, jam)
        if self.jenis_kendaraan == "Mobil":
            self.biaya_parkir = 5000 + (jam - 1) * 3000
        else:
            self.biaya_parkir = 3000 + (jam - 1) * 2000

    def mark_paid(self, method):
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
            "Biaya (Rp)": self.biaya_parkir if self.biaya_parkir else 0,
            "Paid": self.paid,
            "Payment Method": self.payment_method or ""
        }


class ParkingManager:
    def __init__(self):
        self._records = []
        self._index = {}
        self._seen_plate_set = set()  # contoh penggunaan set

    def add(self, nopol, jenis, waktu):
        rec = VehicleRecord(nopol, jenis, waktu)
        self._records.append(rec)
        self._index[rec.nomor_polisi] = rec
        self._seen_plate_set.add(rec.nomor_polisi)
        return rec

    def get(self, nopol):
        return self._index.get(nopol)

    def delete(self, nopol):
        rec = self._index.get(nopol)
        if not rec:
            return False
        try:
            self._records.remove(rec)
        except:
            pass
        del self._index[nopol]
        return True

    def all(self):
        return list(self._records)

    def to_dataframe(self):
        return pd.DataFrame([r.as_dict() for r in self._records])

    def import_df(self, df):
        count = 0
        for _, row in df.iterrows():
            nopol = str(row.get("Nomor Polisi", row.get("Nomor", ""))).strip()
            jenis = str(row.get("Jenis", "Motor")).strip()
            masuk = str(row.get("Masuk", datetime.now().strftime("%H:%M"))).strip()
            self.add(nopol, jenis, masuk)
            count += 1
        return count

    def export_csv(self):
        df = self.to_dataframe()
        return df.to_csv(index=False)

    def overdue(self, hours=24):
        hasil = []
        now = datetime.now()
        for r in self._records:
            end = r.waktu_keluar or now
            dur = end - r.waktu_masuk
            if dur.total_seconds() > hours * 3600:
                r.set_exit_at(now)
                hasil.append(r)
        return hasil


# ===============================
#       STREAMLIT APP
# ===============================
st.set_page_config(page_title="Sistem Parkir", layout="wide")
st.title("🏢 Sistem Manajemen Parkir (Versi Final)")

if "manager" not in st.session_state:
    st.session_state.manager = ParkingManager()

manager: ParkingManager = st.session_state.manager

menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Input Kendaraan", "Cari / Hapus", "Pembayaran (Checkout)", "Import / Export"]
)

# ========== DASHBOARD ==========
if menu == "Dashboard":
    st.header("📊 Dashboard Parkir")

    df = manager.to_dataframe()
    st.dataframe(df, use_container_width=True)

    total_p = sum([r.biaya_parkir or 0 for r in manager.all() if r.paid])
    jml_mobil = len([r for r in manager.all() if r.jenis_kendaraan == "Mobil"])
    jml_motor = len([r for r in manager.all() if r.jenis_kendaraan == "Motor"])

    a, b, c = st.columns(3)
    a.metric("Total Pendapatan (Paid)", f"Rp {total_p:,}")
    b.metric("Jumlah Mobil", jml_mobil)
    c.metric("Jumlah Motor", jml_motor)

    st.subheader("⏰ Notifikasi Parkir > 24 Jam")
    overdue = manager.overdue(hours=24)

    if overdue:
        st.warning(f"{len(overdue)} kendaraan parkir lebih dari 24 jam!")
        st.dataframe(pd.DataFrame([r.as_dict() for r in overdue]), use_container_width=True)
    else:
        st.info("Tidak ada kendaraan yang melebihi 24 jam.")

# ========== INPUT KENDARAAN ==========
elif menu == "Input Kendaraan":
    st.header("➕ Input Kendaraan Masuk")

    c1, c2, c3 = st.columns(3)
    with c1:
        nopol = st.text_input("Nomor Polisi")
    with c2:
        jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"])
    with c3:
        waktu = st.text_input("Waktu Masuk (HH:MM)", datetime.now().strftime("%H:%M"))

    if st.button("Tambah"):
        if nopol.strip():
            manager.add(nopol, jenis, waktu)
            st.success("Data kendaraan ditambahkan.")
        else:
            st.error("Nomor Polisi wajib diisi.")

# ========== CARI / HAPUS ==========
elif menu == "Cari / Hapus":
    st.header("🔍 Cari / Hapus Kendaraan")

    key = st.text_input("Nomor Polisi")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cari"):
            rec = manager.get(key)
            if rec:
                rec.set_exit_now() if not rec.waktu_keluar else None
                st.info(rec.as_dict())
            else:
                st.error("Data tidak ditemukan.")

    with c2:
        if st.button("Hapus"):
            if manager.delete(key):
                st.success("Berhasil dihapus.")
            else:
                st.error("Nomor Polisi tidak ditemukan.")

# ========== PEMBAYARAN ==========
elif menu == "Pembayaran (Checkout)":
    st.header("💳 Pembayaran Parkir")

    key = st.text_input("Nomor Polisi (Checkout)")

    if st.button("Hitung Biaya"):
        rec = manager.get(key)
        if not rec:
            st.error("Data tidak ditemukan.")
        else:
            rec.set_exit_now()
            st.write(f"Durasi: {rec.durasi_parkir}")
            st.write(f"Biaya Parkir: **Rp {rec.biaya_parkir:,}**")

            metode = st.selectbox("Metode Pembayaran", ["Cash", "E-Money", "QRIS"])

            if metode == "Cash":
                cash = st.number_input("Masukkan Uang", min_value=0, step=1000)
                if st.button("Bayar (Cash)"):
                    if cash < rec.biaya_parkir:
                        st.error("Uang tidak cukup.")
                    else:
                        rec.mark_paid("Cash")
                        st.success(f"Pembayaran berhasil. Kembalian: Rp {cash - rec.biaya_parkir:,}")
            else:
                if st.button("Bayar Non-Cash"):
                    rec.mark_paid(metode)
                    st.success(f"Pembayaran berhasil via {metode}")

            st.write("**Struk Pembayaran:**")
            st.json(rec.as_dict())

# ========== IMPORT / EXPORT ==========
elif menu == "Import / Export":
    st.header("📂 Import / Export Data Parkir")

    st.subheader("Import CSV")
    file = st.file_uploader("Upload data CSV", type=["csv"])
    if file:
        df = pd.read_csv(file)
        jumlah = manager.import_df(df)
        st.success(f"Berhasil import {jumlah} data.")

    st.subheader("Export CSV")
    csv = manager.export_csv()
    st.download_button("Download CSV", csv, file_name="data_parkir.csv")

