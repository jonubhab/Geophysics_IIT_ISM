from Complex import *

x = [1.25, -0.75, 1.25, -0.75]
y = [0, 0, 0, 0]
print(np.array(list(map(Im,1))))
print(Complex(x,y)*np.array([1,1,1,1]))
print(np.array(y).isInt())
print(Complex(x, y))
print(np.arange(5))
print(Complex(1,1)**np.array([1,2,Complex(2,0),4]))
print(arg(e**i))
print(np.e**Complex.i)
print(-np.array([2,1]))
print(2*i+8)
print(Complex([1,2],[3,2])+Complex(2,4))

print(type(Complex(0)) is Complex)

