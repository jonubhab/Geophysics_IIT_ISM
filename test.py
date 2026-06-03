from Fourier_Transform import *


def f(t):
    return np.cos(t) + np.cos(2 * t) + np.cos(3 * t) + np.cos(4 * t) + np.cos(5 * t)


def freq(y: np.ndarray, t: Optional[np.ndarray] = None):
    win = np.hanning(len(y))
    A, F = FFT(y * win, t)
    plt.plot(F[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2], abs(A)[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2])
    print(abs(A)[:1 + int(np.ceil(len(A) / 2)) - len(A) % 2])
    plt.show()
