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
        A[k] = sum(y * e ** (-i * 2 * pi * t[k] * f)) / N

    return A, f


def build(A: Union[np.ndarray, Complex], f: Optional[np.ndarray] = None):
    N = len(A)
    if f is None:
        f = np.arange(0, 1, 1 / N)
    else:
        if not np.all(f[:-1] < f[1:]): raise ValueError(f"f must be sorted but received {f}")
        if len(A) != len(f): raise ValueError(f"A and f must have the same length")

    '''
    #cir=e**(i*2*pi*f)
    def fit(t):
        #if hasattr(t, '__iter__'):
        #    return np.array(list(map(fit, t)))
        return Re(sum(A * e**(i*2*pi*f* t),Complex(0,0)))
    '''
    def fit(t):
        phase = i * 2 * pi * f * t
        exp_term = e ** phase
        print(f"Im of exp_term at t={t}: {[Im(exp_term[k]) for k in range(N)]}")
        product = A * exp_term
        total = sum(product, Complex(0, 0))

        if t in (0, 2):  # only print at the broken points
            print(f"\nt={t}")
            print(f"  phase:    {phase}")
            print(f"  exp_term: {exp_term}  type={type(exp_term)}")
            print(f"  amplitude:{A}  type={type(A)}")
            print(f"  product:  {product}  type={type(product)}")
            print(f"  total:    {total}")

        return Re(total)

    return np.vectorize(fit)


def plot(f, a, b, ax=plt, res=1000):
    x = np.linspace(a, b, res)
    y = f(x)
    ax.plot(x, y)


x = np.linspace(0, 2*pi, 5)
y = np.sin(x)

print(y)

A, f = coeff(np.array([1,0,4,0]))

fit = build(A, f)
print(fit(0), fit(1), fit(2), fit(3))
print(Re(Complex(1.0, 0.0)))
print(e**(i*2*pi*0))
#plt.scatter(x, y)
#plot(np.sin, 0, 5)
#plot(fit, 0, 5)

print(A)
plt.show()
