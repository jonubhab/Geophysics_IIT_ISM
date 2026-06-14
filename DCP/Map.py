from matplotlib.cm import inferno

from Point import *


class Map:
    def __init__(self, map, x, y):
        self.map = map
        self.x = x
        self.y = y

    def __repr__(self):
        return f"""
        Map Size: {len(self.x)}x{len(self.y)}
        X-Range: {self.x[0]} - {self.x[-1]}
        Y-Range: {self.y[0]} - {self.y[-1]}
        """

    def __getitem__(self, k):
        if isinstance(k, Point): return self.map[search(self.x, k.x)][search(self.y, k.y)]

        if isinstance(k, slice):
            if np.ndim(self.map) != 1:
                if k.step:
                    result = []
                    for i in np.arange(k.start, k.stop, k.step):
                        result.append(self.map[search(self.x, i)])
                    return Map(np.array(result), np.arange(k.start, k.stop, k.step), self.y)
                else:
                    i = search(self.x, k.start)
                    f = search(self.x, k.stop) + 1
                    return Map(self.map[i:f], self.x[i:f], self.y)
            else:
                if k.step:
                    result = []
                    for i in np.arange(k.start, k.stop, k.step):
                        result.append(self.map[search(self.x, i)])
                    return np.array(result)
                else:
                    i = search(self.y, k.start)
                    f = search(self.y, k.stop) + 1
                    return Map(self.map[i:f], self.x, self.y[i:f])

        if np.ndim(self.map) != 1:
            return Map(self.map[search(self.x, k)], np.array([k]), self.y)
        else:
            return self.map[search(self.y, k)]

    def setTol(self, Ytol):
        self.Ytol = Ytol

    def __iter__(self):
        for i in self.map: yield i

    def maxima(self, x, tol=0):
        if tol == 0:
            tol = self.Ytol

        amp_obj = self[x]
        amp_data = amp_obj.map

        y_spacing = self.y[1] - self.y[0] if len(self.y) > 1 else 1
        idx_tol = max(1, int(tol / y_spacing))

        peaks = set()
        for idx in range(len(self.y)):
            start_bound = max(0, idx - idx_tol)
            end_bound = min(len(self.y), idx + idx_tol + 1)
            if amp_data[idx] == max(amp_data[start_bound:end_bound]):
                peaks.add(self.y[idx])

        return np.array(sorted(peaks))

    def scan(self):
        for x in self.x:
            y = self.maxima(x)
            P = [Point(x, i) for i in y]
            yield x, P

    def plot(self, ax=plt, show=True):

        Per, Vitg = np.meshgrid(self.x, self.y)
        heatmap = ax.contourf(Per, Vitg, self.map.T, 35, cmap=inferno)

        if isinstance(ax, MT):
            fig, ax = ax.gcf(), ax.gca()
        else:
            fig = ax.get_figure()

        ax.set_xlim(Per.min(), Per.max())
        ax.set_ylim(Vitg.min(), Vitg.max())

        col = []
        icol = {}
        for x, P in self.scan():
            icol[x] = P
            col += P

        Point.ridge(icol, self.x, Point(0, 2)).plot(ax)
        pts = Interact(col, ax)

        fig.colorbar(heatmap, label="Signal Strength")
        ax.set_xlabel("Time Period (s)")
        ax.set_ylabel("Group Velocity (km/s)")
        ax.set_title("2D Heatmap")

        plt.tight_layout()

        if show:
            plt.show()

        return pts
