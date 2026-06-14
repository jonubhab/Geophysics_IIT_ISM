from functools import total_ordering


@total_ordering
class Point:
    def __init__(self, x, y):
        self.__x = x
        self.__y = y
        self.net = {}

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

    @property
    def ridge(self):
        # Find the active ridge whose last point is x-maximal (most recently extended)
        active = [r for r in self.net.values() if r.active]
        if not active:
            raise AssertionError("No active ridge connected to point.")
        return max(active, key=lambda r: r[-1].x)

    '''
    @property
    def ridge(self):
        last=next(reversed(self.net.values()))
        if last.active: return last
        else: raise AssertionError("Last connected ridge is inactive.")
    '''

    @property
    def junc(self):
        return len(self.net)
