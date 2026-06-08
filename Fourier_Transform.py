import warnings
from typing import Union, Optional

import matplotlib.pyplot as plt
from finufft import nufft1d3 as nufft
from joblib import Memory

from Complex import *

mem = Memory("./fourier_cache", verbose=0)


@mem.cache
def DFT(y: np.ndarray, t: Optional[np.ndarray] = None):
    N = len(y)
    if t is None:
        t = np.arange(N)
        return DFT(y, t)
    if not np.all(t[:-1] < t[1:]): raise ValueError(f"t must be sorted but received {t}")
    if len(y) != len(t): raise ValueError(f'y(len:{N}) and t(len:{len(t)}) must have the same length')
    t -= t[0]
    T = t[-1] * N / (N - 1)
    f = t * N / T ** 2
    A = Complex(np.zeros(N), np.zeros(N))
    for k in range(N):
        A[k] = sum(y * e ** (-i * 2 * pi * t[k] * f)) / N

    return A, f


def FFT(y: np.ndarray, t: Optional[np.ndarray] = None):
    N = len(y)
    if t is None:
        t = np.arange(N)
        return FFT(y, t)
    if not np.all(t[:-1] < t[1:]): raise ValueError(f"t must be sorted but received {t}")
    if len(y) != len(t): raise ValueError(f"y(len:{N}) and t(len:{len(t)}) must have the same length")
    t = t - t[0]
    T = t[-1] * N / (N - 1)
    f = t * N / T ** 2

    if N > 1:
        dt = t[1:] - t[:-1]
        uniform = np.allclose(dt, dt[0], rtol=1e-9, atol=1e-12)
    else:
        uniform = True

    if uniform:
        A = np.fft.fft(y) / N
    else:
        x = (2 * np.pi * t)
        A = np.conj(nufft(x, y, f)) / N

    return Complex(A.real, A.imag), f

@mem.cache
def SWFT(y: np.ndarray, win:int, t: Optional[np.ndarray] = None, update:int=0,step=1):
    if update==0:
        update=win
    N = len(y)
    if t is None:
        t = np.arange(N)

    A,f=None,None
    half_len = 1 + int(np.ceil(win / 2)) - win % 2
    cir = e ** (i * 2 * np.pi * np.arange(half_len) / win)
    cirs = cir ** step
    cir_neg_powers = np.array([cir ** (-s) for s in range(step)])
    for j in range(N-win+1):
        if j%update==0:
            A, f = FFT(y[j:j + win], t[j:j + win])
            A=A[:half_len]
            f=f[:half_len]
            A=Complex([a.x for a in A],[a.y for a in A])
            if j == 0: yield f
            yield A, f
        elif j % step == 0:
            diffs = np.array([y[j + win + s - 1] - y[j + s - 1] for s in range(step)])
            correction = np.dot(diffs, cir_neg_powers) / win
            A = (A * cirs) + correction
            yield A, f




class fit:
    def __init__(s, A, n, cir):
        s.A = A
        s.n = n
        s.cir = cir

    def __call__(s, t):
        if hasattr(t, '__iter__'):
            return np.array(list(map(s, t)))
        return Re(sum(s.A[:s.n] * s.cir ** t))


@mem.cache
def build(A: Union[np.ndarray, Complex], f: Optional[np.ndarray] = None, n: int = 0):
    N = len(A)
    if n == 0 or n > N:
        if n > N: warnings.warn(f"Cannot generate {n} terms from a time signal of {N} terms.")
        return build(A, f, N)
    if f is None:
        f = np.arange(0, 1, 1 / N)
        return build(A, f, n)
    else:
        if not np.all(f[:-1] < f[1:]): raise ValueError(f"f must be sorted but received {f}")
        if len(A) != len(f): raise ValueError(f"A and f must have the same length")

    cir = e ** (i * 2 * pi * f[:n])

    return fit(A, n, cir)


def plot(f, a, b, ax=plt, res=1000):
    x = np.linspace(a, b, res)
    y = f(x)
    ax.plot(x, y)


def transform(y: np.ndarray, t: Optional[np.ndarray] = None, n: int = 0, dft=False):
    if dft:
        return build(*DFT(y, t), n)
    else:
        return build(*FFT(y, t), n)


@mem.cache
def sample(f, t):
    return f(t)
