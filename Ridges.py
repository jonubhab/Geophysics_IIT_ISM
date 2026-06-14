from Point import *



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
        self._line, = ax.plot(x, y)

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



