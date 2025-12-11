import streamlit as st
import random
import string
from datetime import datetime, timedelta
import pandas as pd

# ===============================
#     DATA MODEL (LINKED LIST)
# ===============================
class Node:
    def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
        self.nomor_polisi = nomor_polisi
        self.jenis_kendaraan = jenis_kendaraan
        self.waktu_masuk = datetime.strptime(waktu_masuk, "%H:%M")

        # Random waktu keluar (simulasi bisnis parkir)
        lama = random.randint(30, 720)  # 30 menit – 12 jam
        self.waktu_keluar = self.waktu_masuk + timedelta(minutes=lama)

        self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
        self.biaya_parkir = self.hit_biaya()
        self.next = None

    def hit_biaya(self):
        jam = int(self.durasi_parkir.total_seconds() // 3600)
        jam = max(1, jam)

        if self.jenis_kendaraan == "Mobil":
            return 5000 + (jam - 1) * 3000
        return 3000 + (jam - 1) * 2000


class DataParkir:
    def __init__(self):
        self.head = N
