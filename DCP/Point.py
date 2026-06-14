from functools import total_ordering
from types import ModuleType as MT

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import RectangleSelector


def search(arr, n):
    arr = np.asarray(arr)
    idx = np.searchsorted(arr, n)
    if idx == 0:
        return 0
    if idx == len(arr):
        return len(arr) - 1
    if abs(arr[idx] - n) < abs(arr[idx - 1] - n):
        return idx
    return idx - 1


@total_ordering
class Point:
    def __init__(self, x, y):
        self.__x = x
        self.__y = y
        self._deselect()

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

    def _select(self):
        self.__selected = True
        self._col = "red"

    def _deselect(self):
        self.__selected = False
        self._col = "green"

    @property
    def selected(self):
        return self.__selected

    def __click(self, event):
        if event.artist not in (self.__plot):
            return

        if self.selected:
            self._deselect()
        else:
            self._select()

        self.__plot.set_color(self._col)

        event.artist.figure.canvas.draw_idle()

    def _refresh(self):
        self.__plot.set_color(self._col)

    def plot(self, ax=plt):
        if isinstance(ax, MT):
            ax = ax.gca()

        self.__plot = ax.scatter(self.x, self.y, c=self._col, zorder=3, picker=True)

        ax.figure.canvas.mpl_connect('pick_event', self.__click)

    @staticmethod
    def ridge(icol, xs, iP):
        pts = []
        for x in xs:
            if len(icol[x]) > 0:
                Px = icol[x]
                y = [i.y for i in Px]
                id = search(y, iP.y)
                if y[id] < iP.y and id < len(icol[x]) - 1:
                    if y[id + 1] - iP.y < 2 * (iP.y - y[id]): id += 1
                Px[id]._select()
                iP = Px[id]
                pts.append(iP)

        return Ridge(pts)


class Ridge:
    slc, sgt = None, None
    update = False

    def __init__(self, points: list[Point]):
        self.pts = points

    def __iter__(self):
        for i in self.pts: yield i

    def plot(self, ax=plt, dynamic=False):
        if isinstance(ax, MT):
            ax = ax.gca()
        if dynamic:
            x = [i.x for i in self.pts]
            y = [i.y for i in self.pts]
            if Ridge.slc: Ridge.slc.remove()
            Ridge.slc, = ax.plot(x, y, c="red", zorder=3)
        else:
            x = [i.x for i in self.pts]
            y = [i.y for i in self.pts]
            Ridge.sgt, = ax.plot(x, y, c="red", zorder=2)

    @staticmethod
    def refresh(pts):
        if not Ridge.update:
            Ridge.update = True
            Ridge.sgt.set_color("green")
            # Ridge.sgt.figure.canvas.draw_idle()
        icol = {}
        for P in pts.selected:
            if P.x in icol:
                icol[P.x].append(P)
            else:
                icol[P.x] = [P]

        Point.ridge(icol, list(sorted(icol.keys())), Point(0, 2)).plot(plt, True)


class Interact:

    def __init__(self, points: list[Point], ax=plt):
        if isinstance(ax, MT):
            ax = ax.gca()
        self._ax = ax
        self._points = points

        for p in self._points:
            p.plot(ax)

        self._rs = RectangleSelector(
            ax,
            self._on_select,
            useblit=True,
            button=[1],
            minspanx=5, minspany=5,
            spancoords='pixels',
            interactive=False,
        )
        ax.figure.canvas.mpl_connect('button_release_event', self._on_click_empty)

    def _on_select(self, eclick, erelease):
        x0, x1 = sorted([eclick.xdata, erelease.xdata])
        y0, y1 = sorted([eclick.ydata, erelease.ydata])

        shift = eclick.key in ('shift', 'shift+')

        for p in self._points:
            inside = x0 <= p.x <= x1 and y0 <= p.y <= y1
            if inside:
                p._select()
            elif not shift:
                p._deselect()
            p._refresh()
        Ridge.refresh(self)

        self._ax.figure.canvas.draw_idle()

    def _on_click_empty(self, event):
        if event.inaxes != self._ax:
            return
        try:
            x0, x1, y0, y1 = self._rs.extents
            span = abs(x1 - x0) + abs(y1 - y0)
        except Exception:
            span = 0

        if span < 1e-10:
            for p in self._points:
                p._deselect()
                p._refresh()
            Ridge.refresh(self)

            self._ax.figure.canvas.draw_idle()

    @property
    def selected(self) -> list[Point]:
        return [p for p in self._points if p.selected]
