import numpy as np


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
        if np.ndim(self.x) == 1:
            return Map(self.map[Map.__search(self.x, k)], k, self.y)
        else:
            return self.map[Map.__search(self.y, k)]

    def setGVTol(self, tol):
        self.tol = tol

    def maxima(self, x, tol=0):
        if tol == 0:
            tol = self.tol
