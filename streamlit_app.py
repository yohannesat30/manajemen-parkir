import streamlit as st
import random
import string
import json 
from datetime import datetime, timedelta
import pandas as pd
import os 

# Nama file untuk menyimpan data
FILE_PARKIR = 'parking_data.json'

# ===============================
#       DATA MODEL (LINKED LIST & OOP Lanjutan)
# ===============================

class Kendaraan:
    """Kelas dasar untuk kendaraan, mendemonstrasikan Basic OOP."""
    def __init__(self, nomor_polisi, jenis_kendaraan):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        self._tarif_dasar = 0
    
    def get_tarif_dasar(self):
        """Method untuk mendapatkan tarif dasar, bisa di-override."""
        return self._tarif_dasar

class Node(Kendaraan):
    """Representasi data parkir, menggunakan Linked List Node."""
    # Override constructor
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk_str):
        super().__init__(nomor_polisi, jenis_kendaraan)
        
        self.waktu_masuk = datetime.strptime(waktu_masuk_str, "%H:%M")

        lama = random.randint(30, 720)  
        self.waktu_keluar = self.waktu_masuk + timedelta(minutes=lama)
        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        
        self.biaya_parkir = self.hit_biaya()
        self.status_pembayaran = "Belum Bayar" 
        self.metode_bayar = None 
        
        self.next = None

    def get_tarif_dasar(self):
        if self.jenis_kendaraan == "Mobil":
            return 5000
        return 3000

    def hit_biaya(self):
        """Menghitung biaya parkir berdasarkan durasi dan jenis kendaraan."""
        jam_total = int(self.durasi_parkir.total_seconds() // 3600)
        jam_total = max(1, jam_total)
        
        tarif_dasar = self.get_tarif_dasar() 
        tarif_per_jam_berikutnya = 0
        
        if self.jenis_kendaraan == "Mobil":
            tarif_per_jam_berikutnya = 3000
        else:
            tarif_per_jam_berikutnya = 2000
        
        biaya = tarif_dasar + (jam_total - 1) * tarif_per_jam_berikutnya
        return biaya
        
    def to_dict(self):
        """Fungsi pembantu untuk konversi ke Dictionary untuk File Handling (JSON)."""
        return {
            "nomor_polisi": self.nomor_polisi,
            "jenis_kendaraan": self.jenis_kendaraan,
            "waktu_masuk": self.waktu_masuk.strftime("%H:%M"),
            "waktu_keluar": self.waktu_keluar.strftime("%H:%M"),
            "status_pembayaran": self.status_pembayaran,
            "metode_bayar": self.metode_bayar
        }


class DataParkir:
    """Class utama untuk mengelola data parkir menggunakan Linked List."""
    def __init__(self):
        self.head = None
        self.load_data()

    # File Handling (Load Data)
    def load_data(self):
        """Memuat data dari FILE_PARKIR (JSON) saat aplikasi dimulai."""
        if os.path.exists(FILE_PARKIR):
            try:
                with open(FILE_PARKIR, 'r') as f:
                    data_list = json.load(f)
                    for data in data_list:
                        node = Node(data['nomor_polisi'], data['jenis_kendaraan'], data['waktu_masuk'])
                        node.waktu_keluar = datetime.strptime(data['waktu_keluar'], "%H:%M")
                        node.durasi_parkir = node.waktu_keluar - node.waktu_masuk
                        node.biaya_parkir = node.hit_biaya()
