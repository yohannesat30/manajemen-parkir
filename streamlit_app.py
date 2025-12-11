# app_refactor.py
import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd
import io
import re
import os
from urllib.parse import quote_plus
import requests

# -------------------------------
# Config
# -------------------------------
DATA_FILE = "parkir_data.csv"
ADMIN_PASS = "admin123"
PLATE_REGEX = r"^[A-Z]{1,2}\s?\d{1,4}\s?[A-Z]{1,3}$"
DEFAULT_PAYMENT_METHODS = ["Cash", "QRIS", "Debit", "E-Wallet"]
KNOWN_BRANDS = {"Toyota", "Honda", "Suzuki", "Daihatsu", "Yamaha", "Kawasaki", "BMW", "Mercedes", "Other"}

# -------------------------------
# Data model (Node + LinkedList)
# -------------------------------
class Node:
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk_str,
                 metode_bayar="Cash", merk="Other", waktu_keluar_str=None, status_bayar="Belum Dibayar"):
        self.nomor_polisi = nomor_polisi.strip().upper()
        self.jenis_kendaraan = jenis_kendaraan
        self.merk = merk if merk in KNOWN_BRANDS else "Other"
        self.metode_bayar = metode_bayar
        self.status_bayar = status_bayar

        # parse masuk
        try:
            if isinstance(waktu_masuk_str, str) and len(waktu_masuk_str) == 5 and ":" in waktu_masuk_str:
                t = datetime.strptime(waktu_masuk_str, "%H:%M").time()
                self.waktu_masuk = datetime.combine(datetime.now().date(), t)
            else:
                self.waktu_masuk = datetime.fromisoformat(str(waktu_masuk_str))
        except Exception:
            self.waktu_masuk = datetime.now()

        # parse keluar
        if waktu_keluar_str:
            try:
                if isinstance(waktu_keluar_str, str) and len(waktu_keluar_str) == 5 and ":" in waktu_keluar_str:
                    t = datetime.strptime(waktu_keluar_str, "%H:%M").time()
                    self.waktu_keluar = datetime.combine(self.waktu_masuk.date(), t)
                else:
                    self.waktu_keluar = datetime.fromisoformat(str(waktu_keluar_str))
            except Exception:
                self.waktu_keluar = None
        else:
            self.waktu_keluar = None

        self.update_durasi_biaya()
        self.next = None

    def update_durasi_biaya(self):
        self.durasi_parkir = (self.waktu_keluar - self.waktu_masuk) if self.waktu_keluar else (datetime.now() - self.waktu_masuk)
        self.biaya_parkir = self.hitung_biaya()

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
            "Durasi_s": int(self.durasi_parkir.total_seconds()) if self.durasi_parkir else 0,
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
            cols = ["Nomor Polisi","Jenis","Merk","Metode Bayar","Status","Masuk","Keluar","Durasi","Biaya (Rp)"]
            return pd.DataFrame(columns=cols)

    def save_to_csv(self, filepath=DATA_FILE):
        df = pd.DataFrame([n.to_dict() for n in self])
        df.to_csv(filepath, index=False)

    def load_from_csv(self, filepath=DATA_FILE):
        if hasattr(filepath, "read"):
            df = pd.read_csv(filepath)
        else:
            if not os.path.exists(filepath):
                return
            df = pd.read_csv(filepath)
        self.head = None
        for _, row in df.iterrows():
            masuk = row.get("Masuk")
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
            node.update_durasi_biaya()

# -------------------------------
# Helpers
# -------------------------------
def valid_plate(plate):
    return bool(re.match(PLATE_REGEX, plate.strip().upper()))

def gen_random_plate():
    return f"{random.choice(['B','D','AB','Z'])} {random.randint(100,9999)} {''.join(random.choices(string.ascii_uppercase, k=2))}"

def generate_qr_image_bytes(text, size=300):
    """Download QR from Google Chart API and return raw bytes, or None."""
    base = "https://chart.googleapis.com/chart"
    params = f"?chs={size}x{size}&cht=qr&chl={quote_plus(text)}&choe=UTF-8"
    url = base + params
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.content
    except Exception:
        return None
    return None

# -------------------------------
# App UI
# -------------------------------
st.set_page_config(page_title="Sistem Parkir (Refactor)", layout="wide")

if "parkir" not in st.session_state:
    st.session_state.parkir = DataParkir()
    st.session_state.parkir.load_from_csv(DATA_FILE)

parkir = st.session_state.parkir

menu = st.sidebar.radio("Menu", ["Dashboard", "Input", "Checkout", "Data", "Admin"])

st.title("🏢 Sistem Parkir — Versi Refactor")

# -------- Dashboard ----------
if menu == "Dashboard":
    st.header("Dashboard")
    data_nodes = parkir.to_df()
    data = parkir.all_data()

    total_income = data_nodes["Biaya (Rp)"].sum() if not data_nodes.empty else 0
    total_vehicles = len(data)
    in_area = len([n for n in data if not n.waktu_keluar])
    paid = len([n for n in data if n.status_bayar == "Sudah Dibayar"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pendapatan", f"Rp {total_income:,}")
    c2.metric("Total Kendaraan", total_vehicles)
    c3.metric("Masih Parkir", in_area)
    c4.metric("Telah Bayar", paid)

    st.subheader("Pendapatan Harian (sample)")
    if not data_nodes.empty:
        # convert Masuk to date and sum Biaya per Masuk-date (note: biaya may be 0 if still parked)
        df_rev = data_nodes.copy()
        df_rev["Masuk_date"] = pd.to_datetime(df_rev["Masuk"]).dt.date
        rev = df_rev.groupby("Masuk_date")["Biaya (Rp)"].sum().reset_index()
        rev = rev.rename(columns={"Masuk_date":"Tanggal"})
        rev["Tanggal"] = pd.to_datetime(rev["Tanggal"])
        st.line_chart(rev.set_index("Tanggal")["Biaya (Rp)"])
    else:
        st.info("Belum ada data untuk grafik.")

    st.subheader("Notifikasi: Kendaraan >24 jam")
    old = []
    for n in parkir.all_data():
        dur = (datetime.now() - n.waktu_masuk) if not n.waktu_keluar else (n.waktu_keluar - n.waktu_masuk)
        if not n.waktu_keluar and dur > timedelta(hours=24):
            old.append((n.nomor_polisi, n.merk, dur))
    if old:
        for p, m, d in old:
            st.warning(f"{p} ({m}) — terparkir {str(d)}")
    else:
        st.success("Tidak ada kendaraan >24 jam.")

# -------- Input ----------
elif menu == "Input":
    st.header("Parkir Masuk")
    col1, col2, col3, col4 = st.columns([2,2,2,2])
    with col1:
        nopol = st.text_input("Nomor Polisi", value=gen_random_plate()).upper()
    with col2:
        jenis = st.selectbox("Jenis", ["Mobil", "Motor"])
    with col3:
        merk = st.selectbox("Merk", sorted(list(KNOWN_BRANDS)))
    with col4:
        waktu = st.time_input("Waktu Masuk", value=datetime.now().time())
    metode = st.selectbox("Metode Bayar", DEFAULT_PAYMENT_METHODS)

    if st.button("Simpan Masuk"):
        if not nopol.strip():
            st.error("Nomor polisi wajib diisi")
        elif not valid_plate(nopol):
            st.error("Format nomor tidak valid (contoh: B 1234 ABC)")
        else:
            parkir.add(nopol, jenis, waktu.strftime("%H:%M"), metode, merk)
            parkir.save_to_csv(DATA_FILE)
            st.success(f"{nopol} tercatat masuk.")
            # generate QR bytes and show + download
            text = f"PLAT:{nopol}|MASUK:{datetime.now().isoformat()}"
            qr_bytes = generate_qr_image_bytes(text, size=300)
            if qr_bytes:
                st.image(qr_bytes, width=250, caption="QR Tiket")
                st.download_button("Download QR", qr_bytes, file_name=f"ticket_{nopol}.png", mime="image/png")
            else:
                st.info("QR tidak dapat dibuat (cek koneksi).")

# -------- Checkout ----------
elif menu == "Checkout":
    st.header("Parkir Keluar / Pembayaran")
    key = st.text_input("Nomor Polisi untuk Checkout").upper()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cari"):
            node = parkir.search(key)
            if node:
                node.update_durasi_biaya()
                st.write(pd.DataFrame([node.to_dict()]))
            else:
                st.warning("Data tidak ditemukan.")
    with col2:
        if st.button("Tandai Lunas & Set Keluar"):
            node = parkir.search(key)
            if node:
                node.status_bayar = "Sudah Dibayar"
                if not node.waktu_keluar:
                    node.waktu_keluar = datetime.now()
                node.update_durasi_biaya()
                parkir.save_to_csv(DATA_FILE)
                st.success(f"{key} telah dilunasi. Biaya: Rp {node.biaya_parkir:,}")
            else:
                st.error("Data tidak ditemukan.")

    st.write("---")
    st.subheader("Cetak / Download QR dari Nomor Polisi")
    qr_key = st.text_input("Nomor Polisi untuk QR (Cetak)").upper()
    if st.button("Generate QR untuk Nomor"):
        node = parkir.search(qr_key)
        if node:
            text = f"PLAT:{node.nomor_polisi}|MASUK:{node.waktu_masuk.isoformat()}|BIAYA:{node.biaya_parkir}"
            qr_bytes = generate_qr_image_bytes(text, size=300)
            if qr_bytes:
                st.image(qr_bytes, width=250)
                st.download_button("Download QR", qr_bytes, file_name=f"ticket_{node.nomor_polisi}.png", mime="image/png")
            else:
                st.error("Gagal mengambil QR (cek koneksi).")
        else:
            st.error("Nomor polisi tidak ditemukan.")

# -------- Data ----------
elif menu == "Data":
    st.header("Data Parkir")
    df = parkir.to_df()
    st.dataframe(df, use_container_width=True)
    st.write("---")
    if st.button("Generate Simulasi 20"):
        for _ in range(20):
            nomor = gen_random_plate()
            j = random.choice(["Mobil", "Motor"])
            w = f"{random.randint(6,22)}:{random.randint(0,59):02d}"
            m = random.choice(DEFAULT_PAYMENT_METHODS)
            merk = random.choice(list(KNOWN_BRANDS))
            parkir.add(nomor, j, w, m, merk)
        parkir.save_to_csv(DATA_FILE)
        st.success("Simulasi ditambahkan.")

# -------- Admin ----------
elif menu == "Admin":
    st.header("Admin / Export")
    pw = st.text_input("Password Admin", type="password")
    if pw == ADMIN_PASS:
        st.success("Autentikasi berhasil")
        if st.button("Save CSV Sekarang"):
            parkir.save_to_csv(DATA_FILE)
            st.success("Tersimpan.")
        uploaded = st.file_uploader("Import CSV (format export)", type=["csv"])
        if uploaded:
            try:
                parkir.load_from_csv(uploaded)
                parkir.save_to_csv(DATA_FILE)
                st.success("Import berhasil")
            except Exception as e:
                st.error(f"Gagal import: {e}")
        if st.button("Export CSV untuk Download"):
            df = parkir.to_df()
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", data=csv, file_name="parkir_export.csv", mime="text/csv")
    else:
        if pw:
            st.error("Password salah")

st.write("---")
st.caption("Aplikasi Parkir — Refactor. QR di-generate via Google Charts API & didownload agar tampil di Streamlit.")
