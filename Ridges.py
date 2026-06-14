import pickle
import subprocess
import sys
from copy import deepcopy
from functools import total_ordering, partial
from types import ModuleType as MT
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import inferno
from tqdm import tqdm


@total_ordering
class Point:
    def __init__(self, x, y):
        self.__x = x
        self.__y = y
        self.net = {}

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    def __call__(self):
        return self.x, self.y

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def slope(self, P):
        if isinstance(P, Point):
            try:
                return (P.y - self.y) / (P.x - self.x)
            except ZeroDivisionError:
                return float('inf')
        else:
            raise TypeError(f"{type(P)} object {P} is incompatible to point {self}")

    def __gt__(self, P):
        if isinstance(P, Point):
            return self.x > P.x
        else:
            raise TypeError(f"{type(P)} object {P} is incompatible to point {self}")

    def __eq__(self, P):
        if isinstance(P, Point):
            return self.x == P.x and self.y == P.y
        else:
            raise TypeError(f"{type(P)} object {P} is incompatible to point {self}")

    @property
    def ridge(self):
        # Find the active ridge whose last point is x-maximal (most recently extended)
        active = [r for r in self.net.values() if r.active]
        if not active:
            raise AssertionError("No active ridge connected to point.")
        return max(active, key=lambda r: r[-1].x)

    '''
    @property
    def ridge(self):
        last=next(reversed(self.net.values()))
        if last.active: return last
        else: raise AssertionError("Last connected ridge is inactive.")
    '''

    @property
    def junc(self):
        return len(self.net)



class Ridge:

    def __init__(self, P=None):
        if P:
            if isinstance(P, Ridge):
                self.pts = P.pts
                for i in P: i.net[id(self)] = self
            elif hasattr(P, '__iter__'):
                self.pts = P
                for i in P: i.net[id(self)] = self
            elif isinstance(P, Point):
                self.pts = [P]
                P.net[id(self)] = self
            else:
                raise TypeError(f"Cannot pass {type(P)} object {P} to Ridge")
        else:
            self.pts = []
        self.active = True

    def __iadd__(self, P, force=False, closeOK=True):
        if self.active or force:
            if isinstance(P, Ridge):
                self.pts += P.pts
                for i in P: i.net[id(self)] = self
            elif isinstance(P, Point):
                self.pts += [P]
                P.net[id(self)] = self
            else:
                raise TypeError(f"{type(P)} object {P} is incompatible to ridge {self}")
        elif not closeOK:
            raise ConnectionRefusedError(f"Cannot join {P} to closed Ridge {self}")
        self.pts = sorted(self.pts)
        return self

    def __add__(self, P, force=False, closeOK=True):
        R = deepcopy(self)
        R.__iadd__(P, force, closeOK)
        return R

    def __getitem__(self, i):
        self.pts = sorted(self.pts)
        return self.pts[i]

    def __call__(self):
        x = np.array([i.x for i in self.pts])
        y = np.array([i.y for i in self.pts])
        return x, y

    def _on_pick(self, event):
        # Ignore clicks on artists that don't belong to this ridge
        if event.artist not in (self._scatter_mid, self._scatter_ends, self._line):
            return

        self._selected = not self._selected
        col = 'red' if self._selected else self.col  # swap to highlight colour

        self._scatter_mid.set_color(col)
        self._scatter_ends.set_color(col)
        self._line.set_color(col)
        event.artist.figure.canvas.draw_idle()  # redraw without blocking

        if self._on_select:
            self._on_select(self)

    def plot(self, ax, on_select=None):
        x, y = self()
        self._selected = False
        self.col=np.random.rand(3)
        self._base_col = self.col  # <-- store base color for reset after unpickle
        self._on_select = None  # don't store the callback (not picklable)

        self._scatter_mid = ax.scatter(x[1:-1], y[1:-1], s=10,
                                       color=self.col, zorder=3, picker=True)
        self._scatter_ends = ax.scatter([x[0], x[-1]], [y[0], y[-1]],
                                        color=self.col, zorder=3, picker=True)
        self._line, = ax.plot(x, y, color=self.col, zorder=2, pickradius=5)

        # Tag each artist with a back-reference to this ridge
        for artist in (self._scatter_mid, self._scatter_ends, self._line):
            artist._ridge = self

        # Connect only if we have a real canvas (not inside a to-be-pickled fig)
        ax.figure.canvas.mpl_connect('pick_event', self._on_pick)

    '''    
    def plot(self, plt=plt):
        x, y = self()
        col = np.random.rand(3)
        plt.scatter(x[1:-1], y[1:-1], s=10, color=col, zorder=3)
        plt.scatter([x[0], x[-1]], [y[0], y[-1]], color=col, zorder=3)
        plt.plot(x, y, color=col, zorder=2)'''

    def __contains__(self, P):
        return any(i == P for i in self)

    def __repr__(self):
        return str(self.pts)

    def close(self):
        self.active = False

    def __iter__(self):
        for i in sorted(self.pts): yield i

    def __len__(self):
        return len(self.pts)

    def slice(self, i, close=True, delete=True):
        if i < 0:
            i = len(self.pts) + i
        if i < len(self.pts):
            R1, R2 = Ridge(self.pts[:i + 1]), Ridge(self.pts[i:])
            if close: R1.close()
            if delete: self.delete()
            return R1, R2
        else:
            raise IndexError(f"{i} is out of range for {len(self)} sized Ridge {self}")

    def __eq__(self, R):
        if isinstance(R,Ridge):
            if len(self) != len(R): return False
            return all(R[i] == self[i] for i in range(len(self)))
        else: raise TypeError(f"{type(R)} object {R} is incompatible to ridge {self}")

    def delete(self):
        for i in self.pts: i.net.pop(id(self))
        self.pts = None
        self.close()

    @property
    def alive(self):
        return True if self.pts else False

    def __hash__(self):
        return id(self)



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
            yield x,P

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

    def plot(self, plt=plt, show=True):

        Per, Vitg = np.meshgrid(self.x, self.y)
        heatmap = plt.contourf(Per, Vitg, self.map.T, 35, cmap=inferno)

        if isinstance(plt, MT):
            fig, plt = plt.gcf(), plt.gca()
        else:
            fig = plt.get_figure()

        if self.Rs:
            for R in self.Rs:
                R.plot(plt,on_select=partial(print,R))

        fig.colorbar(heatmap, label="Signal Strength")
        plt.set_xlabel("Time Period (s)")
        plt.set_ylabel("Group Velocity (km/s)")
        plt.set_title("2D Heatmap")

        if show:
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
        heatmap = plt.pcolormesh(
            self.x, self.y, self.map.T, shading="auto", cmap="inferno"
            )
        '''