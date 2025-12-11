import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd

# ===============================
#   MODEL & MANAGER
# ===============================
class VehicleRecord:
    def __init__(self, nomor_polisi: str, jenis_kendaraan: str, waktu_masuk: datetime):
        self.nomor_polisi = nomor_polisi.strip()
        self.jenis_kendaraan = jenis_kendaraan
        # Terima waktu masuk langsung dari input manual tanpa koreksi
        self.waktu_masuk = waktu_masuk
        self.waktu_keluar = None
        self.durasi_parkir = None
        self.biaya_parkir = None
        self.paid = False
        self.payment_method = None
        self.payment_time = None

    def set_exit_now(self):
        self.waktu_keluar = datetime.now()
        self._calc_durasi_biaya()

    def set_exit_manual(self, waktu_keluar: datetime):
        """Untuk keluar dengan waktu manual"""
        self.waktu_keluar = waktu_keluar
        self._calc_durasi_biaya()

    def _calc_durasi_biaya(self):
        if not self.waktu_keluar:
            return
        dur = self.waktu_keluar - self.waktu_masuk
        self.durasi_parkir = dur
        
        # Hitung durasi dalam jam (pembulatan ke atas)
        total_detik = dur.total_seconds()
        jam = int(total_detik // 3600)
        
        # Jika ada sisa menit lebih dari 0, tambah 1 jam
        if total_detik % 3600 > 0:
            jam += 1
        
        # Minimal 1 jam
        jam = max(1, jam)
        
        if self.jenis_kendaraan == "Mobil":
            self.biaya_parkir = 5000 + (jam - 1) * 3000
        else:  # Motor
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
            "Keluar": self.waktu_keluar.strftime("%Y-%m-%d %H:%M") if self.waktu_keluar else "Masih Parkir",
            "Durasi": str(self.durasi_parkir).split('.')[0] if self.durasi_parkir else "",
            "Biaya (Rp)": f"{self.biaya_parkir:,}" if self.biaya_parkir else "0",
            "Status Bayar": "✅ Lunas" if self.paid else "❌ Belum",
            "Metode Bayar": self.payment_method or "",
            "Waktu Bayar": self.payment_time.strftime("%H:%M") if self.payment_time else ""
        }

class ParkingManager:
    def __init__(self):
        self._records = []
        self._index = {}

    def add(self, nomor_polisi, jenis, waktu_masuk):
        rec = VehicleRecord(nomor_polisi, jenis, waktu_masuk)
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
        if not self._records:
            return pd.DataFrame()
        return pd.DataFrame([r.as_dict() for r in self._records])

    def overdue_records(self, hours=24):
        now = datetime.now()
        out = []
        for r in self._records:
            if not r.waktu_keluar:  # Hanya yang masih parkir
                dur = now - r.waktu_masuk
                if dur.total_seconds() > hours * 3600:
                    out.append(r)
        return out

    def statistics_today(self):
        today = datetime.now().date()
        masuk_hari_ini = [r for r in self._records if r.waktu_masuk.date() == today]
        bayar_hari_ini = [r for r in self._records if r.payment_time and r.payment_time.date() == today]
        total_pendapatan = sum([r.biaya_parkir or 0 for r in bayar_hari_ini if r.paid])
        return {
            "pendapatan": total_pendapatan,
            "mobil": len([r for r in masuk_hari_ini if r.jenis_kendaraan == "Mobil"]),
            "motor": len([r for r in masuk_hari_ini if r.jenis_kendaraan == "Motor"]),
            "transaksi": len(bayar_hari_ini),
            "total_kendaraan": len(masuk_hari_ini),
            "parkir_aktif": len([r for r in self._records if not r.waktu_keluar])
        }

# ===============================
#       STREAMLIT UI
# ===============================
st.set_page_config(page_title="Sistem Parkir Outlet", layout="wide")
st.title("🏢 Sistem Manajemen Data Parkir Outlet Bisnis")

# Inisialisasi session state
if "manager" not in st.session_state:
    st.session_state.manager = ParkingManager()
if "show_payment" not in st.session_state:
    st.session_state.show_payment = False
if "current_plate" not in st.session_state:
    st.session_state.current_plate = None

manager = st.session_state.manager

# -------------------------------
# Dashboard
# -------------------------------
st.header("📊 Dashboard Parkir")

# Statistik
stats = manager.statistics_today()
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Pendapatan Hari Ini", f"Rp {stats['pendapatan']:,}")
col2.metric("Mobil Masuk", stats["mobil"])
col3.metric("Motor Masuk", stats["motor"])
col4.metric("Transaksi Selesai", stats["transaksi"])
col5.metric("Parkir Aktif", stats["parkir_aktif"])

# Tabel Data
st.subheader("📋 Data Semua Kendaraan")
df = manager.to_dataframe()
if not df.empty:
    st.dataframe(df, use_container_width=True, height=300)
else:
    st.info("Belum ada data kendaraan.")

# -------------------------------
# Kendaraan parkir >24 jam
# -------------------------------
st.subheader("⏰ Kendaraan Parkir > 24 Jam")
over = manager.overdue_records()
if over:
    st.warning(f"⚠️ {len(over)} kendaraan parkir lebih dari 24 jam!")
    over_df = pd.DataFrame([r.as_dict() for r in over])
    st.dataframe(over_df, use_container_width=True)
else:
    st.success("✅ Tidak ada kendaraan yang parkir lebih dari 24 jam.")

# -------------------------------
# Input kendaraan masuk - FULL MANUAL
# -------------------------------
st.header("➕ Input Kendaraan Masuk")
with st.expander("Tambah Kendaraan Baru", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nopol = st.text_input("Nomor Polisi*", placeholder="Contoh: B 1234 ABC")
        jenis = st.selectbox("Jenis Kendaraan*", ["Mobil", "Motor"])
    
    with col2:
        # Input tanggal dan waktu manual sepenuhnya
        tanggal_masuk = st.date_input("Tanggal Masuk*", date.today())
        waktu_masuk = st.time_input("Waktu Masuk*", value=datetime.now().time())
    
    # Gabungkan tanggal dan waktu
    waktu_masuk_dt = datetime.combine(tanggal_masuk, waktu_masuk)
    
    st.info(f"**Waktu Masuk yang dipilih:** {waktu_masuk_dt.strftime('%A, %d %B %Y %H:%M')}")
    
    if st.button("🚗 Simpan Data Masuk", type="primary", use_container_width=True):
        if not nopol.strip():
            st.error("❌ Nomor polisi wajib diisi!")
        else:
            # Cek apakah nomor polisi sudah ada dan masih parkir
            existing = manager.get(nopol)
            if existing and not existing.waktu_keluar:
                st.error(f"❌ Kendaraan {nopol} masih tercatat parkir!")
            else:
                try:
                    manager.add(nopol, jenis, waktu_masuk_dt)
                    st.success(f"✅ Data kendaraan **{nopol}** berhasil ditambahkan!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan: {str(e)}")

# -------------------------------
# Cari / Edit / Hapus kendaraan
# -------------------------------
st.header("🔍 Cari / Kelola Data Kendaraan")
search_tab, delete_tab = st.tabs(["🔎 Cari Data", "🗑️ Hapus Data"])

with search_tab:
    search_key = st.text_input("Masukkan Nomor Polisi untuk pencarian")
    if search_key:
        record = manager.get(search_key)
        if record:
            st.success(f"✅ Data ditemukan untuk {search_key}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📋 Detail Kendaraan")
                data_dict = record.as_dict()
                for key, value in data_dict.items():
                    st.write(f"**{key}:** {value}")
            
            with col2:
                st.subheader("🛠️ Aksi")
                if not record.waktu_keluar:
                    if st.button("🚪 Hitung Biaya & Checkout", type="secondary", use_container_width=True):
                        record.set_exit_now()
                        st.session_state.show_payment = True
                        st.session_state.current_plate = search_key
                        st.rerun()
                else:
                    st.info("✅ Kendaraan sudah checkout")
                    
                    if not record.paid:
                        if st.button("💳 Lanjutkan Pembayaran", type="primary", use_container_width=True):
                            st.session_state.show_payment = True
                            st.session_state.current_plate = search_key
                            st.rerun()
        else:
            st.error("❌ Data tidak ditemukan")

with delete_tab:
    del_key = st.text_input("Masukkan Nomor Polisi untuk dihapus")
    if st.button("🗑️ Hapus Data Permanen", type="secondary"):
        if del_key:
            if manager.delete(del_key):
                st.success(f"✅ Data {del_key} berhasil dihapus!")
            else:
                st.error("❌ Nomor polisi tidak ditemukan")

# -------------------------------
# Checkout / Pembayaran
# -------------------------------
if st.session_state.show_payment and st.session_state.current_plate:
    st.header("💳 Pembayaran & Checkout")
    
    record = manager.get(st.session_state.current_plate)
    if record:
        # Hitung biaya jika belum
        if not record.biaya_parkir:
            if not record.waktu_keluar:
                record.set_exit_now()
            else:
                record._calc_durasi_biaya()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Detail Pembayaran")
            st.write(f"**Nomor Polisi:** {record.nomor_polisi}")
            st.write(f"**Jenis:** {record.jenis_kendaraan}")
            st.write(f"**Waktu Masuk:** {record.waktu_masuk.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Waktu Keluar:** {record.waktu_keluar.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Durasi:** {str(record.durasi_parkir).split('.')[0]}")
            st.write(f"**Biaya Parkir:** Rp {record.biaya_parkir:,}")
        
        with col2:
            st.subheader("Metode Pembayaran")
            
            if not record.paid:
                metode = st.selectbox(
                    "Pilih Metode Pembayaran",
                    ["Cash", "Debit", "Credit Card", "QRIS", "E-Money", "E-Wallet"],
                    key="payment_method"
                )
                
                if metode == "Cash":
                    st.write(f"**Total:** Rp {record.biaya_parkir:,}")
                    bayar = st.number_input(
                        "Masukkan jumlah uang",
                        min_value=0,
                        value=record.biaya_parkir,
                        step=1000
                    )
                    
                    kembalian = bayar - record.biaya_parkir
                    if kembalian >= 0:
                        st.success(f"Kembalian: Rp {kembalian:,}")
                    else:
                        st.error(f"Kurang: Rp {abs(kembalian):,}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("💵 Proses Pembayaran Cash", type="primary", use_container_width=True):
                            if bayar >= record.biaya_parkir:
                                record.mark_paid("Cash")
                                st.success("✅ Pembayaran cash berhasil!")
                                st.session_state.show_payment = False
                                st.session_state.current_plate = None
                                st.rerun()
                            else:
                                st.error("❌ Jumlah pembayaran tidak mencukupi")
                    
                    with col_btn2:
                        if st.button("❌ Batalkan", type="secondary", use_container_width=True):
                            st.session_state.show_payment = False
                            st.session_state.current_plate = None
                            st.rerun()
                
                else:  # Non-cash
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"💳 Bayar via {metode}", type="primary", use_container_width=True):
                            record.mark_paid(metode)
                            st.success(f"✅ Pembayaran via {metode} berhasil!")
                            st.session_state.show_payment = False
                            st.session_state.current_plate = None
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("❌ Batalkan", type="secondary", use_container_width=True):
                            st.session_state.show_payment = False
                            st.session_state.current_plate = None
                            st.rerun()
            else:
                st.success("✅ Pembayaran sudah lunas!")
                st.write(f"**Metode:** {record.payment_method}")
                st.write(f"**Waktu Bayar:** {record.payment_time.strftime('%Y-%m-%d %H:%M')}")
                
                if st.button("Kembali ke Dashboard", type="secondary"):
                    st.session_state.show_payment = False
                    st.session_state.current_plate = None
                    st.rerun()

# -------------------------------
# Export Data
# -------------------------------
st.header("📤 Export Data")
if st.button("📥 Download Data sebagai CSV", use_container_width=True):
    df = manager.to_dataframe()
    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Klik untuk Download",
            data=csv,
            file_name=f"data_parkir_{date.today()}.csv",
            mime="text/csv"
        )
    else:
        st.warning("Tidak ada data untuk diexport")

# -------------------------------
# Footer
# -------------------------------
st.divider()
st.caption(f"© {datetime.now().year} Sistem Parkir Outlet | Terakhir diperbarui: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
