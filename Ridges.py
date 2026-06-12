import pickle
import subprocess
import sys
from copy import deepcopy
from functools import total_ordering
from types import ModuleType as MT

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import inferno

'''
class Ridge:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.node=None

    def copy(self):
        return Ridge(self.x, self.y)

    def __iadd__(self, P):
        if self.node:
            self.node += P
        else:
            if type(P) is Ridge:
                self.node = P
            else:
                self.node = Ridge(*P)
        return self

    def __add__(self, P):
        R = self.copy()
        R += P
        return R

    def end(self):
        if self.node:
            return self.node.end()
        else:
            return (self.x, self.y)

    def __call__(self):
        if self.node:
            x, y = self.node()
            x = np.append(np.array([self.x]), x)
            y = np.append(np.array([self.y]), y)
            return x, y
        return np.array([self.x]), np.array([self.y])

    def plot(self,plt=plt):

        x, y = self()

        plt.plot(x, y)
        plt.scatter(x, y)


    def dist(self,R):
        X,Y=self.end()
        return np.sqrt((X-R.x)**2+(Y-R.y)**2)


    def __in__(self,P):
        if P.x==self.x and P.y==self.y: return True
        elif self.node: return P in self.node
        return False
'''


@total_ordering
class Point:
    def __init__(self, x, y):
        self.__x = x
        self.__y = y

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

    def __eq__(self, P):
        if isinstance(P, Point):
            return self.x == P.x
        else:
            raise TypeError(f"{type(P)} object {P} is incompatible to point {self}")

    def __gt__(self, P):
        if isinstance(P, Point):
            return self.x > P.x
        else:
            raise TypeError(f"{type(P)} object {P} is incompatible to point {self}")

    def eq(self, P):
        if isinstance(P, Point):
            return self.x == P.x and self.y == P.y
        else:
            raise TypeError(f"{type(P)} object {P} is incompatible to point {self}")


class Ridge:

    def __init__(self, P=None):
        if P:
            if isinstance(P, Ridge):
                self.pts = P.pts
            elif hasattr(P, '__iter__'):
                self.pts = P
            elif isinstance(P, Point):
                self.pts = [P]
            else:
                raise TypeError(f"Cannot pass {type(P)} object {P} to Ridge")
        else:
            self.pts = []
        self.active = True

    def __iadd__(self, P, force=False, closeOK=True):
        if self.active or force:
            if isinstance(P, Ridge):
                self.pts += P.pts
            elif isinstance(P, Point):
                self.pts += [P]
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

    def plot(self, plt=plt):
        x, y = self()
        col = np.random.rand(3)
        plt.scatter(x[1:-1], y[1:-1], s=10, color=col, zorder=3)
        plt.scatter([x[0], x[-1]], [y[0], y[-1]], color=col, zorder=3)
        plt.plot(x, y, color=col, zorder=2)

    def __contains__(self, P):
        return any(i.eq(P) for i in self)

    def __repr__(self):
        return str(self.pts)

    def close(self):
        self.active = False

    def __iter__(self):
        for i in sorted(self.pts): yield i

    def __len__(self):
        return len(self.pts)

    def slice(self, i, close=True):
        if i < 0:
            i = len(self.pts) + i
        if i < len(self.pts):
            R1, R2 = Ridge(self.pts[:i + 1]), Ridge(self.pts[i:])
            if close: R1.close()
            return R1, R2
        else:
            raise IndexError(f"{i} is out of range for {len(self)} sized Ridge {self}")

    def __eq__(self, R):
        return all(R[i].eq(self[i]) for i in range(len(self)))



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
        arr = abs(arr - n)
        return np.argmin(arr)

    def __getitem__(self, k):
        if isinstance(k, Point): return self.map[Map.__search(self.x, k.x)][Map.__search(self.y, k.y)]

        if isinstance(k, slice):
            if np.ndim(self.map) != 1:
                result = []
                for i in np.arange(k.start, k.stop, k.step):
                    result.append(self.map[Map.__search(self.x, i)])
                return Map(np.array(result), np.arange(k.start, k.stop, k.step), self.y)
            else:
                result = []
                for i in np.arange(k.start, k.stop, k.step):
                    result.append(self.map[Map.__search(self.x, i)])
                return np.array(result)

        if np.ndim(self.map) != 1:
            return Map(self.map[Map.__search(self.x, k)], np.array([k]), self.y)
        else:
            return self.map[Map.__search(self.y, k)]

    # def __index__(self,k):

    def setTol(self, GVtol, slopetol):
        self.GVtol = GVtol
        self.slopetol = slopetol

    def __iter__(self):
        for i in self.map: yield i

    '''
    def maxima(self, x, tol=0):
        if tol == 0:
            tol = self.GVtol


        amp=self[x]
        peaks=set()

        for i in self.y:
            if amp[i]==max(amp[i-tol:i + tol]): peaks.add(i)

        return np.array(list(peaks))
        '''

    def maxima(self, x, tol=0):
        if tol == 0:
            tol = self.GVtol

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

        return np.array(list(peaks))

    '''
    def scan(self,tol=0,plt=plt):
        if tol==0: tol=self.disttol

        peaks=np.array([self.maxima(i) for i in self.x])
        Rs=[]
        for i in range(len(self.x)):
            Rx=[Ridge(self.x[i],peaks[j]) for j in range(len(peaks))]
            for R in Rs:
                for P in Rx:
                    if R.dist(P)<=tol:
                        R+=P
            Rx = [P for P in Rx if not any(P in R for R in Rs)]
            Rs+=Rx

        for R in Rs: R.plot(plt)


        heatmap = plt.pcolormesh(self.x, self.y, self.map.T, shading="auto", cmap="inferno")
        plt.colorbar(heatmap, label="Signal Strength")
        plt.xlabel("Time Period (s0)")
        plt.ylabel("Group Velocity (km/s)")
        plt.title("2D Heatmap")

        return Rs
    '''

    def scan(self, tol=0):
        if tol == 0:
            tol = self.slopetol

        peaks = [self.maxima(i) for i in self.x]
        Rs = []

        for i in range(len(self.x)):
            x = self.x[i]
            ys = peaks[i]

            Px = [Point(x, p) for p in ys]

            ex, ap = [], []
            for P in Px:
                ctr = 0
                ex, ap = [], []
                for R in Rs:
                    if R[-1] == P and len(R) > 2 and 0 <= R[-2].slope(P) < tol:
                        ex += [R]
                        R1, R2 = R.slice(-2)
                        ap += [R1, R2, Ridge([R1[-1], P])]
                        ctr += 1
                for e in ex: Rs.remove(e)
                Rs += ap

                ex, ap = [], []
                for R in Rs:
                    if P > R[-1] and 0 <= R[-1].slope(P) < tol:
                        if ctr > 1:
                            for A in ap:
                                if A[-1].eq(P): A.close()
                            ap += [R + P]
                            ap[-1].close()
                            ap += [Ridge(P)]
                        else:
                            ex += [R]
                            ap += [R + P]
                        ctr += 1
                for e in ex: Rs.remove(e)
                Rs += ap

                if ctr == 0: Rs += [Ridge(P)]

        self.Rs = Rs

        return Rs

    def plot(self, plt=plt, show=True):

        if self.Rs:
            for R in self.Rs:
                R.plot(plt)

        Per, Vitg = np.meshgrid(self.x, self.y)
        heatmap = plt.contourf(Per, Vitg, self.map.T, 35, cmap=inferno)

        if isinstance(plt, MT):
            fig, plt = plt.gcf(), plt.gca()
        else:
            fig = plt.get_figure()

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
fig=pickle.load(open("tmp67as1305kdgf.pkl", "rb"))
os.remove("tmp67as1305kdgf.pkl")
#mgr = plt.new_figure_manager(1)
#mgr.canvas.figure = fig
#fig.set_canvas(mgr.canvas)
#fig.canvas.draw()
plt.show()
"""
            subprocess.Popen([sys.executable, "-c", script])

        '''
        heatmap = plt.pcolormesh(
            self.x, self.y, self.map.T, shading="auto", cmap="inferno"
            )
        '''
