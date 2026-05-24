import numpy as np
from forbiddenfruit import curse

class Meta(type):
    @property
    def i(cls):
        return cls(0,1)

class Complex(metaclass=Meta):


    def __init__(s,x=0,y=0):

        if type(x) is Complex or type(y) is Complex:
            s.x = Re(x) - Im(y)
            s.y = Im(x) + Re(y)
            if x.arr or y.arr:
                s.C = [Complex(s.x[i], s.y[i]) for i in range(len(x))]
                s.arr = True
            else:
                s.arr = False

        elif np.ndim(x) == 0 and np.ndim(y) == 0:
            s.x=x
            s.y=y
            s.arr=False

        elif len(x)==len(y):
            s.x=np.array(x)
            s.y=np.array(y)
            s.C=[Complex(x[i],y[i]) for i in range(len(x))]
            s.arr=True

        else:
            raise ValueError("Lists must be of equal length.")

        s.__clean()

    def __clean(s):
        if s.arr:
            map(lambda x: x.__clean(), s.C)
            s.x = np.array(list(map(Re, s.C)))
            s.y = np.array(list(map(Im, s.C)))
            return
        if abs(round(s.x) - s.x) <= 5*EPS: s.x = round(s.x)
        if abs(round(s.y) - s.y) <= 5*EPS: s.y = round(s.y)



    def isInt(s):
        return Im(s)==0 and int(Re(s))==Re(s)

    def isReal(s):
        return Im(s)==0

    def __int__(s):
        if not s.arr and s.isReal(): return int(Re(s))
        raise TypeError(f"int() argument must be a string or a real number, not Complex Number {s}")

    def __float__(s):
        if not s.arr and s.isReal(): return float(Re(s))
        raise TypeError(f"float() argument must be a string or a real number, not Complex Number {s}")

    def __repr__(s):
        if s.arr:
            return str([str(s.C[i]) for i in range(len(s.C))])
        else:
            return (str(s.x) if s.x!=0 or s.y==0 else "")+("+" if s.y>0 and s.x!=0 else "")+(str(s.y) if not (s.y==1 or s.y==0 or s.y==-1) else "-" if s.y==-1 else "")+("i" if s.y!=0 else "")

    def __len__(self):
        if self.arr: return len(self.C)
        else: raise TypeError(f"Scalar Complex '{self}' has no length.")

    def __getitem__(self, key):
        if self.arr:
            return self.C[key]
        else: raise TypeError(f"Scalar Complex '{self}' is not subscriptable.")

    def __setitem__(s, key, val):
        if s.arr:
            s.x[key] = Re(val)
            s.y[key] = Im(val)
            s.C[key] = val
        else:
            raise TypeError(f"Scalar Complex '{s}' is not subscriptable.")

    def __index__(s):
        if not s.arr and s.isInt(): return Re(s)
        raise TypeError(f"{s} cannot be interpreted as an integer")

    def __iter__(s):
        if s.arr:
            for ele in s.C:
                yield ele
        else:
            yield s

    def __abs__(s):
        return np.sqrt(s.x**2+s.y**2)


    def __invert__(s):
        return Complex(s.x,-s.y)


    def __add__(s,o):
        return Complex(s.x+Re(o),s.y+Im(o))

    def __radd__(s,o):
        return Complex(s.x+o,s.y)

    def __iadd__(s, o):
        return s+o

    def __neg__(s):
        return Complex(-s.x,-s.y)

    def __sub__(s,o):
        return s+(-o)

    def __rsub__(s,o):
        return o+(-s)

    def __mul__(s, o):
        return Complex(s.x*Re(o)-s.y*Im(o),s.x*Im(o)+s.y*Re(o))

    def __rmul__(s, o):
        return Complex(o * s.x, o * s.y)

    def __imul__(s, o):
        C=s*o
        return C

    def __pow__(s,o):
        if np.ndim(o)!=0 or (type(o) is Complex and o.arr):
            return np.array(list(map(lambda x: s**x,o)))

        if o.isInt():
            C=Complex(1,0)
            if o > 0:
                for j in range(int(o)): C *= s
            elif o < 0:
                for j in range(int(o)): C /= s
            return C
        A=abs(s)
        t=arg(s)
        x=Re(o)
        y=Im(o)
        return A**x*e**(-y*t+i*(x*t+np.log(A)*y))

    def __rpow__(s,A):
        if np.ndim(A) != 0:
            if s.arr:
                return np.array(list(map(lambda x, y: x ** y, A, s)))
            else:
                return np.array(list(map(lambda x: x ** s, A)))
        elif s.arr:
            return np.array(list(map(lambda x: A ** x, s)))
        if A == e and s.x==0: return Complex(np.cos(s.y),np.sin(s.y))
        return A**s.x * e**(i*np.log(A)*s.y)

    def __rtruediv__(s, A):
        return A * ~s / abs(s) ** 2

    def __truediv__(s, o):
        if o.isReal(): return Complex(s.x / Re(o), s.y / Re(o))
        return s * (1 / o)

    def __itruediv__(s, o):
        return s / o

    def __eq__(s, o):
        return s.x == o.x and s.y == o.y

    def __ne__(s, o):
        return s.x != o.x or s.y != o.y

    def __lt__(s, o):
        if s.arr: return np.array(list(map(lambda x: x < o, s)))
        if type(o) is Complex and o.arr: return np.array(list(map(lambda x: s < x, o)))
        if s.isReal() and o.isReal(): return Re(s) < Re(o)
        raise ValueError(f"{s} cannot be interpreted as an integer")

    def __le__(s, o):
        if s.arr: return np.array(list(map(lambda x: x <= o, s)))
        if type(o) is Complex and o.arr: return np.array(list(map(lambda x: s <= x, o)))
        if s.isReal() and o.isReal(): return Re(s) <= Re(o)
        raise ValueError(f"{s} cannot be interpreted as an integer")

    def __gt__(s, o):
        if s.arr: return np.array(list(map(lambda x: x > o, s)))
        if type(o) is Complex and o.arr: return np.array(list(map(lambda x: s > x, o)))
        if s.isReal() and o.isReal(): return Re(s) > Re(o)
        raise ValueError(f"{s} cannot be interpreted as an integer")

    def __ge__(s, o):
        if s.arr: return np.array(list(map(lambda x: x >= o, s)))
        if type(o) is Complex and o.arr: return np.array(list(map(lambda x: s >= x, o)))
        if s.isReal() and o.isReal(): return Re(s) >= Re(o)
        raise ValueError(f"{s} cannot be interpreted as an integer")

    def scatter(self, ax):
        ax.scatter(self.x, self.y)




EPS = np.finfo(np.float64).eps
e =np.e
pi=np.pi
i = Complex.i

def Re(s):
    if type(s) is not Complex: return s
    return s.x

def Im(s:Complex):
    if type(s) is not Complex:
        try:
            return np.array(list(map(Im,s)))
        except TypeError:
            return 0
    return s.y

def sca_arg(s):
    if type(s) is not Complex: return np.arctan2(0,s)
    return np.arctan2(s.y, s.x)
arg=np.vectorize(sca_arg)


curse(int, "isInt", lambda x: True)
curse(np.int64,"isInt",lambda x: True)
curse(float, "isInt", lambda x: int(x)==x)
curse(np.float64, "isInt", lambda x: int(x)==x)
curse(np.ndarray, "isInt", lambda x: np.array([y % 1 == 0 for y in x]))

curse(int, "isReal", lambda x: True)
curse(float, "isReal", lambda x: True)
curse(np.int64,"isReal",lambda x: True)
curse(np.float64,"isReal",lambda x: True)
curse(np.ndarray, "isReal", lambda x: np.array([y.isReal() for y in x]))
