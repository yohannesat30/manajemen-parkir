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
    def __init__(self, nomor_polisi, jenis_kendaraan):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        self._tarif_dasar = 0
    
    def get_tarif_dasar(self):
        return self._tarif_dasar

class Node(Kendaraan):
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
        return {
            "nomor_polisi": self.nomor_polisi,
            "jenis_kendaraan": self.jenis_kendaraan,
            "waktu_masuk": self.waktu_masuk.strftime("%H:%M"),
            "waktu_keluar": self.waktu_keluar.strftime("%H:%M"),
            "status_pembayaran": self.status_pembayaran,
            "metode_bayar": self.metode_bayar
        }


class DataParkir:
    def __init__(self):
        self.head = None
        self.load_data()

    # File Handling (Load Data) - Indentasi diperiksa secara ketat di sini
    def load_data(self):
        if os.path.exists(FILE_PARKIR):
            try:
                with open(FILE_PARKIR, 'r') as f:
                    data_list = json.load(f)
                    for data in data_list:
                        # Baris 85
                        node = Node(data['nomor_polisi'], data['jenis_kendaraan'], data['waktu_masuk'])
                        # Memperbarui properti
                        node.waktu_keluar = datetime.strptime(data['waktu_keluar'], "%H:%M")
                        node.durasi_parkir = node.waktu_keluar - node.waktu_masuk
                        # Baris 95
                        node.biaya_parkir = node.hit_biaya() 
                        node.status_pembayaran = data['status_pembayaran']
                        node.metode_bayar = data['metode_bayar']
                        
                        # Menambahkan node ke linked list
                        if not self.head:
                            self.head = node
                        else:
                            cur = self.head
                            while cur.next:
                                cur = cur.next
                            cur.next = node
            # Indentasi blok except harus sejajar dengan try
            except json.JSONDecodeError:
                st.warning("Gagal memuat data parkir (file JSON rusak).")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memuat data: {e}")

    # File Handling (Save Data)
    def save_data(self):
        data_to_save = [d.to_dict() for d in self.all_data()]
        try:
            with open(FILE_PARKIR, 'w') as f:
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            st.error(f"Gagal menyimpan data ke file: {e}")

    def add(self, nomor_polisi, jenis, waktu):
        if self.search(nomor_polisi):
            return False 
            
        node = Node(nomor_polisi, jenis, waktu)
        if not self.head:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node
            
        self.save_data()
        return True

    def search(self, nomor_polisi):
        cur = self.head
        while cur:
            if cur.nomor_polisi == nomor_polisi:
                return cur
            cur = cur.next
        return None

    def delete(self, nomor_polisi):
        if not self.head:
            return False

        if self.head.nomor_polisi == nomor_polisi:
            self.head = self.head.next
            self.save_data()
            return True

        cur = self.head
        while cur.next:
            if cur.next.nomor_polisi == nomor_polisi:
                cur.next = cur.next.next
                self.save_data()
                return True
            cur = cur.next
        return False
        
    def bayar(self, nomor_polisi, metode):
        node = self.search(nomor_polisi)
        if node and node.status_pembayaran == "Belum Bayar":
            node.status_pembayaran = "Lunas"
            node.metode_bayar = metode
            self.save_data()
