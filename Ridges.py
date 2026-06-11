import matplotlib.pyplot as plt
import numpy as np

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


class Ridge:

    def __init__(self, x, y):
        # If x and y are arrays or lists, store them directly.
        # Otherwise, wrap individual floats into a coordinate list.
        self.x = np.atleast_1d(x).tolist()
        self.y = np.atleast_1d(y).tolist()

    def copy(self):
        return Ridge(self.x.copy(), self.y.copy())

    def __iadd__(self, P):
        if isinstance(P, Ridge):
            self.x.extend(P.x)
            self.y.extend(P.y)
        elif isinstance(P, (tuple, list, np.ndarray)) and len(P) == 2:
            self.x.append(P[0])
            self.y.append(P[1])
        return self

    def __add__(self, P):
        R = self.copy()
        R += P
        return R

    def end(self):
        return (self.x[-1], self.y[-1])

    def __call__(self):
        return np.array(self.x), np.array(self.y)

    def plot(self, plt=plt):
        x, y = self()
        plt.plot(x, y)
        plt.scatter(x, y)

    def slope(self, R):
        X, Y = self.end()
        try:
            return (Y - R.y[0]) / (X - R.x[0]) * np.sign(R.y[0] - Y)
        except ZeroDivisionError:
            return -1

    def __contains__(self, P):
        return any(px == P.x[0] and py == P.y[0] for px, py in zip(self.x, self.y))

    def __repr__(self):
        return str(list(zip(self.x, self.y)))



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

    @staticmethod
    def __search(arr, n):
        arr = abs(arr - n)
        return np.argmin(arr)


    def __getitem__(self, k):
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

    def setTol(self, GVtol,disttol):
        self.GVtol = GVtol
        self.disttol=disttol


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
        # Extract the raw 1D NumPy array of amplitudes directly
        amp_data = amp_obj.map
        peaks = set()

        # Convert your float coordinate 'tol' into an integer number of array index steps
        # e.g., if total Y range is 1794 steps over ~3.8 km/s, calculate indices per unit
        y_spacing = self.y[1] - self.y[0] if len(self.y) > 1 else 1
        idx_tol = int(tol / y_spacing) if tol > 0 else 5  # Default to 5 indices if tol is 0

        # Loop using clean integer indices across the 1794 elements
        for idx in range(len(self.y)):
            # Define local window boundaries safely within array limits
            start_bound = max(0, idx - idx_tol)
            end_bound = min(len(self.y), idx + idx_tol + 1)

            # Check if the current point is strictly the local maximum in its neighborhood window
            if amp_data[idx] == max(amp_data[start_bound:end_bound]):
                # Map the successful integer index back to its real Y float coordinate
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

    def scan(self, tol=0, plt=plt):
        if tol == 0:
            tol = self.disttol

        # 1. Get the list of peak velocity arrays per x coordinate
        raw_peaks = [self.maxima(i) for i in self.x]
        Rs = []

        # 2. Correctly build the initial Ridge objects step-by-step
        for i in range(len(self.x)):
            current_x = self.x[i]
            current_y_peaks = raw_peaks[i]

            # Generate individual Ridge elements for EVERY peak found at this X coordinate
            Rx = [Ridge(current_x, p) for p in current_y_peaks]

            # Link them up to existing tracks in Rs
            for R in Rs:
                for P in Rx:
                    if 0 <= R.slope(P) <= tol:
                        R += P

            # Filter out points that have successfully been integrated into existing chains
            Rx = [P for P in Rx if not any(P in R for R in Rs)]
            Rs += Rx

        # --- PLOTTING CODE ---
        # 3. Draw the tracks over the heatmap canvas
        for R in Rs:
            R.plot(plt)

        # Draw the background heatmap matrix
        heatmap = plt.pcolormesh(
            self.x, self.y, self.map.T, shading="auto", cmap="inferno"
        )
        plt.colorbar(heatmap, label="Signal Strength")
        plt.xlabel("Time Period (s0)")
        plt.ylabel("Group Velocity (m/s)")
        plt.title("2D Heatmap")

        return Rs


