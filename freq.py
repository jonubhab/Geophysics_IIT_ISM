import argparse
import os
import time
import tkinter as tk
from tkinter import filedialog
from typing import Optional

import h5py
import matplotlib.pyplot as plt
import numpy as np
import obspy as ob
from scipy.ndimage import minimum_filter1d
from scipy.signal import find_peaks, savgol_filter

import Fourier_Transform as ft
from Complex import Re


def parse_arguments():
    parser = argparse.ArgumentParser(description="Visualize seismic data.")

    parser.add_argument(
        "file_path",
        type=str,
        nargs="?",
        default=None,
        help="Path to the input file (optional)"
    )

    parser.add_argument("--info", action="store_true", help="Display only header")
    parser.add_argument("--freq", action="store_true", help="Visualize data in frequency domain")
    parser.add_argument("--time", action="store_true", help="Visualize data in time domain")

    return parser.parse_args()


args = parse_arguments()

def open():
    if args.file_path is not None:
        path = args.file_path
    else:
        win = tk.Tk()
        win.withdraw()
        win.attributes('-topmost', True)

        path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("Data Files", ["*.MSEED", "*.SAC"]), ("All Files", "*.*")]
        )

        win.destroy()

    print(f"File selected: {path}")
    return path


def freqfun(y: np.ndarray, t: Optional[np.ndarray] = None):
    A, F = ft.FFT(y, t)
    plt.plot(F[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2], abs(A)[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2])
    print(abs(A)[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2])
    return F[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2], abs(A)[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2]


def scan(x, y, noise_multiplier=4.0, min_height_fraction=0.008, smoothing_fraction=0.02):
    pad = int(len(x) / 10)
    decay = np.exp(-10 * np.arange(pad) ** 2)

    revx = x[::-1][-pad - 1:-1]
    end = x[1:pad + 1] + x[-1]

    x = np.concatenate((revx, x, end))
    y = np.concatenate((
        -np.flip(decay) * y[:pad][::-1],
        y,
        -decay * y[-pad:][::-1]
    ))

    high=x[-1]
    dlen = len(x) - 1
    '''
    x = np.concatenate((-x[::-1][:-1], x))
    y = np.concatenate((-y[::-1][:-1], y))
    '''

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
                'start_x': x[start_idx] if 0 < x[start_idx] < high else 0 if 0 < x[start_idx] else 0,
                'end_x': x[end_idx] if x[end_idx] < high else high,
                'sigma': sigma,
                'direction': direction,
                'si': start_idx - dlen,
                'ei': end_idx - dlen
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


def slide(mov):
    for A, f in mov:
        y = np.log(Re(abs(A)))
        '''
        ranges = scan(f, y)
        for ran in ranges:
            if ran["peak_x"] > 0:
                si = np.searchsorted(f, ran["start_x"])
                ei = np.searchsorted(f, ran["end_x"])
                si = max(1, si)
                ei = min(len(y) - 1, ei)
                if si >= ei:
                    continue
                sub = y[si:ei+1]
                if len(sub) == 0:
                    continue
                gt = max(sub) - y[si-1]
                if gt == 0:
                    continue
                y[si:ei+1] = (y[si:ei+1] - y[si-1]) / gt + y[si-1]
                '''
        yield y

def plot_spectrogram(Avf, t, F, filename='spectrogram.h5'):
    n_windows = len(t)
    n_freq    = len(F)

    cache = "/home/arjun/Anubhab Sen/PyCharm/Geophysics_IIT_ISM/freq_cache"

    if not os.path.exists(cache): os.makedirs(cache)

    filename = os.path.join(cache, filename)

    if os.path.exists(filename):
        print(f"Found existing file '{filename}', skipping streaming.")
    else:
        print(f"Streaming data into '{filename}'...")
        with h5py.File(filename, 'w') as hf:
            hf.create_dataset('buffer', shape=(n_freq, n_windows), dtype='float32')
            hf.create_dataset('t', data=t)
            hf.create_dataset('F', data=F)

            for i, amp in enumerate(Avf):
                if i >= n_windows:
                    print(f"Warning: generator yielded more than {n_windows} windows, stopping.")
                    break
                hf['buffer'][:, i] = amp
                if i % 100 == 0:
                    print(f"  {i}/{n_windows} windows processed...")

        print("Streaming complete.")

    print("Plotting...")

    with h5py.File(filename, 'r') as hf:
        buffer = hf['buffer'][:]
        t_axis = hf['t'][:]
        f_axis = hf['F'][:]


    plt.figure(figsize=(14, 6))
    vmin = np.percentile(buffer, 2)
    vmax = np.percentile(buffer, 98)


    plt.imshow(
        buffer,
        aspect='auto',
        origin='lower',
        extent=[t_axis[0], t_axis[-1], f_axis[0], f_axis[-1]],
        cmap='inferno',
        vmin=vmin,
        vmax=vmax,
        interpolation='gaussian'
    )
    plt.colorbar(label='Amplitude (Log Scale)')
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title(os.path.splitext(os.path.basename(filename))[0])
    plt.tight_layout()



file = open()
st = ob.read(file)

print(st)
print(st[0].stats)

freq = args.freq or not (args.info or args.time)
if freq:
    data = st[0].data
    t = st[0].times()

    N = len(data)
    T = t[-1] * N / (N - 1)
    print(f"\nFrequency Limit: {N / T} Hz")
    print(f"Time Limit: {T} s")
    win = int(input("Window Size: "))
    step = int(input("Step Size: "))
    print(f"Frequency Resolution: {N / T / t[win]} Hz")
    print(f"Time Resolution: {T / N * step} s")
    time.sleep(2)
    n_windows = (len(data) - win) // step + 1

    window = ft.SWFT(data, win, t, step=step)
    F = next(window)
    Avf = slide(window)

    plot_spectrogram(Avf, t[:n_windows], F,
                     str(win) + "_" + str(step) + "_" + os.path.splitext(os.path.basename(file))[0] + ".h5")

if args.time or not (args.info or args.freq):
    st.plot()  # show=False)
'''
if args.info:
    data = st[0].data
    t = st[0].times()
    N=len(data)
    T=t[-1] * N / (N - 1)
    print(f"Frequency Limit: {N/T} Hz")
    print(f"Frequency Resolution: {N/T**2} Hz")
    print(f"Time Limit: {T} s")
    print(f"Time Resolution: {T/N} s")
    x, y = freqfun(data, t)
    peaks = scan(x, y)
    i = 0
    for peak in peaks:
        if peak["peak_x"] > 0:
            if peak["si"] >= peak["ei"]:
                continue
            i += 1
            print(f'\nWindow #{i}\n'
                  f'Frequency: {peak["peak_x"]} Hz\n'
                  f'Relative Peak Amplitude: {max(y[peak["si"]:peak["ei"] + 1])}\n'
                  f'Range: {peak["start_x"]} Hz to {peak["end_x"]} Hz \n'
                  f'Standard Deviation: {peak["sigma"]}\n')
'''
if freq: plt.show()
