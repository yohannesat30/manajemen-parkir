# app.py
import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd
import io
import re
import segno
import os

# -------------------------------
# Configuration / Constants
# -------------------------------
DATA_FILE = "parkir_data.csv"
PLATE_REGEX = r"^[A-Z]{1,2}\s?\d{1,4}\s?[A-Z]{1,3}$"  # contoh: B 1234 ABC atau AB1234CD
DEFAULT_PAYMENT_METHODS = ["Cash", "QRIS", "Debit", "E-Wallet"]
KNOWN_BRANDS = {"Toyota", "Honda", "Suzuki", "Daihatsu", "Yamaha", "Kawasaki", "BMW", "Mercedes", "Other"}

# ===============================
#     DATA MODEL (LINKED LIST)
# ===============================
class Node:
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk_str,
                 metode_bayar="Cash", merk="Other", waktu_keluar_str=None, status_bayar="Belum Dibayar"):
        self.nomor_polisi = nomor_polisi.strip().upper()
        self.jenis_kendaraan = jenis_kendaraan  # "Mobil" / "Motor"
        self.merk = merk if merk in KNOWN_BRANDS else "Other"
        self.metode_bayar = metode_bayar
        self.status_bayar = status_bayar

        # Parse waktu masuk (we store full ISO datetimes internally)
        # Accept either HH:MM (today) or ISO string
        try:
            if len(waktu_masuk_str) == 5 and ":" in waktu_masuk_str:
                t = datetime.strptime(waktu_masuk_str, "%H:%M").time()
                self.waktu_masuk = datetime.combine(datetime.now().date(), t)
            else:
                self.waktu_masuk = datetime.fromisoformat(waktu_masuk_str)
        except Exception:
            # fallback to now
            self.waktu_masuk = datetime.now()

        # waktu keluar optional
        if waktu_keluar_str:
            try:
                if len(waktu_keluar_str) == 5 and ":" in waktu_keluar_str:
                    t = datetime.strptime(waktu_keluar_str, "%H:%M").time()
                    self.waktu_keluar = datetime.combine(self.waktu_masuk.date(), t)
                else:
                    self.waktu_keluar = datetime.fromisoformat(waktu_keluar_str)
            except Exception:
                self.waktu_keluar = None
        else:
            self.waktu_keluar = None

        # duration
        if self.waktu_keluar:
            self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        else:
            self.durasi_parkir = datetime.now() - self.waktu_masuk

        self.biaya_parkir = self.hitung_biaya()
        self.next = None

    def hitung_biaya(self):
        seconds = max(0, int(self.durasi_parkir.total_seconds()))
        jam = seconds // 3600
        if seconds % 3600 != 0:
            jam += 1
        jam = max(1, jam)
        if self.jenis_kendaraan == "Mobil":
            return 5000 + (jam - 1) * 3000
        else:
            return 3000 + (jam - 1) * 2000

    def to_dict(self):
        return {
            "Nomor Polisi": self.nomor_polisi,
            "Jenis": self.jenis_kendaraan,
            "Merk": self.merk,
            "Metode Bayar": self.metode_bayar,
            "Status": self.status_bayar,
            "Masuk": self.waktu_masuk.isoformat(),
            "Keluar": self.waktu_keluar.isoformat() if self.waktu_keluar else "",
            "Durasi_s": int(self.durasi_parkir.total_seconds()),
            "Biaya (Rp)": self.biaya_parkir
        }

class DataParkir:
    def __init__(self):
        self.head = None

    def __iter__(self):
        cur = self.head
        while cur:
            yield cur
            cur = cur.next

    def add(self, nomor_polisi, jenis, waktu, metode="Cash", merk="Other"):
        node = Node(nomor_polisi, jenis, waktu, metode, merk)
        if not self.head:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node
        return node

    def search(self, nomor_polisi):
        key = nomor_polisi.strip().upper()
        cur = self.head
        while cur:
            if cur.nomor_polisi == key:
                return cur
            cur = cur.next
        return None

    def delete(self, nomor_polisi):
        key = nomor_polisi.strip().upper()
        if not self.head:
            return False
        if self.head.nomor_polisi == key:
            self.head = self.head.next
            return True
        cur = self.head
        while cur.next:
            if cur.next.nomor_polisi == key:
                cur.next = cur.next.next
                return True
            cur = cur.next
        return False

    def all_data(self):
        return list(iter(self))

    def to_df(self):
        rows = []
        for n in self:
            d = n.to_dict()
            masuk_h = datetime.fromisoformat(d["Masuk"]).strftime("%Y-%m-%d %H:%M")
            keluar_h = d["Keluar"] and datetime.fromisoformat(d["Keluar"]).strftime("%Y-%m-%d %H:%M") or ""
            durasi_h = str(timedelta(seconds=d["Durasi_s"]))
            rows.append({
                "Nomor Polisi": d["Nomor Polisi"],
                "Jenis": d["Jenis"],
                "Merk": d["Merk"],
                "Metode Bayar": d["Metode Bayar"],
                "Status": d["Status"],
                "Masuk": masuk_h,
                "Keluar": keluar_h,
                "Durasi": durasi_h,
                "Biaya (Rp)": d["Biaya (Rp)"]
            })
        if rows:
            return pd.DataFrame(rows)
        else:
            # empty df with columns
            cols = ["Nomor Polisi","Jenis","Merk","Metode Bayar","Status","Masuk","Keluar","Durasi","Biaya (Rp)"]
            return pd.DataFrame(columns=cols)

    def save_to_csv(self, filepath=DATA_FILE):
        df = pd.DataFrame([n.to_dict() for n in self])
        df.to_csv(filepath, index=False)

    def load_from_csv(self, filepath=DATA_FILE):
        if isinstance(filepath, io.IOBase):
            # file-like (uploaded)
            df = pd.read_csv(filepath)
        else:
            if not os.path.exists(filepath):
                return
            df = pd.read_csv(filepath)
        # rebuild linked list
        self.head = None
        for _, row in df.iterrows():
            masuk = row.get("Masuk") or row.get("Masuk")
            keluar = row.get("Keluar", "")
            self.add(
                row["Nomor Polisi"],
                row["Jenis"],
                masuk,
                row.get("Metode Bayar", "Cash"),
                row.get("Merk", "Other")
            )
            node = self.search(row["Nomor Polisi"])
            node.status_bayar = row.get("Status", "Belum Dibayar")
            if keluar and isinstance(keluar, str) and keluar.strip() != "":
                try:
                    node.waktu_keluar = datetime.fromisoformat(keluar)
                except Exception:
                    node.waktu_keluar = None
            # recompute durations and biaya
            node.durasi_parkir = (node.waktu_keluar - node.waktu_masuk) if node.waktu_keluar else (datetime.now() - node.waktu_masuk)
            node.biaya_parkir = node.hitung_biaya()

# -------------------------------
# Helper functions
# -------------------------------
def valid_plate(plate):
    return bool(re.match(PLATE_REGEX, plate.strip().upper()))

def gen_random_plate():
    return f"{random.choice(['B','D','AB','Z'])} {random.randint(100,9999)} {''.join(random.choices(string.ascii_uppercase, k=2))}"

def generate_qr_bytes(text):
    """
    Return PNG bytes for given text using segno (no external pillow needed).
    """
    qr = segno.make(text)
    buf = io.BytesIO()
    qr.save(buf, kind='png', scale=6)  # scale controls size
    buf.seek(0)
    return buf.read()

# -------------------------------
# Streamlit App UI
# -------------------------------
st.set_page_config(page_title="Sistem Parkir Lengkap", layout="wide")

# init manager and load data
if "parkir" not in st.session_state:
    st.session_state.parkir = DataParkir()
    # try to load if file exists
    st.session_state.parkir.load_from_csv(DATA_FILE)

parkir = st.session_state.parkir

# Sidebar menu
menu = st.sidebar.radio("📌 Menu", ["Dashboard", "Input Kendaraan", "Pencarian & Pembayaran", "Data Parkir", "Admin / Export"])

st.title("🏢 Sistem Manajemen Parkir (Streamlit)")

# ---------------- Dashboard ----------------
if menu == "Dashboard":
    st.header("📊 Dashboard")
    data = parkir.all_data()
    df = parkir.to_df()

    total_pendapatan = sum(n.biaya_parkir for n in data) if data else 0
    jml_mobil = len([n for n in data if n.jenis_kendaraan == "Mobil"])
    jml_motor = len([n for n in data if n.jenis_kendaraan == "Motor"])
    jml_belum_bayar = len([n for n in data if n.status_bayar == "Belum Dibayar"])
    jml_lunas = len([n for n in data if n.status_bayar == "Sudah Dibayar"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pendapatan", f"Rp {total_pendapatan:,}")
    c2.metric("Jumlah Mobil", jml_mobil)
    c3.metric("Jumlah Motor", jml_motor)
    c4.metric("Transaksi Lunas", jml_lunas)

    st.subheader("Ringkasan per Merk")
    merk_summary = {}
    for n in data:
        merk_summary.setdefault(n.merk, 0)
        merk_summary[n.merk] += 1
    st.write(merk_summary)

    st.subheader("Notifikasi: Kendaraan > 24 jam (Kemungkinan Tinggal)")
    old = []
    for n in data:
        dur = (datetime.now() - n.waktu_masuk) if not n.waktu_keluar else (n.waktu_keluar - n.waktu_masuk)
        if not n.waktu_keluar and dur > timedelta(hours=24):
            old.append((n.nomor_polisi, n.merk, dur))
    if old:
        for p, m, d in old:
            st.warning(f"{p} ({m}) - sudah {str(d)} terparkir (>24 jam).")
    else:
        st.success("Tidak ada kendaraan yang terparkir lebih dari 24 jam.")

    st.write("---")
    st.subheader("Data Terakhir")
    st.dataframe(df, use_container_width=True)

# ---------------- Input Kendaraan ----------------
if menu == "Input Kendaraan":
    st.header("➕ Input Kendaraan Masuk")
    col1, col2, col3, col4 = st.columns([2,2,2,2])
    with col1:
        inp_nopol = st.text_input("Nomor Polisi (contoh: B 1234 ABC)", value=gen_random_plate())
    with col2:
        inp_jenis = st.selectbox("Jenis Kendaraan", ["Mobil", "Motor"])
    with col3:
        inp_merk = st.selectbox("Merk Kendaraan", sorted(list(KNOWN_BRANDS)))
    with col4:
        inp_waktu = st.time_input("Waktu Masuk (jam:menit)", value=datetime.now().time())
    metode = st.selectbox("Metode Pembayaran", DEFAULT_PAYMENT_METHODS)

    if st.button("Tambah Data"):
        if not inp_nopol.strip():
            st.error("Nomor polisi wajib diisi.")
        elif not valid_plate(inp_nopol):
            st.error("Format nomor polisi tidak valid. Gunakan format STNK-like (contoh: B 1234 ABC).")
        else:
            time_str = inp_waktu.strftime("%H:%M")
            parkir.add(inp_nopol, inp_jenis, time_str, metode, inp_merk)
            st.success("Data berhasil ditambahkan.")
            parkir.save_to_csv(DATA_FILE)

    st.write("---")
    st.subheader("Contoh QR Ticket (preview dari input saat ini)")
    if st.button("Generate contoh tiket QR (dari input saat ini)"):
        if not valid_plate(inp_nopol):
            st.error("Nomor polisi belum valid.")
        else:
            text = f"PLAT:{inp_nopol.strip().upper()}|JENIS:{inp_jenis}|MERK:{inp_merk}|WAKTU:{datetime.now().isoformat()}"
            png_bytes = generate_qr_bytes(text)
            st.image(png_bytes, caption="QR Ticket (PNG)", use_column_width=False)
            st.code(text)

# ---------------- Pencarian & Pembayaran ----------------
if menu == "Pencarian & Pembayaran":
    st.header("🔍 Cari / Hapus / Proses Pembayaran / Cetak QR")
    key = st.text_input("Masukkan Nomor Polisi untuk mencari")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Cari"):
            node = parkir.search(key)
            if node:
                st.success("Data ditemukan")
                st.write(pd.DataFrame([node.to_dict()]))
            else:
                st.warning("Tidak ditemukan.")
    with col2:
        if st.button("Hapus"):
            if parkir.delete(key):
                st.success("Data dihapus.")
                parkir.save_to_csv(DATA_FILE)
            else:
                st.error("Gagal hapus (tidak ditemukan).")
    with col3:
        if st.button("Proses Pembayaran (Tandai Lunas)"):
            node = parkir.search(key)
            if node:
                node.status_bayar = "Sudah Dibayar"
                if not node.waktu_keluar:
                    node.waktu_keluar = datetime.now()
                node.durasi_parkir = node.waktu_keluar - node.waktu_masuk
                node.biaya_parkir = node.hitung_biaya()
                parkir.save_to_csv(DATA_FILE)
                st.success(f"{node.nomor_polisi} sudah dibayar. Biaya: Rp {node.biaya_parkir:,}")
            else:
                st.error("Data tidak ditemukan.")

    st.write("---")
    st.subheader("Cetak QR Ticket dari Nomor Polisi")
    key2 = st.text_input("Nomor Polisi untuk QR")
    if st.button("Generate QR Ticket"):
        node = parkir.search(key2)
        if node:
            text = f"PLAT:{node.nomor_polisi}|MASUK:{node.waktu_masuk.isoformat()}|BIAYA:{node.biaya_parkir}"
            png_bytes = generate_qr_bytes(text)
            st.image(png_bytes, caption="QR Ticket (PNG)")
            st.download_button("Download QR PNG", data=png_bytes, file_name=f"ticket_{node.nomor_polisi}.png", mime="image/png")
        else:
            st.error("Data tidak ditemukan untuk QR.")

# ---------------- Data Parkir ----------------
if menu == "Data Parkir":
    st.header("📋 Data Parkir")
    df = parkir.to_df()
    st.dataframe(df, use_container_width=True)

    st.write("---")
    if st.button("Generate Data Parkir (Simulasi 20)"):
        for _ in range(20):
            nomor = gen_random_plate()
            j = random.choice(["Mobil", "Motor"])
            w = f"{random.randint(6,22)}:{random.randint(0,59):02d}"
            m = random.choice(DEFAULT_PAYMENT_METHODS)
            merk = random.choice(list(KNOWN_BRANDS))
            parkir.add(nomor, j, w, m, merk)
        parkir.save_to_csv(DATA_FILE)
        st.success("Simulasi data ditambahkan.")

# ---------------- Admin / Export ----------------
if menu == "Admin / Export":
    st.header("🔐 Admin / Export")
    st.write("Penyimpanan saat ini:", DATA_FILE)
    if st.button("Save Sekarang ke CSV"):
        parkir.save_to_csv(DATA_FILE)
        st.success("Tersimpan.")
    uploaded = st.file_uploader("Import CSV (format export)", type=["csv"])
    if uploaded:
        try:
            parkir.load_from_csv(uploaded)
            parkir.save_to_csv(DATA_FILE)  # persist imported
            st.success("Import berhasil.")
        except Exception as e:
            st.error(f"Gagal import: {e}")

    # Export current table to CSV for user
    if st.button("Export CSV untuk Download"):
        df = parkir.to_df()
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="parkir_export.csv", mime="text/csv")

st.write("---")
st.caption("Aplikasi Parkir: fitur lengkap (validation, QR via segno, persistence, notifikasi >24h).")





