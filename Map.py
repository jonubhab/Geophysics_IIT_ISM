from matplotlib.cm import inferno

from Ridges import *


class Map:
    def __init__(self, map, x, y):
        self.map = map
        self.x = x
        self.y = y
        self.Rs = None

    def __repr__(self):
        return f"""
        Map Size: {len(self.x)}x{len(self.y)}
        X-Range: {self.x[0]} - {self.x[-1]}
        Y-Range: {self.y[0]} - {self.y[-1]}
        """

    @staticmethod
    def __search(arr, n):
        arr = np.asarray(arr)
        idx = np.searchsorted(arr, n)
        if idx == 0:
            return 0
        if idx == len(arr):
            return len(arr) - 1
        if abs(arr[idx] - n) < abs(arr[idx - 1] - n):
            return idx
        return idx - 1

    '''
    @staticmethod
    def __search(arr, n):
        arr=np.array(arr)
        arr = np.abs(arr - n)
        return np.argmin(arr)
        '''
    '''
        low = 0
        high = len(arr) - 1
        idx = -1

        while low <= high:
            mid = (low + high) // 2

            if arr[mid]==0:
                return mid
            if arr[mid] > 0:
                idx = mid
                high = mid - 1
            else:
                low = mid + 1

        if idx==-1: raise ValueError("Array is empty.")
        return idx
        '''

    def __getitem__(self, k):
        if isinstance(k, Point): return self.map[Map.__search(self.x, k.x)][Map.__search(self.y, k.y)]

        if isinstance(k, slice):
            if np.ndim(self.map) != 1:
                if k.step:
                    result = []
                    for i in np.arange(k.start, k.stop, k.step):
                        result.append(self.map[Map.__search(self.x, i)])
                    return Map(np.array(result), np.arange(k.start, k.stop, k.step), self.y)
                else:
                    i = Map.__search(self.x, k.start)
                    f = Map.__search(self.x, k.stop) + 1
                    return Map(self.map[i:f], self.x[i:f], self.y)
            else:
                if k.step:
                    result = []
                    for i in np.arange(k.start, k.stop, k.step):
                        result.append(self.map[Map.__search(self.x, i)])
                    return np.array(result)
                else:
                    i = Map.__search(self.y, k.start)
                    f = Map.__search(self.y, k.stop) + 1
                    return Map(self.map[i:f], self.x, self.y[i:f])

        if np.ndim(self.map) != 1:
            return Map(self.map[Map.__search(self.x, k)], np.array([k]), self.y)
        else:
            return self.map[Map.__search(self.y, k)]

    # def __index__(self,k):

    def setTol(self, Ytol, mtol, Xtol):
        self.Ytol = Ytol
        self.mtol = mtol
        self.Xtol = Xtol

    def __iter__(self):
        for i in self.map: yield i

    def maxima(self, x, tol=0):
        if tol == 0:
            tol = self.Ytol

        amp_obj = self[x]
        amp_data = amp_obj.map
        peaks = set()

        y_spacing = self.y[1] - self.y[0] if len(self.y) > 1 else 1
        idx_tol = int(tol / y_spacing) if tol > 0 else 3 * y_spacing

        for idx in range(len(self.y)):
            start_bound = max(0, idx - idx_tol)
            end_bound = min(len(self.y), idx + idx_tol + 1)

            if amp_data[idx] == max(amp_data[start_bound:end_bound]):
                peaks.add(self.y[idx])

        # print(self[x],peaks)

        return np.array(list(peaks))

    def scan(self):
        for x in self.x:
            y = self.maxima(x)
            P = [Point(x, i) for i in y]
            yield x, P

    def ridges(self, mtol=0, Xtol=0):
        if mtol == 0: mtol = self.mtol
        if Xtol == 0: Xtol = self.Xtol

        R = set()

        for x, Px in tqdm(self.scan(), total=len(self.x)):
            idx = Map.__search(self.x, x) + 1
            fdx = Map.__search(self.x, x + Xtol) + 1
            A = Map(self.map[idx:fdx], self.x[idx:fdx], self.y)
            A.setTol(self.Ytol, self.mtol, self.Xtol)

            for P in Px:

                if P.junc == 0:
                    R.add(Ridge(P))
                elif P.junc > 1:
                    for i in P.net: i.close()
                    R.add(Ridge(P))

                '''
                for nx,nPx in A.scan():
                    if len(nPx) >0:
                        yi = (x - nx)*mtol +P.y
                        yf = (nx - x)*mtol +P.y

                        idy=Map.__search([i.y for i in nPx], yi)

                        for nP in nPx[idy:]:
                            '''
                for nx, nPx in A.scan():
                    if len(nPx) > 0:
                        dt = np.log(nx) - np.log(x)  # always > 0
                        yi = np.exp(np.log(P.y) - dt * mtol)  # lower bound
                        yf = np.exp(np.log(P.y) + dt * mtol)  # upper bound

                        # searchsorted gives first index >= yi (not nearest)
                        nPx_sorted = sorted(nPx, key=lambda p: p.y)
                        ys = [p.y for p in nPx_sorted]
                        idy = np.searchsorted(ys, yi, side='left')

                        for nP in nPx_sorted[idy:]:
                            if nP.y > yf:
                                break
                            actR = P.ridge
                            if actR[-1] < nP:
                                actR += nP
                            else:
                                if P.junc > 1:
                                    actR = Ridge(P)
                                    R.add(actR)
                                    actR += nP
                                else:
                                    R1, R2 = P.ridge.slice(-2)
                                    R.add(R1)
                                    R.add(R2)
                                    actR = Ridge(P)
                                    R.add(actR)
                                    actR += nP

        self.Rs = [i for i in R if i.alive]

        return self.Rs

    def plot(self, ax=plt, show=True):

        Per, Vitg = np.meshgrid(self.x, self.y)
        heatmap = ax.contourf(Per, Vitg, self.map.T, 35, cmap=inferno)

        if isinstance(ax, MT):
            fig, ax = ax.gcf(), ax.gca()
        else:
            fig = ax.get_figure()

        if self.Rs:
            for R in self.Rs:
                R.plot(ax)

        fig.colorbar(heatmap, label="Signal Strength")
        ax.set_xlabel("Time Period (s)")
        ax.set_ylabel("Group Velocity (km/s)")
        ax.set_title("2D Heatmap")

        if show: plt.show()

        '''
            tmp = "tmp67as1305kdgf.pkl"
            pickle.dump(fig, open(tmp, "wb"))
            script = f"""
import pickle
import os
import matplotlib.pyplot as plt

fig = pickle.load(open("{tmp}", "rb"))
os.remove("{tmp}")

ax = fig.axes[0]
def on_pick(event):
    artist = event.artist
    if not hasattr(artist, '_ridge'):
        return
    ridge = artist._ridge
    ridge._selected = not getattr(ridge, '_selected', False)
    col = 'red' if ridge._selected else ridge._base_col
    ridge._scatter_mid.set_color(col)
    ridge._scatter_ends.set_color(col)
    ridge._line.set_color(col)
    fig.canvas.draw_idle()

fig.canvas.mpl_connect('pick_event', on_pick)
plt.show()
"""
            subprocess.Popen([sys.executable, "-c", script])
'''
        '''
        heatmap = plt.pcolormesh(
            self.x, self.y, self.map.T, shading="auto", cmap="inferno"
            )
        '''
