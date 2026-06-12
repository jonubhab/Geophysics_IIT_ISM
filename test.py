import matplotlib.pyplot as plt
import numpy as np

from .Ridges import Map


def test():
    amp = np.loadtxt('write_amp.txt')
    P = np.loadtxt('write_FP.txt')
    V = np.loadtxt('write_TV.txt')
    M = Map(amp, P, V)
    M.setTol(0.2, 1)
    M.scan()
    M.plot(plt)

test()
