import os
import numpy as np


dir="/home/arjun/WESTERN-TIBET/Control/RAW_FTAN_FILES/01/"

def plot_save(wave):
    for file in os.listdir(dir):
        path = os.path.join(dir, file, wave)

        os.chdir(path)

        import matplotlib.pyplot as plt

        try:
            amp = np.loadtxt('write_amp.txt').T

            # Process the dispersion curve
            U = np.loadtxt('write_TV.txt')
            P = np.loadtxt('write_FP.txt')
            # get axes limits
            xmin = min(P)
            xmax = max(P)
            ymin = min(U)
            ymax = max(U)

            # setup matrix for contour plot
            Per, Vitg = np.meshgrid(P, U)
            plt.figure()
            plt.contourf(Per, Vitg, amp, 35, cmap='inferno')
            plt.colorbar()
            # plt.contour(Per, Vitg, amp, 35, colors='k')

            plt.xlim(xmin, xmax)
            plt.ylim(ymin, ymax)

            plt.xlabel("Period (s)")
            plt.ylabel("Velocity (km/s)")

            NET1, STA1, NET2, STA2, crap = file.split('_')

            title = "%s.%s - %s.%s" % (NET1, STA1, NET2, STA2)

            plt.title("FTAN\n" + title)

            plt.savefig(f"{file}_{wave}.png")

            plt.close()
        except ValueError:
            print("Value Error in ",file)


plot_save("RW")
plot_save("LW")