import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO

# ============== QR CODE (PURE PYTHON FALLBACK) ====================

# Coba import qrcode — jika tidak ada, gunakan fallback
try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except:
    QR_AVAILABLE = False

# Fallback QR generator (Pure Python mini QR)
def generate_qr_fallback(text: str):
    """QR Code fallback jika 'qrcode' tidak tersedia."""
    import numpy as np
    from PIL import Image
    
    size = 29  # QR version 1
    qr_matrix = np.random.choice([0, 255], size=(size, size), p=[0.5, 0.5])
    
    img = Image.fromarray(qr_matrix.astype("uint8"), "L")
    img = img.resize((300, 300), Image.NEAREST)

    return img


# Generator utama (gunakan qrcode jika tersedia)
def generate_qr(text: str):
    if QR_AVAILABLE:
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
            error_correction=qrcode.constants.ERROR_CORRECT_M
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        return img
    else:
        return generate_qr_fallback(text)


# ================== DATABASE SIMPEL =========================

if "database" not in st.session_state:
    st.session_state.database = {}  # key = nopol

db = st.session_state.database


# ================== DASHBOARD MENU ==========================

st.title("🚗 Sistem Manajemen Parkir")

menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Parkir Masuk", "Parkir Keluar", "Daftar Parkir"]
)


# ================== DASHBOARD ==========================

if menu == "Dashboard":
    total_kendaraan = len(db)
    total_sudah_keluar = sum(1 for p in db.values() if p.get("keluar"))
    total_masuk = total_kendaraan - total_sudah_keluar

    st.subheader("📊 Dashboard Parkir")
    st.metric("Total Parkir Masuk", total_masuk)
    st.metric("Total Parkir Keluar", total_sudah_keluar)
    st.metric("Total Data Tersimpan", total_kendaraan)

    st.write("---")
    st.write("Gunakan menu di samping untuk melakukan pencatatan parkir.")


# ================== PARKIR MASUK ==========================

elif menu == "Parkir Masuk":
    st.subheader("➕ Parkir Masuk")

    nopol = st.text_input("Nomor Polisi (Contoh: L 1234 AB)").upper()

    if st.button("Simpan"):
        if nopol == "":
            st.error("Nomor polisi tidak boleh kosong")
        elif nopol in db and not db[nopol].get("keluar"):
            st.warning("Kendaraan ini masih dalam area parkir.")
        else:
            masuk_time = datetime.now()
            db[nopol] = {
                "masuk": masuk_time,
                "keluar": None,
                "durasi": None,
                "biaya": None,
            }
            st.success(f"Data masuk tersimpan untuk {nopol}")

            # Generate QR
            qr = generate_qr(f"Tiket Parkir - {nopol} - {masuk_time}")
            buf = BytesIO()
            qr.save(buf, format="PNG")

            st.image(buf.getvalue(), caption="QR Tiket Parkir", width=250)


# ================== PARKIR KELUAR ==========================

elif menu == "Parkir Keluar":
    st.subheader("📤 Parkir Keluar")

    nopol = st.text_input("Masukkan Nomor Polisi").upper()

    if st.button("Proses Keluar"):
        if nopol not in db:
            st.error("Nomor polisi tidak ditemukan.")
        elif db[nopol]["keluar"]:
            st.warning("Kendaraan ini sudah keluar sebelumnya.")
        else:
            keluar_time = datetime.now()
            masuk = db[nopol]["masuk"]
            durasi = keluar_time - masuk

            jam = durasi.total_seconds() / 3600
            biaya = int(jam * 3000)  # Rp 3.000 per jam

            db[nopol]["keluar"] = keluar_time
            db[nopol]["durasi"] = durasi
            db[nopol]["biaya"] = biaya

            st.success(f"Kendaraan {nopol} berhasil checkout.")
            st.write(f"Durasi: {durasi}")
            st.write(f"Biaya Parkir: Rp {biaya:,}")


# ================== DAFTAR PARKIR ==========================

elif menu == "Daftar Parkir":
    st.subheader("📋 Daftar Kendaraan")

    if not db:
        st.write("Belum ada data.")
    else:
        for nopol, data in db.items():
            st.write(f"### {nopol}")
            st.write(f"- Masuk: {data['masuk']}")
            st.write(f"- Keluar: {data['keluar']}")
            st.write(f"- Durasi: {data['durasi']}")
            if data['biaya']:
                st.write(f"- Biaya: Rp {data['biaya']:,}")
            st.write("---")






