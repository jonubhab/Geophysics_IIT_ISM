from typing import Union, Optional
import matplotlib.pyplot as plt
from Complex import *
import warnings


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
        A[k] = sum(y * e ** (-i * 2 * pi * t[k] * f)) / N

    return A, f


def build(A: Union[np.ndarray, Complex], f: Optional[np.ndarray] = None,n:int=0):
    N = len(A)
    if n==0 or n>N:
        if n>N: warnings.warn(f"Cannot generate {n} terms from time signal of {N} terms.")
        n=N
    if f is None:
        f = np.arange(0, 1, 1 / N)
    else:
        if not np.all(f[:-1] < f[1:]): raise ValueError(f"f must be sorted but received {f}")
        if len(A) != len(f): raise ValueError(f"A and f must have the same length")

    cir=e**(i*2*pi*f[:n])
    def fit(t):
        if hasattr(t, '__iter__'):
            return np.array(list(map(fit, t)))
        return Re(sum(A[:n]*cir**t))

    return fit


def plot(f, a, b, ax=plt, res=1000):
    x = np.linspace(a, b, res)
    y = f(x)
    ax.plot(x, y)


def transform(y: np.ndarray, t: Optional[np.ndarray] = None,n:int=0):
    if t is None: return build(*coeff(y),n)
    else: return lambda x: build(*coeff(y,t),n)(x-t[0])

x=np.array([0,1,1.5,2,3,5,8,10,11,12,13,14,15,19,20])
A=np.sin(x)

plt.scatter(x,A)
plot(np.sin,0,100)
plot(transform(A,x,n=15),0,100)

plt.show()