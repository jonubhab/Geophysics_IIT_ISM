import tkinter as tk
from tkinter import filedialog
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import obspy as ob
from scipy.ndimage import minimum_filter1d
from scipy.signal import find_peaks, savgol_filter

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


def freq(y: np.ndarray, t: Optional[np.ndarray] = None):
    A, F = ft.FFT(y, t)
    plt.plot(F[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2], abs(A)[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2])
    print(abs(A)[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2])
    return F[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2], abs(A)[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2]


def scan(x, y, noise_multiplier=4.0, min_height_fraction=0.008, smoothing_fraction=0.02):
    x = np.concatenate((-x[::-1][:-1], x))
    y = np.concatenate((-y[::-1][:-1], y))
    N = len(y)

    if len(x) != N:
        raise ValueError("x and y arrays must have the same length.")
    wlen = int(smoothing_fraction * N)
    if wlen % 2 == 0:
        wlen += 1
    if wlen < 5:
        wlen = 5
    yfil = savgol_filter(y, wlen, polyorder=2)

    bwin = max(int(0.10 * N), wlen * 2)
    base = minimum_filter1d(yfil, size=bwin)

    hi = yfil - savgol_filter(yfil, min(wlen * 3, N // 2 | 1), 2)
    mad = np.median(np.abs(hi))
    noise_std = 1.4826 * mad
    if noise_std <= 0:
        noise_std = np.std(yfil) * 0.05 if np.std(yfil) > 0 else 1e-5

    y_zeroed = yfil - base
    y_span = np.max(yfil) - np.min(yfil)

    absolute_min_height = min_height_fraction * y_span

    detected_curves = []

    for direction in ['positive', 'negative']:
        signal = y_zeroed if direction == 'positive' else -y_zeroed

        min_prominence = max(noise_multiplier * noise_std, absolute_min_height)

        peaks, _ = find_peaks(signal, prominence=min_prominence, distance=wlen // 2)

        for peak_idx in peaks:
            if signal[peak_idx] < min_prominence:
                continue

            threshold = max(0.10 * signal[peak_idx], 2.0 * noise_std)

            start_idx = peak_idx
            while start_idx > 0:
                if signal[start_idx] <= threshold:
                    break
                if start_idx < peak_idx - 1 and signal[start_idx] > signal[start_idx + 1]:
                    if signal[start_idx] - signal[start_idx + 1] > noise_std:
                        break
                start_idx -= 1

            end_idx = peak_idx
            while end_idx < N - 1:
                if signal[end_idx] <= threshold:
                    break
                if end_idx > peak_idx + 1 and signal[end_idx] > signal[end_idx - 1]:
                    if signal[end_idx] - signal[end_idx - 1] > noise_std:
                        break
                end_idx += 1

            curve_slice_x = x[start_idx: end_idx + 1]
            curve_slice_y = signal[start_idx: end_idx + 1]

            if len(curve_slice_x) < 3:
                continue

            total_area = np.sum(curve_slice_y)
            if total_area > 0:
                centroid = np.sum(curve_slice_x * curve_slice_y) / total_area
                variance = np.sum((curve_slice_x ** 2) * curve_slice_y) / total_area - (centroid ** 2)
                sigma = np.sqrt(max(0, variance))
            else:
                sigma = (x[end_idx] - x[start_idx]) / 4.0

            detected_curves.append({
                'peak_x': x[peak_idx],
                'peak_y': yfil[peak_idx],
                'start_x': x[start_idx] if x[start_idx] > 0 else 0,
                'end_x': x[end_idx],
                'sigma': sigma,
                'direction': direction
            })

    cleaned_curves = []
    for curve in sorted(detected_curves, key=lambda c: abs(c['peak_y'] - np.median(y)), reverse=True):
        overlap = False
        for clean in cleaned_curves:
            if (curve['peak_x'] >= clean['start_x'] and curve['peak_x'] <= clean['end_x']):
                overlap = True
                break
        if not overlap:
            cleaned_curves.append(curve)
    cleaned_curves = sorted(cleaned_curves, key=lambda c: c['start_x'])
    return cleaned_curves


st = ob.read(open())
data = st[0].data
t = st[0].times()
x, y = freq(data, t)

peaks = scan(x, y)

i = 0
for peak in peaks:
    if peak["peak_x"] > 0:
        i += 1
        print(f'\nWindow #{i}\n'
              f'Frequency: {peak["peak_x"]} Hz\n'
              f'Peak Amplitude: {peak["peak_y"]}\n'
              f'Range: {peak["start_x"]} Hz to {peak["end_x"]} Hz \n'
              f'Standard Deviation: {peak["sigma"]}\n')

plt.show()
