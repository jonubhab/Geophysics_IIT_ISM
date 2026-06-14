
import numpy as np

from Map import *


def test():
    amp = np.loadtxt('DCPdata/write_amp.txt')
    P = np.loadtxt('DCPdata/write_FP.txt')
    V = np.loadtxt('DCPdata/write_TV.txt')
    print("Loaded data")
    M = Map(amp, P, V)
    M.setTol(0.2, 1, 1.5)
    M.ridges()
    M.plot(plt)

test()

'''
P = np.loadtxt('DCPdata/write_FP.txt')

print("Linear: ",P)
print(P[1:]-P[:-1])

L=np.log(P)
print("\nLogarithmic: ",L)
print(L[1:]-L[:-1])

E = np.exp(P)
print("\nExponential: ",E)
print(E[1:]-E[:-1])
'''
