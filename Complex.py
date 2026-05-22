import numpy as np

class Complex:

    def __init__(s,x=0,y=0):

        if np.ndim(x)==0 and np.ndim(y)==0:
            s.x=x
            s.y=y

            s.arr=False

        elif len(x)==len(y):
            s.x=x
            s.y=y
            s.C=[Complex(x[i],y[i]) for i in range(len(x))]
            s.arr=True

        else:
            raise ValueError("Lists must be of equal length.")



    @staticmethod
    def expi(n):
        C=Complex(np.cos(n),np.sin(n))
        return C

    def __repr__(s):
        if s.arr:
            return str([str(s.C[i]) for i in range(len(s.C))])
        else:
            return (str(s.x) if s.x!=0 or s.y==0 else "")+("+" if s.y>0 and s.x!=0 else "")+(str(s.y) if not (s.y==1 or s.y==0) else "")+("i" if s.y!=0 else "")

    def __len__(self):
        if self.arr: return len(self.C)
        else: raise TypeError(f"Scalar Complex '{self}' has no length.")

    def __getitem__(self, i):
        if self.arr: return self.C[i]
        else: raise TypeError(f"Scalar Complex '{self}' is not subscriptable.")


    def __abs__(s):
        return np.sqrt(s.x**2+s.y**2)

    def arg(s):
        return np.atan2(s.y,s.x)

    def __invert__(s):
        return Complex(s.x,-s.y)


    def __add__(s,o):
        if s.arr:
            return Complex(s.x+o.x,s.y+o.y)
        else:
            C=Complex()
            if type(o) is Complex:
                C.x=s.x+o.x
                C.y=s.y+o.y
                return C
            C.x=s.x+o
            C.y=s.y
            return C

    def __neg__(s):
        return Complex(-s.x,-s.y)

    def __sub__(s,o):
        return s+(-o)

    def __mul__(s, o):
        if type(o) is not Complex:
            return Complex(o*s.x,o*s.y)

        A=abs(s)*abs(o)
        t=s.arg+o.arg

        return A*Complex.expi(t)

    def Re(self):
        return self.x

    def Im(self):
        return self.y
