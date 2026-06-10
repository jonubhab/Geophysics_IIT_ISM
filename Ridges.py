import numpy as np
import matplotlib.pyplot as plt


class Ridge:
    def __init__(self, x, y):
        self.x = x
        self.y = y

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



class Map:
    def __init__(self, map, x, y):
        self.map = map
        self.x = x
        self.y = y


    @staticmethod
    def __search(arr, n):
        arr = abs(arr - n)
        return np.argmin(arr)


    def __getitem__(self, k):
        if len(self.x) == 1:
            return Map(self.map[Map.__search(self.x, k)], np.array([k]), self.y)
        else:
            return self.map[Map.__search(self.y, k)]


    def setTol(self, GVtol,disttol):
        self.GVtol = GVtol
        self.disttol=disttol


    def __iter__(self):
        for i in self.map: yield i


    def maxima(self, x, tol=0):
        if tol == 0:
            tol = self.GVtol

        amp=self[x]
        peaks=set()

        for i in self.y:
            if amp[i]==max(amp[i-tol:i + tol]): peaks.add(i)

        return np.array(list(peaks))


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
            for i in range(len(Rx)):
                for R in Rs:
                    if Rx[i] in R: Rx=Rx[:i]+(Rx[i+1:] if i<len(Rx)-1 else [])
            Rs+=Rx

        for R in Rs: R.plot()

        x=np.array([[self.x[i] for j in range(len(peaks[i]))] for i in range(len(self.x))]).flatten()
        y=peaks.flatten()

        plt.scatter(x,y)

        heatmap = plt.pcolormesh(x, y, self.map, shading="auto", cmap="inferno")
        plt.colorbar(heatmap, label="Signal Strength")
        plt.xlabel("Time Period (s0)")
        plt.ylabel("Group Velocity (km/s)")
        plt.title("2D Heatmap")

        return Rs



