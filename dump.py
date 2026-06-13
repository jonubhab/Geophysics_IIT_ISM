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

'''def scan(self, tol=0):
    if tol == 0:
        tol = self.slopetol

    peaks = [self.maxima(i) for i in self.x]
    Rs = []

    for i in tqdm(range(len(self.x))):
        x = self.x[i]
        ys = peaks[i]
        Px = [Point(x, p) for p in ys]

        for P in Px:
            ctr = 0

            to_remove, to_add = [], []
            for R in Rs:
                if R[-1] == P and len(R) > 2 and -tol < R[-2].slope(P) < tol:
                    to_remove.append(R)
                    R1, R2 = R.slice(-2)
                    to_add += [R1, R2, Ridge([R1[-1], P])]
                    ctr += 1
            for e in to_remove:
                Rs.remove(e)
            Rs += to_add

            to_remove2, to_add2 = [], []
            for R in Rs:
                if R.active and P > R[-1] and -tol < R[-1].slope(P) < tol:
                    if ctr > 1:
                        for A in to_add2:
                            if A[-1].eq(P):
                                A.close()
                        to_add2.append(R + P)
                        to_add2[-1].close()
                        to_add2.append(Ridge(P))
                    else:
                        to_remove2.append(R)
                        to_add2.append(R + P)
                    ctr += 1
            for e in to_remove2:
                Rs.remove(e)
            Rs += to_add2

            if ctr == 0:
                Rs.append(Ridge(P))

    self.Rs = Rs
    return Rs'''

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
'''

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
