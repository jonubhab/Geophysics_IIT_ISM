import sys

import numpy as np

'''
'''
amp = np.loadtxt('write_amp.txt')  # this the FTAN matrix
amp = amp.T
P = np.loadtxt('write_FP.txt')  # this is the period axis
V = np.loadtxt('write_TV.txt')


def test():
    import importlib.util
    from pathlib import Path
    file_path = (
        "/home/arjun/anaconda3/envs/tomo/lib/python3.10/"
        "site-packages/msnoise_tomo/Ridges.py"
    )

    if Path(file_path).exists():
        spec = importlib.util.spec_from_file_location("Ridges", file_path)
        Ridges = importlib.util.module_from_spec(spec)
        sys.modules["Ridges"] = Ridges
        spec.loader.exec_module(Ridges)
        Map = Ridges.Map
    else:
        print(f"Error: The file at {file_path} does not exist.")
    import matplotlib.pyplot as plt
    M = Map(amp.T, P, V)
    M.setTol(0.2, 1)
    M.scan(plt=plt)
    plt.show()
    sys.exit(0)


test()
'''
'''
