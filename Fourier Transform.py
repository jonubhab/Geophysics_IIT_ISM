from typing import Union, Optional

import matplotlib.pyplot as plt

from Complex import *


def coeff(y: np.ndarray, t: Optional[np.ndarray] = None):
    N = len(y)
    if t is None:
        t = np.arange(N)
    else:
        if not np.all(t[:-1] < t[1:]): raise ValueError(f"t must be sorted but received {t}")
        if len(y) != len(t): raise ValueError(f'y(len:{N}) and t(len:{len(t)}) must have the same length')
        t -= t[0]
    T = t[-1] * N / (N - 1)
    f = t * N / T ** 2
    A = Complex(np.zeros(N), np.zeros(N))
    for k in range(N):
        A[k] = sum(y * e ** (-i * 2 * pi * t[k] * t * N / T ** 2)) / N

    return A, f


def build(A: Union[np.ndarray, Complex], f: Optional[np.ndarray] = None):
    N = len(A)
    if f is None:
        f = np.arange(0, 1, 1 / N)
    else:
        if not np.all(f[:-1] < f[1:]): raise ValueError(f"f must be sorted but received {f}")
        if len(A) != len(f): raise ValueError(f"A and f must have the same length")

    def fit(t):
        if hasattr(t, '__iter__'):
            return np.array(list(map(fit, t)))
        return Re(sum(A * e ** (i * 2 * pi * f * t)))

    return fit


def plot(f, a, b, ax=plt, res=1000):
    x = np.linspace(a, b, res)
    y = f(x)
    ax.plot(x, y)


x = np.linspace(0, 4, 5)
y = np.sin(x)

A, f = coeff(y)

plt.scatter(x, y)
plot(np.sin, 0, 5)
plot(build(A, f), 0, 5)

print(A)
plt.show()
