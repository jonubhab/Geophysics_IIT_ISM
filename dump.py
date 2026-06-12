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