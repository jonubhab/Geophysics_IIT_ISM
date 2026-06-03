import tkinter as tk
from tkinter import filedialog

import obspy as ob
from matplotlib import pyplot as plt
from plyer import notification

import Fourier_Transform as ft


def open():
    win = tk.Tk()
    win.withdraw()
    win.attributes('-topmost', True)

    path = filedialog.askopenfilename(
        title="Select a File",
        filetypes=[("MSEED Files", "*.MSEED"), ("All Files", "*.*")]
    )

    win.destroy()
    return path


def notify():
    notification.notify(
        title="Fourier Transform",
        message="Data has been successfully transformed",
        app_name="Python Script",
        timeout=10
    )


st = ob.read(open())

# Print basic information
print(st)

# Print detailed header
print(st[0].stats)

# Access the raw numerical waveform data as a NumPy array
data = st[0].data
print(len(data))
print("Fourier Transformation begins...")
ft.plot(ft.transform(data), 0, len(data), plt, len(data))
print("Fourier Transformation ends...")

plt.show()

# Plots the wave
# st.plot()

notify()
