# -*- coding: utf-8 -*-
#
from __future__ import division

import numpy
import sympy

import orthopy


def test_integral0(n=4):
    '''Make sure that the polynomials are orthonormal
    '''
    x = sympy.Symbol('x')
    y = sympy.Symbol('y')
    vals = numpy.concatenate(
        orthopy.disk.tree(n, numpy.array([x, y]), symbolic=True)
        )

    # Cartesian integration in sympy is bugged, cf.
    # <https://github.com/sympy/sympy/issues/13816>.
    # Simply transform to polar coordinates for now.
    r = sympy.Symbol('r')
    phi = sympy.Symbol('phi')
    assert sympy.integrate(
        r * vals[0].subs([(x, r*sympy.cos(phi)), (y, r*sympy.sin(phi))]),
        (r, 0, 1), (phi, 0, 2*sympy.pi)
        ) == sympy.sqrt(sympy.pi)

    for val in vals[1:]:
        assert sympy.integrate(
            r * val.subs([(x, r*sympy.cos(phi)), (y, r*sympy.sin(phi))]),
            (r, 0, 1), (phi, 0, 2*sympy.pi)
            ) == 0
    return


# def test_orthogonality(n=4):
#     x = sympy.Symbol('x')
#     y = sympy.Symbol('y')
#     tree = numpy.concatenate(
#         orthopy.disk.tree(n, numpy.array([x, y]), symbolic=True)
#         )
#     vals = tree * numpy.roll(tree, 1, axis=0)
#
#     for val in vals:
#         assert sympy.integrate(val, (x, -1, +1), (y, -1, +1)) == 0
#     return
#
#
# def test_normality(n=4):
#     x = sympy.Symbol('x')
#     y = sympy.Symbol('y')
#     tree = numpy.concatenate(
#             orthopy.disk.tree(n, numpy.array([x, y]), symbolic=True)
#             )
#
#     for val in tree:
#         assert sympy.integrate(val**2, (x, -1, +1), (y, -1, +1)) == 1
#     return
#
#
# def test_show(n=2, r=1):
#     def f(X):
#         return orthopy.disk.tree(n, X)[n][r]
#
#     orthopy.disk.show(f)
#     # orthopy.disk.plot(f)
#     # import matplotlib.pyplot as plt
#     # plt.savefig('quad.png', transparent=True)
#     return


# if __name__ == '__main__':
#     test_show()
