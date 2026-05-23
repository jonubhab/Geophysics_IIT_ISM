import numpy as np
from forbiddenfruit import curse

class Meta(type):
    @property
    def i(cls):
        return cls(0,1)



class Complex(metaclass=Meta):


    def __init__(s,x=0,y=0):

        if np.ndim(x)==0 and np.ndim(y)==0:
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

    def __getitem__(self, i):
        if self.arr: return self.C[i]
        else: raise TypeError(f"Scalar Complex '{self}' is not subscriptable.")

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
            for j in range(Re(o)):
                C*=s
            return C
        A=abs(s)
        t=arg(s)
        x=Re(o)
        y=Im(o)
        return A**x*e**(-y*t+i*(x*t+np.log(A)*y))

    def __rpow__(s,A):
        #print(A,s.x)
        if A == e and s.x==0: return Complex(np.cos(s.y),np.sin(s.y))
        return A**s.x * e**(i*np.log(A)*s.y)


e =np.e
pi=np.pi
i = Complex.i

def Re(s):
    if type(s) is not Complex: return s
    return s.x

def Im(s:Complex):
    if type(s) is not Complex: return 0
    return s.y

def sca_arg(s):
    if type(s) is not Complex: return np.arctan2(0,s)
    return np.atan2(s.y,s.x)
arg=np.vectorize(sca_arg)


curse(int, "isInt", lambda x: True)
curse(np.int64,"isInt",lambda x: True)
curse(float, "isInt", lambda x: int(x)==x)
curse(np.float64, "isInt", lambda x: int(x)==x)
curse(np.ndarray,"isInt", lambda x: np.array(y%1==0 for y in x))

curse(int, "isReal", lambda x: True)
curse(float, "isReal", lambda x: True)
curse(np.int64,"isReal",lambda x: True)
curse(np.float64,"isReal",lambda x: True)
curse(np.ndarray,"isReal", lambda x: np.array(y.isReal() for y in x))