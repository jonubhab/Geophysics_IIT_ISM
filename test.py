import matplotlib.pyplot as plt
import numpy as np

from Ridges import Map


def test():
    amp = np.loadtxt('DCPdata/write_amp.txt')
    P = np.loadtxt('DCPdata/write_FP.txt')
    V = np.loadtxt('DCPdata/write_TV.txt')
    print("Loaded data")
    M = Map(amp, P, V)
    M.setTol(0.2, 1)
    M.scan()
    M.plot(plt)

test()
