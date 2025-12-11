import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd

# ===============================
#   MODEL: VehicleRecord & Manager
# ===============================
class VehicleRecord:
    def __init__(self, nomor_polisi: str, jenis_kendaraan: str, waktu_masuk: str):
        self.nomor_polisi = nomor_polisi.strip()
        self.jenis_kendaraan = jenis_kendaraan

        # parsing waktu masuk (HH:MM). Jika error, gunakan sekarang
        try:
            hh, mm = map(int, waktu_masuk.split(":"))
            now = datetime.now()
            self.waktu_masuk = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            # jika waktu masuk terlihat di masa depan (lebih dari 5 menit), anggap kemarin
            if self.waktu_masuk > now + timedelta(minutes=5):
                self.waktu_masuk -= timedelta(days=1)
        except Exception:
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

    def set_exit_at(self, waktu_keluar: datetime):
        self.waktu_keluar = waktu_keluar
        self._calc_durasi_biaya()

    def _calc_durasi_biaya(self):
        if not self.waktu_keluar:
            return
        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        jam = int(self.durasi_parkir.total_seconds() // 3600)
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
            "Biaya (Rp)": self.biaya_parkir if self.biaya_parkir else 0,
            "Paid": self.paid,
            "Payment Method": self.payment_method or ""
        }

class ParkingManager:
    def __init__(self):
        self._records = []            # simpan urutan input
        self._index = {}             # lookup cepat: nomor_polisi -> record
        self._seen_plate_set = set() # contoh penggunaan set (unik plat)

    def add(self, nomor_polisi, jenis, waktu):
        rec = VehicleRecord(nomor_polisi, jenis, waktu)
        self._records.append(rec)
        self._index[rec.nomor_polisi] = rec
        self._seen_plate_set.add(rec.nomor_polisi)
        return rec

    def get(self, nomor_polisi):
        return self._index.get(nomor_polisi)

    def delete(self, nomor_polisi):
        rec = self._index.get(nomor_polisi)
        if not rec:
            return False
        try:
            self._records.remove(rec)
        except ValueError:
            pass
        del self._index[nomor_polisi]
        return True

    def all(self):
        return list(self._records)

    def to_dataframe(self):
        return pd.DataFrame([r.as_dict() for r in self._records])

    def generate_sample(self, n=10):
        jenis = ["Mobil", "Motor"]
        for _ in range(n):
            nomor = f"B {random.randint(1000,9999)} {''.join(random.choices(string.ascii_uppercase, k=3))}"
            j = random.choice(jenis)
            w = f"{random.randint(6,22)}:{random.randint(0,59):02d}"
            self.add(nomor, j, w)

    def overdue_records(self, hours=24):
        """
        Kembalikan list VehicleRecord yang durasinya (sampai sekarang jika belum keluar)
        lebih besar dari 'hours'. Jangan ganti nama method — gunakan overdue_records saat memanggil.
        """
        now = datetime.now()
        hasil = []
        for r in self._records:
            end = r.waktu_keluar or now
            durasi = end - r.waktu_masuk
            if durasi.total_seconds() > hours * 3600:
                # pastikan durasi dan biaya dihitung untuk tampilan
                if not r.waktu_keluar:
                    r.set_exit_at(now)
                hasil.append(r)
        return hasil

# ===============================
#       STREAMLIT UI
# ===============================
st.set_page_config(page_title="Sistem Manajemen Parkir", layout="wide")
st.title("🏢 Sistem Manajemen Parkir — Perbaikan")

# inisialisasi session
if "manager" not in st.session_state:
    st.session_state.manager = ParkingManager()
manager: ParkingManager = st.session_state.manager

# Sidebar menu — import/export dihapus sesuai permintaan
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Input Kendaraan", "Cari / Hapus", "Pembayaran (Checkout)"])

# ================= Dashboard =================
if menu == "Dashboard":
    st.header("📊 Dashboard Parkir")
    df = manager.to_dataframe()
    st.dataframe(df, use_container_width=True)

    total_pendapatan = sum([r.biaya_parkir or 0 for r in manager.all() if r.paid])
    jml_mobil = len([r for r in manager.all() if r.jenis_kendaraan == "Mobil"])
    jml_motor = len([r for r in manager.all() if r.jenis_kendaraan == "Motor"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pendapatan (Paid)", f"Rp {total_pendapatan:,}")
    col2.metric("Jumlah Mobil", jml_mobil)
    col3.metric("Jumlah Motor", jml_motor)

    st.subheader("Notifikasi: Kendaraan parkir > 24 jam")
    overdue = manager.overdue_records(hours=24)
    if overdue:
        st.warning(f"Ada {len(overdue)} kendaraan yang parkir lebih dari 24 jam!")
        st.dataframe(pd.DataFrame([r.as_dict() for r in overdue]), use_container_width=True)
    else:
        st.info("Tidak ada kendaraan yang parkir lebih dari 24 jam.")

# ================= Input Kendaraan =================
elif menu == "Input Kendaraan":
    st.header("➕ Input Kendaraan Masuk")
    col1, col2, col3 = st.columns(3)
    with col1:
        inp_nopol = st.text_input("Nomor Polisi")
    with col2:
        inp_jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"])
    with col3:
        inp_waktu = st.text_input("Waktu Masuk (HH:MM)", datetime.now().strftime("%H:%M"))

    if st.button("Tambah Data"):
        if inp_nopol and inp_nopol.strip():
            manager.add(inp_nopol, inp_jenis, inp_waktu)
            st.success("Data parkir ditambahkan.")
        else:
            st.error("Nomor polisi wajib diisi.")

# ================= Cari / Hapus =================
elif menu == "Cari / Hapus":
    st.header("🔍 Cari atau Hapus Data Parkir")
    search_key = st.text_input("Cari berdasarkan Nomor Polisi")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cari"):
            result = manager.get(search_key)
            if result:
                # tampilkan info (set exit sekarang untuk melihat durasi jika perlu)
                result.set_exit_now() if not result.waktu_keluar else None
                st.info(
                    f"*Nomor Polisi:* {result.nomor_polisi}\n"
                    f"*Jenis:* {result.jenis_kendaraan}\n"
                    f"*Masuk:* {result.waktu_masuk.strftime('%Y-%m-%d %H:%M')}\n"
                    f"*Keluar:* {result.waktu_keluar.strftime('%Y-%m-%d %H:%M') if result.waktu_keluar else '—'}\n"
                    f"*Durasi:* {result.durasi_parkir}\n"
                    f"*Biaya:* Rp {result.biaya_parkir:,}\n"
                    f"*Paid:* {result.paid}"
                )
            else:
                st.warning("Data tidak ditemukan.")
    with c2:
        if st.button("Hapus"):
            if manager.delete(search_key):
                st.success("Data berhasil dihapus!")
            else:
                st.error("Nomor polisi tidak ditemukan.")

# ================= Pembayaran =================
elif menu == "Pembayaran (Checkout)":
    st.header("💳 Pembayaran / Checkout")
    key = st.text_input("Masukkan Nomor Polisi untuk Checkout")

    if st.button("Hitung Biaya"):
        rec = manager.get(key)
        if not rec:
            st.error("Data tidak ditemukan.")
        else:
            rec.set_exit_now()
            st.write(f"Biaya parkir: Rp {rec.biaya_parkir:,} (durasi {rec.durasi_parkir})")
            method = st.selectbox("Metode Pembayaran", ["Cash", "E-Money (simulasi)", "QR (simulasi)"])
            if method == "Cash":
                uang = st.number_input("Bayar (uang tunai)", min_value=0, step=1000)
                if st.button("Proses Bayar (Cash)"):
                    if uang < rec.biaya_parkir:
                        st.error("Uang tidak cukup.")
                    else:
                        change = uang - rec.biaya_parkir
                        rec.mark_paid("Cash")
                        st.success(f"Pembayaran diterima. Kembalian: Rp {change:,}")
                        st.write(rec.as_dict())
            else:
                if st.button("Proses Bayar (Non-Cash)"):
                    rec.mark_paid(method)
                    st.success(f"Pembayaran via {method} berhasil (simulasi).")
                    st.write(rec.as_dict())

# End of app
