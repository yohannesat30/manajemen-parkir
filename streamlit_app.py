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
    """Rekam data kendaraan — contoh OOP dasar + property."""
    def __init__(self, nomor_polisi: str, jenis_kendaraan: str, waktu_masuk: str):
        self.nomor_polisi = nomor_polisi.strip()
        self.jenis_kendaraan = jenis_kendaraan
        # parsing waktu masuk (format HH:MM). Jika tanggal tidak disediakan, gunakan hari ini.
        try:
            # gunakan tanggal sekarang + jam
            hh, mm = map(int, waktu_masuk.split(":"))
            now = datetime.now()
            self.waktu_masuk = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            # jika waktu masuk dianggap di masa depan hari ini, anggap kemarin
            if self.waktu_masuk > datetime.now() + timedelta(minutes=5):
                self.waktu_masuk = self.waktu_masuk - timedelta(days=1)
        except Exception:
            # default ke sekarang
            self.waktu_masuk = datetime.now()

        # simulasi waktu keluar (bisa diatur saat checkout)
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
    """Manager memegang data parkir. Menyediakan operasi add/search/delete/list/import/export."""
    def __init__(self):
        # simpan list untuk urutan dan dict untuk lookup cepat
        self._records = []
        self._index = {}  # nomor_polisi -> record (last occurrence)
        self._seen_plate_set = set()  # contoh penggunaan set

    def add(self, nomor_polisi, jenis, waktu_masuk):
        rec = VehicleRecord(nomor_polisi, jenis, waktu_masuk)
        # append dan index
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
        # hapus dari list
        try:
            self._records.remove(rec)
        except ValueError:
            pass
        # hapus dari index (tetap biarkan di seen set)
        del self._index[nomor_polisi]
        return True

    def all(self):
        return list(self._records)

    def to_dataframe(self):
        return pd.DataFrame([r.as_dict() for r in self._records])

    def import_from_df(self, df: pd.DataFrame):
        # df harus berisi kolom: Nomor, Jenis, Masuk (HH:MM atau YYYY-MM-DD HH:MM)
        count = 0
        for _, row in df.iterrows():
            nom = str(row.get("Nomor", row.get("Nomor Polisi", ""))).strip()
            jenis = str(row.get("Jenis", "Motor")).strip()
            masuk = str(row.get("Masuk", row.get("Waktu Masuk", ""))).strip()
            if not masuk:
                # jika tidak ada jam, pakai sekarang
                masuk = datetime.now().strftime("%H:%M")
            self.add(nom, jenis, masuk)
            count += 1
        return count

    def export_to_csv(self):
        df = self.to_dataframe()
        return df.to_csv(index=False)

    def generate_sample(self, n=20):
        jenis = ["Mobil", "Motor"]
        for _ in range(n):
            nomor = f"B {random.randint(1000,9999)} {''.join(random.choices(string.ascii_uppercase, k=3))}"
            j = random.choice(jenis)
            w = f"{random.randint(6,22)}:{random.randint(0,59):02d}"
            self.add(nomor, j, w)

    def overdue_records(self, hours=24):
        res = []
        now = datetime.now()
        for r in self._records:
            # hitung durasi sampai sekarang jika belum keluar
            end = r.waktu_keluar or now
            dur = end - r.waktu_masuk
            if dur.total_seconds() > hours * 3600:
                # pastikan durasi dan biaya dihitung untuk display
                if not r.waktu_keluar:
                    r.set_exit_at(now)
                res.append(r)
        return res

# ===============================
#       STREAMLIT UI
# ===============================
st.set_page_config(page_title="Sistem Manajemen Parkir (Demo)", layout="wide")
st.title("🏢 Sistem Manajemen Parkir — Demo lengkap untuk materi pemrograman")

# session init
if "manager" not in st.session_state:
    st.session_state.manager = ParkingManager()
manager: ParkingManager = st.session_state.manager

# Sidebar menu
menu = st.sidebar.selectbox("Menu", [
    "Dashboard",
    "Input Kendaraan",
    "Cari / Hapus",
    "Pembayaran (Checkout)",
    "Import / Export",
    "Sample Data & Utilitas"
])

# ---------- Dashboard ----------
if menu == "Dashboard":
    st.header("📊 Dashboard Parkir")
    data = manager.all()
    df = manager.to_dataframe()
    st.dataframe(df, use_container_width=True)

    total_pendapatan = sum([r.biaya_parkir or 0 for r in data if r.paid])
    jml_mobil = len([r for r in data if r.jenis_kendaraan == "Mobil"])
    jml_motor = len([r for r in data if r.jenis_kendaraan == "Motor"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pendapatan (paid)", f"Rp {total_pendapatan:,}")
    c2.metric("Jumlah Mobil (parkir tercatat)", jml_mobil)
    c3.metric("Jumlah Motor (parkir tercatat)", jml_motor)

    st.subheader("Notifikasi - Kendaraan parkir > 24 jam")
    overdue = manager.overdue_records(hours=24)
    if overdue:
        st.warning(f"Ada {len(overdue)} kendaraan yang parkir lebih dari 24 jam!")
        df_over = pd.DataFrame([r.as_dict() for r in overdue])
        st.dataframe(df_over, use_container_width=True)
        # action: tampilkan tombol notifikasi (visual)
        if st.button("Tandai semua overdue sebagai 'Diberitahu' (simulasi)"):
            # kita hanya simulasi: tambahkan tag ke payment method
            for r in overdue:
                r.payment_method = (r.payment_method or "") + " | overdue-notified"
            st.success("Semua kendaraan overdue ditandai.")
    else:
        st.info("Tidak ada kendaraan yang parkir lebih dari 24 jam.")

    st.markdown("---")
    st.subheader("Ringkasan Data Mentah")
    st.write(f"Jumlah plat unik tercatat: {len(manager._seen_plate_set)} (contoh penggunaan set).")

# ---------- Input Kendaraan ----------
elif menu == "Input Kendaraan":
    st.header("➕ Input Kendaraan Masuk")
    col1, col2, col3 = st.columns(3)
    with col1:
        inp_nopol = st.text_input("Nomor Polisi", value="")
    with col2:
        inp_jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"])
    with col3:
        inp_waktu = st.text_input("Waktu Masuk (HH:MM)", value=datetime.now().strftime("%H:%M"))

    if st.button("Tambah Data"):
        if not inp_nopol.strip():
            st.error("Nomor polisi wajib diisi.")
        else:
            r = manager.add(inp_nopol, inp_jenis, inp_waktu)
            st.success(f"Ditambahkan: {r.nomor_polisi} — {r.jenis_kendaraan} masuk pukul {r.waktu_masuk.strftime('%Y-%m-%d %H:%M')}")

# ---------- Search / Delete ----------
elif menu == "Cari / Hapus":
    st.header("🔍 Cari / Hapus Data")
    key = st.text_input("Masukkan Nomor Polisi untuk Cari/Hapus")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cari"):
            rec = manager.get(key)
            if rec:
                rec.set_exit_now() if not rec.waktu_keluar else None
                st.info(
                    f"Nomor: {rec.nomor_polisi}\n"
                    f"Jenis: {rec.jenis_kendaraan}\n"
                    f"Masuk: {rec.waktu_masuk.strftime('%Y-%m-%d %H:%M')}\n"
                    f"Keluar: {rec.waktu_keluar.strftime('%Y-%m-%d %H:%M') if rec.waktu_keluar else '—'}\n"
                    f"Durasi: {rec.durasi_parkir}\n"
                    f"Biaya: Rp {rec.biaya_parkir:,}\n"
                    f"Paid: {rec.paid}"
                )
            else:
                st.warning("Data tidak ditemukan.")
    with c2:
        if st.button("Hapus"):
            if manager.delete(key):
                st.success("Data dihapus.")
            else:
                st.error("Nomor polisi tidak ditemukan.")

# ---------- Pembayaran ----------
elif menu == "Pembayaran (Checkout)":
    st.header("💳 Pembayaran / Checkout")
    key = st.text_input("Masukkan Nomor Polisi untuk Checkout")
    if st.button("Hitung Biaya"):
        rec = manager.get(key)
        if not rec:
            st.error("Data tidak ditemukan.")
        else:
            # set exit sekarang dan hitung biaya
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
                        st.write("=== STRUK ===")
                        st.write(rec.as_dict())
            else:
                if st.button("Proses Bayar (Non-Cash)"):
                    # simulasi sukses
                    rec.mark_paid(method)
                    st.success(f"Pembayaran via {method} berhasil (simulasi).")
                    st.write(rec.as_dict())

# ---------- Import / Export ----------
elif menu == "Import / Export":
    st.header("📂 Import / Export Data (CSV)")

    st.subheader("Import CSV")
    uploaded = st.file_uploader("Upload CSV (kolom: Nomor, Jenis, Masuk[HH:MM atau datetime])", type=["csv"])
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            cnt = manager.import_from_df(df)
            st.success(f"Berhasil import {cnt} baris.")
        except Exception as e:
            st.error(f"Gagal import: {e}")

    st.subheader("Export CSV")
    csv = manager.export_to_csv()
    st.download_button("Download data parkir (CSV)", data=csv, file_name="data_parkir.csv", mime="text/csv")

    st.subheader("Export Log Pembayaran (CSV)")
    # buat DataFrame pembayaran
    paid_df = pd.DataFrame([r.as_dict() for r in manager.all() if r.paid])
    csv_paid = paid_df.to_csv(index=False)
    st.download_button("Download pembayaran (CSV)", data=csv_paid, file_name="log_pembayaran.csv", mime="text/csv")

# ---------- Sample Data & Utilitas ----------
elif menu == "Sample Data & Utilitas":
    st.header("⚙️ Sample & Utilitas")
    if st.button("Generate Sample Data (20)"):
        manager.generate_sample(20)
        st.success("Sample data ditambahkan.")
    if st.button("Bersihkan semua data (RESET)"):
        # reset session manager
        st.session_state.manager = ParkingManager()
        st.success("Data direset.")
    st.markdown("---")
    st.write("Contoh struktur data internal (dict index & set):")
    st.write("Index keys (beberapa):", list(manager._index.keys())[:10])
    st.write("Seen plates count (set):", len(manager._seen_plate_set))

# ===============================
#      Footer / Penjelasan
# ===============================
st.sidebar.markdown("---")
st.sidebar.markdown("Aplikasi demo ini meliputi materi:\n\n"
                    "- Variables, Input/Output (Streamlit)\n"
                    "- Branching (if/else)\n"
                    "- Looping (for/while dalam list handling)\n"
                    "- Strings (format, parsing)\n"
                    "- List, Dict, Set (data structures)\n"
                    "- File handling (import/export CSV)\n"
                    "- OOP dasar + sedikit lanjutan (class, enkapsulasi, methods)\n\n"
                    "Kamu tidak perlu meng-upload file untuk menjalankan — fitur upload disediakan jika kamu ingin memulai dari file CSV.")
