import pickle
import subprocess
import sys
from copy import deepcopy
from functools import total_ordering
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
        if isinstance(R,Ridge):
            if len(self) != len(R): return False
            return all(R[i].eq(self[i]) for i in range(len(self)))
        else: raise TypeError(f"{type(R)} object {R} is incompatible to ridge {self}")



class Tracker:
    def __init__(self):
        self.Rs=[]
        self.on: dict[int, Ridge] = {}

    def __iadd__(self,R:Ridge):
        self.Rs.append(R)
        if R.active:
            self.on[id(R)] = R
        return self

    def off(self,R: Ridge):
        self.on.pop(id(R), None)

    def close(self,R: Ridge):
        R.close()
        self.off(R)

    def extend(self,R: Ridge,P: Point) -> Ridge:
        self.off(R)
        R2 = R + P
        self.Rs.append(R2)
        self.on[id(R2)] = R2
        return R2

    def __call__(self):
        return self.Rs

    def active(self):
        return self.on.values()



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

    @staticmethod
    def _segments_intersect(p1, p2, p3, p4):
        """
        Check if segment p1->p2 intersects segment p3->p4.
        Returns (True, intersection_x, intersection_y) or (False, None, None).
        Uses parametric form.
        """
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y
        x4, y4 = p4.x, p4.y

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-12:
            return False, None, None  # parallel

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)
            return True, ix, iy
        return False, None, None

    def scan(self, tol=0, max_gap=3, min_len=1, amp_weight=0):
        if tol == 0:
            tol = self.slopetol

        peaks = [self.maxima(x) for x in self.x]

        active = []  # list of dicts: {pts, gap}
        closed = []  # list of list-of-Point

        def _amp(P):
            xi = Map._Map__search(self.x, P.x)
            yi = Map._Map__search(self.y, P.y)
            return float(self.map[xi][yi])

        def _score(R_dict, P):
            last = R_dict['pts'][-1]
            s = abs(last.slope(P)) / tol
            a = 1.0 - _amp(P)
            return (1.0 - amp_weight) * s + amp_weight * a


        def _check_and_split_intersections(new_pt, new_prev_pt):
            """
            For the segment new_prev_pt -> new_pt, check against all segments
            in all active+closed ridges. If an intersection is found, split the
            crossed ridge at the nearest point to the intersection and return
            the intersection Point so the caller can terminate its own ridge there.

            Returns a Point at the intersection (snapped to grid) if a crossing
            was found, else None.
            """
            best_t = float('inf')
            best_hit = None
            best_rid = None
            best_seg = None  # (seg_idx) index of point AFTER the intersected segment start

            all_ridges = active + [{'pts': pts, 'gap': 0} for pts in closed]

            for r_idx, R in enumerate(all_ridges):
                pts = R['pts']
                for k in range(len(pts) - 1):
                    p3, p4 = pts[k], pts[k + 1]
                    # only check segments that straddle our x range
                    if p4.x <= new_prev_pt.x or p3.x >= new_pt.x:
                        continue
                    hit, ix, iy = Map._segments_intersect(new_prev_pt, new_pt, p3, p4)
                    if hit:
                        # parametric t along new segment
                        dx = new_pt.x - new_prev_pt.x
                        t = (ix - new_prev_pt.x) / dx if abs(dx) > 1e-12 else 0
                        if t < best_t:
                            best_t = t
                            best_hit = (ix, iy)
                            best_rid = r_idx
                            best_seg = k + 1  # index of p4

            if best_hit is None:
                return None

            ix, iy = best_hit
            # snap intersection to nearest grid point
            xi = int(np.argmin(np.abs(self.x - ix)))
            yi = int(np.argmin(np.abs(self.y - iy)))
            P_int = Point(self.x[xi], self.y[yi])

            # split the crossed ridge at best_seg
            r_idx = best_rid
            if r_idx < len(active):
                R = active[r_idx]
                left = R['pts'][:best_seg]
                right = R['pts'][best_seg - 1:]  # share the boundary point
                closed.append(left)
                active[r_idx] = {'pts': right, 'gap': R['gap']}
            else:
                c_idx = r_idx - len(active)
                left = closed[c_idx][:best_seg]
                right = closed[c_idx][best_seg - 1:]
                closed[c_idx] = left
                closed.append(right)

            return P_int

        for i in tqdm(range(len(self.x))):
            x = self.x[i]
            Px = [Point(x, p) for p in peaks[i]]

            claimed = set()
            Px_sorted = sorted(Px, key=lambda P: -_amp(P))
            assignments = {}

            for P in Px_sorted:
                best_idx = None
                best_score = float('inf')
                for j, R in enumerate(active):
                    if j in claimed:
                        continue
                    last = R['pts'][-1]
                    if last.x >= x:
                        continue
                    sl = last.slope(P)
                    if not (-tol < sl < tol):
                        continue
                    sc = _score(R, P)
                    if sc < best_score:
                        best_score = sc
                        best_idx = j
                if best_idx is not None:
                    assignments[id(P)] = best_idx
                    claimed.add(best_idx)

            new_active = []
            for j, R in enumerate(active):
                if j in claimed:
                    for P in Px_sorted:
                        if assignments.get(id(P)) == j:
                            prev = R['pts'][-1]

                            # --- intersection check ---
                            P_int = _check_and_split_intersections(P, prev)
                            if P_int is not None:
                                # close this ridge at the intersection point
                                R['pts'].append(P_int)
                                closed.append(R['pts'])
                                # start a fresh branch from the intersection
                                new_active.append({'pts': [P_int, P], 'gap': 0})
                            else:
                                R['pts'].append(P)
                                R['gap'] = 0
                                new_active.append(R)
                            break
                else:
                    R['gap'] += 1
                    if R['gap'] <= max_gap:
                        new_active.append(R)
                    else:
                        closed.append(R['pts'])

            active = new_active

            assigned_pids = set(assignments.keys())
            for P in Px:
                if id(P) not in assigned_pids:
                    active.append({'pts': [P], 'gap': 0})

        for R in active:
            closed.append(R['pts'])

        # build Ridge objects, drop short stubs
        self.Rs = []
        for pts in closed:
            if len(pts) >= min_len:
                R = Ridge(pts[0])
                for P in pts[1:]:
                    R.pts.append(P)
                R.close()
                self.Rs.append(R)

        return self.Rs

    '''
    def scan(self, tol=0, max_gap=3, min_len=1, amp_weight=0):
        """
        tol        : slope tolerance (km/s per s)
        max_gap    : how many consecutive columns a ridge may skip before dying
        min_len    : discard ridges shorter than this many points
        amp_weight : 0=pick by slope only, 1=pick by amplitude only (blended score)
        """
        if tol == 0:
            tol = self.slopetol

        peaks = [self.maxima(x) for x in self.x]

        # --- internal ridge state -------------------------------------------
        # Each active ridge is stored as a dict so we avoid deepcopy overhead:
        #   pts   : list of Point
        #   gap   : consecutive columns missed
        active = []  # list of dicts
        closed = []  # list of list-of-Point (only pts kept, Ridge built at end)

        def _score(ridge_dict, P):
            """Lower is better. Blend normalised |slope| and (1-normalised amp)."""
            last = ridge_dict['pts'][-1]
            s = abs(last.slope(P)) / tol  # 0..1 within tolerance
            a = 1.0 - float(self[P])  # lower amp → higher cost
            # self[P] needs a 1-D lookup; guard below
            return (1.0 - amp_weight) * s + amp_weight * a

        for i in tqdm(range(len(self.x))):
            x = self.x[i]
            Px = [Point(x, p) for p in peaks[i]]

            # which active ridges got claimed this column?
            claimed = set()  # indices into `active`

            # greedy assignment: for each new point, find best ridge
            # sort Px by amplitude descending so bright peaks get first pick
            Px_sorted = sorted(Px, key=lambda P: -float(self[P]))

            assignments = {}  # point -> ridge index

            for P in Px_sorted:
                best_idx = None
                best_score = float('inf')
                for j, R in enumerate(active):
                    if j in claimed:
                        continue
                    last = R['pts'][-1]
                    if last.x >= x:  # already on this column
                        continue
                    sl = last.slope(P)
                    if not (-tol < sl < tol):
                        continue
                    sc = _score(R, P)
                    if sc < best_score:
                        best_score = sc
                        best_idx = j

                if best_idx is not None:
                    assignments[id(P)] = best_idx
                    claimed.add(best_idx)

            # apply assignments
            new_active = []
            for j, R in enumerate(active):
                if j in claimed:
                    # find which P was assigned
                    for P in Px_sorted:
                        if assignments.get(id(P)) == j:
                            R['pts'].append(P)
                            R['gap'] = 0
                            break
                    new_active.append(R)
                else:
                    R['gap'] += 1
                    if R['gap'] <= max_gap:
                        new_active.append(R)  # keep alive through the gap
                    else:
                        closed.append(R['pts'])

            active = new_active

            # start new ridges for unclaimed points
            assigned_pids = set(assignments.keys())
            for P in Px:
                if id(P) not in assigned_pids:
                    active.append({'pts': [P], 'gap': 0})

        # drain remaining active ridges
        for R in active:
            closed.append(R['pts'])

        # build Ridge objects, filter short ones
        self.Rs = []
        for pts in closed:
            if len(pts) >= min_len:
                R = Ridge(pts[0])
                for P in pts[1:]:
                    R.pts.append(P)  # direct append avoids deepcopy in __add__
                R.close()
                self.Rs.append(R)

        return self.Rs

    
    def scan(self, tol=0):
        if tol == 0:
            tol = self.slopetol

        peaks = [self.maxima(x) for x in self.x]

        T=Tracker()

        for i in tqdm(range(len(self.x))):
            x = self.x[i]
            Px = [Point(x, p) for p in peaks[i]]

            for P in Px:

                candidates = [
                    R for R in T.active()
                    if -tol < R[-1].slope(P) < tol
                ]

                if not candidates:
                    T+=Ridge(P)
                    continue

                if len(candidates) == 1:
                    T.extend(candidates[0], P)
                    continue

                candidates.sort(key=lambda R: abs(R[-1].slope(P)))
                best = candidates[0]

                for R in candidates[1:]:
                    T.close(R)

                T.extend(best, P)

        self.Rs = T()
        return self.Rs
    '''
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
