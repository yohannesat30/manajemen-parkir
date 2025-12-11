import tkinter as tk
from tabulate import tabulate
import random
import string
from datetime import datetime, timedelta
from tkinter import messagebox

class Node:
  def __init__(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
    self.nomor_polisi = nomor_polisi
    self.jenis_kendaraan = jenis_kendaraan
    self.waktu_masuk = datetime.strptime(waktu_masuk, "%H:%M")
    random_minutes = random.randint(1, 1440)
    self.waktu_keluar = self.waktu_masuk + timedelta(minutes=random_minutes)
    self.durasi_parkir = self.waktu_keluar - self.waktu_masuk
    self.biaya_parkir = self.calculate_biaya_parkir()
    self.next = None

  def calculate_biaya_parkir(self):
    hours = self.durasi_parkir.total_seconds() // 3600
    if self.jenis_kendaraan == "Mobil":
      cost = 5000 + (hours - 1) * 1000
    else:
      cost = 3000 + (hours - 1) * 1000
    return cost

class DataParkir:
  def __init__(self):
    self.head = None

  def add_data(self, nomor_polisi, jenis_kendaraan, waktu_masuk):
    new_node = Node(nomor_polisi, jenis_kendaraan, waktu_masuk)
    if self.head is None:
      self.head = new_node
    else:
      current = self.head
      while current.next:
        current = current.next
      current.next = new_node

  def delete_data(self, nomor_polisi):
    if self.head is None:
      return False
    if self.head.nomor_polisi == nomor_polisi:
      self.head = self.head.next
      return True
    current = self.head
    while current.next:
      if current.next.nomor_polisi == nomor_polisi:
        current.next = current.next.next
        return True
      current = current.next
    return False

  def display_data(self):
    i = 0
    sorted_data = sorted(self.get_data(), key=lambda x: x.waktu_masuk)
    table_data = []
    for data in sorted_data:
      i += 1
      table_data.append([
        i,
        data.nomor_polisi,
        data.jenis_kendaraan,
        data.waktu_masuk.strftime("%H:%M"),
        data.waktu_keluar.strftime("%H:%M"),
        str(data.durasi_parkir),
        str(data.biaya_parkir)
      ])
    headers = ["No", "Nomor Polisi", "Jenis Kendaraan", "Waktu Masuk", "Waktu Keluar", "Durasi Parkir", "Biaya Parkir"]
    return tabulate(table_data, headers, tablefmt="grid")

  def display_filter(self, jenis_kendaraan=None):
    current = self.head
    i = 0
    sorted_data = sorted(self.get_data(), key=lambda x: x.waktu_masuk)
    table_data = []
    for data in sorted_data:
      if jenis_kendaraan is None or data.jenis_kendaraan == jenis_kendaraan:
        i += 1
        table_data.append([
          i,
          data.nomor_polisi,
          data.jenis_kendaraan,
          data.waktu_masuk.strftime("%H:%M"),
          data.waktu_keluar.strftime("%H:%M"),
          str(data.durasi_parkir),
          str(data.biaya_parkir)
        ])
    headers = ["No", "Nomor Polisi", "Jenis Kendaraan", "Waktu Masuk", "Waktu Keluar", "Durasi Parkir", "Biaya Parkir"]
    return tabulate(table_data, headers, tablefmt="grid")

  def display_sort(self, reverse):
    i = 0
    sorted_data = sorted(self.get_data(), key=lambda x: x.durasi_parkir, reverse=reverse)
    table_data = []
    for data in sorted_data:
      i += 1
      table_data.append([
        i,
        data.nomor_polisi,
        data.jenis_kendaraan,
        data.waktu_masuk.strftime("%H:%M"),
        data.waktu_keluar.strftime("%H:%M"),
        str(data.durasi_parkir),
        str(data.biaya_parkir)
      ])
    headers = ["No", "Nomor Polisi", "Jenis Kendaraan", "Waktu Masuk", "Waktu Keluar", "Durasi Parkir", "Biaya Parkir"]
    return tabulate(table_data, headers, tablefmt="grid")

  def update_data(self, nomor_polisi, new_nomor_polisi, new_jenis_kendaraan, new_waktu_masuk):
    current = self.head
    while current:
      if current.nomor_polisi == nomor_polisi:
        current.nomor_polisi = new_nomor_polisi
        current.jenis_kendaraan = new_jenis_kendaraan
        current.waktu_masuk = datetime.strptime(new_waktu_masuk, "%H:%M")
      current = current.next
    return True

  def get_data(self):
    data = []
    current = self.head
    while current:
      data.append(current)
      current = current.next
    return data

  def search_data(self, nomor_polisi):
    current = self.head
    while current:
      if current.nomor_polisi == nomor_polisi:
        return current
      current = current.next
    return None

def generate_random_data():
  jenis_kendaraans = ["Mobil", "Motor"]
  for _ in range(20):
    random_number = random.randint(1000, 9999)
    random_string = ''.join(random.choices(string.ascii_uppercase, k=3))
    nomor_polisi = f"B {random_number} {random_string}"
    jenis_kendaraan = random.choice(jenis_kendaraans)
    waktu_masuk = f"{random.randint(6, 23)}:{random.randint(0, 59)}"
    parking_data.add_data(nomor_polisi, jenis_kendaraan, waktu_masuk)

def add_data():
  nomor_polisi = entry_nomor_polisi.get()
  jenis_kendaraan = entry_jenis_kendaraan.get()
  waktu_masuk = entry_waktu_masuk.get()
  parking_data.add_data(nomor_polisi, jenis_kendaraan, waktu_masuk)
  entry_nomor_polisi.delete(0, tk.END)
  entry_jenis_kendaraan.delete(0, tk.END)
  entry_waktu_masuk.delete(0, tk.END)
  update_display(parking_data.display_data())

def search_data():
  nomor_polisi = entry_search.get()
  searched_data = parking_data.search_data(nomor_polisi)
  entry_nomor_polisi.delete(0, tk.END)
  entry_jenis_kendaraan.delete(0, tk.END)
  entry_waktu_masuk.delete(0, tk.END)
  if searched_data:
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, f"Nomor Polisi: {searched_data.nomor_polisi}\nJenis Kendaraan: {searched_data.jenis_kendaraan}\nWaktu Masuk: {searched_data.waktu_masuk.strftime('%H:%M')}\nWaktu Keluar: {searched_data.waktu_keluar.strftime('%H:%M')}\nDurasi Parkir: {str(searched_data.durasi_parkir)}\nBiaya Parkir: {str(searched_data.biaya_parkir)}")
    entry_nomor_polisi.insert(tk.END, searched_data.nomor_polisi)
    entry_jenis_kendaraan.insert(tk.END, searched_data.jenis_kendaraan)
    entry_waktu_masuk.insert(tk.END, searched_data.waktu_masuk.strftime("%H:%M"))
  else:
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Data tidak ditemukan.")

def update_data():
  nomor_polisi_lama = entry_search.get()
  searched_data = parking_data.search_data(nomor_polisi_lama)
  if searched_data:
    nomor_polisi = entry_nomor_polisi.get()
    if nomor_polisi == "":
      nomor_polisi = nomor_polisi_lama
    jenis_kendaraan = entry_jenis_kendaraan.get()
    if jenis_kendaraan == "":
      jenis_kendaraan = searched_data.jenis_kendaraan
    waktu_masuk = entry_waktu_masuk.get()
    if waktu_masuk == "":
      waktu_masuk = searched_data.waktu_masuk.strftime("%H:%M")
    parking_data.update_data(nomor_polisi_lama, nomor_polisi, jenis_kendaraan, waktu_masuk)
    entry_nomor_polisi.delete(0, tk.END)
    entry_jenis_kendaraan.delete(0, tk.END)
    entry_waktu_masuk.delete(0, tk.END)
    update_display(parking_data.display_data())
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Data berhasil diupdate.")
  else:
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Data tidak ditemukan.")

def delete_data():
  nomor_polisi = entry_search.get()
  if parking_data.delete_data(nomor_polisi):
    entry_search.delete(0, tk.END)
    update_display(parking_data.display_data())
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Data berhasil dihapus.")
  else:
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Data tidak ditemukan.")

def on_exit():
  if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
    root.destroy()

def update_display(display_method):
  display_text.delete(1.0, tk.END)
  display_text.insert(tk.END, display_method)

# Create an instance of DataParkir
parking_data = DataParkir()

# Create the GUI
root = tk.Tk()
root.title("Parking Data")
root.geometry("1280x720")

# Create labels
label_nomor_polisi = tk.Label(root, text="Nomor Polisi:")
label_jenis_kendaraan = tk.Label(root, text="Jenis Kendaraan:")
label_waktu_masuk = tk.Label(root, text="Waktu Masuk (HH:MM):")
label_search = tk.Label(root, text="Search by Nomor Polisi:")

# Create entry fields
entry_nomor_polisi = tk.Entry(root)
entry_jenis_kendaraan = tk.Entry(root)
entry_waktu_masuk = tk.Entry(root)
entry_search = tk.Entry(root)

# Create buttons
button_add_data = tk.Button(root, text="Add Data", command=add_data)
button_search_data = tk.Button(root, text="Search Data", command=search_data)
button_update_data = tk.Button(root, text="Update Data", command=update_data)
button_delete_data = tk.Button(root, text="Delete Data", command=delete_data)
button_exit = tk.Button(root, text="Exit", command=on_exit)
button_display_data = tk.Button(root, text="Display Data", command=lambda: update_display(parking_data.display_data()))
button_filter_mobil = tk.Button(root, text="Filter Mobil", command=lambda: update_display(parking_data.display_filter("Mobil")))
button_filter_motor = tk.Button(root, text="Filter Motor", command=lambda: update_display(parking_data.display_filter("Motor")))
button_sort_time_asc = tk.Button(root, text="Sort Time Asc", command=lambda: update_display(parking_data.display_sort(False)))
button_sort_time_desc = tk.Button(root, text="Sort Time Desc", command=lambda: update_display(parking_data.display_sort(True)))

# Create text areas
display_text = tk.Text(root, height=20, width=113)
result_text = tk.Text(root, height=20, width=35)

# Grid layout
label_nomor_polisi.grid(row=0, column=0, padx=10, pady=10, sticky="w")
entry_nomor_polisi.grid(row=0, column=0, padx=10, pady=10)
label_jenis_kendaraan.grid(row=1, column=0, padx=10, pady=10, sticky="w")
entry_jenis_kendaraan.grid(row=1, column=0, padx=10, pady=10)
label_waktu_masuk.grid(row=2, column=0, padx=10, pady=10, sticky="w")
entry_waktu_masuk.grid(row=2, column=0, padx=10, pady=10)
button_add_data.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")
label_search.grid(row=4, column=0, padx=10, pady=10, sticky="w")
entry_search.grid(row=4, column=0, padx=10, pady=10)
button_search_data.grid(row=4, column=0, columnspan=10, padx=360, pady=10, sticky="w")
button_update_data.grid(row=4, column=0, columnspan=10, padx=460, pady=10 ,sticky="w")
button_delete_data.grid(row=4, column=0, columnspan=10, padx=560, pady=10, sticky="w")
button_display_data.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")
button_filter_mobil.grid(row=5, column=0, columnspan=2, padx=110, pady=10, sticky="w")
button_filter_motor.grid(row=5, column=0, columnspan=2, padx=210, pady=10, sticky="w")
button_sort_time_asc.grid(row=5, column=0, columnspan=2, padx=310, pady=10, sticky="w")
button_sort_time_desc.grid(row=5, column=0, columnspan=2, padx=410, pady=10, sticky="w")
display_text.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
result_text.grid(row=6, column=5, columnspan=2, padx=10, pady=10)
button_exit.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="w")

# Generate random data
generate_random_data()

# Update display
update_display(parking_data.display_data())

root.mainloop()
