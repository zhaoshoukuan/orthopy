import itertools

import numpy
import sympy

from ..tools import full_like


def tree(n, *args, **kwargs):
    return list(itertools.islice(Iterator(*args, **kwargs), n + 1))


class Iterator:
    """Evaluates the entire tree of associated Legendre polynomials.

    There are many recurrence relations that can be used to construct the associated
    Legendre polynomials. However, only few are numerically stable. Many implementations
    (including this one) use the classical Legendre recurrence relation with increasing
    L.

    Useful references are

    Taweetham Limpanuparb, Josh Milthorpe,
    Associated Legendre Polynomials and Spherical Harmonics Computation for Chemistry
    Applications,
    Proceedings of The 40th Congress on Science and Technology of Thailand;
    2014 Dec 2-4, Khon Kaen, Thailand. P. 233-241.
    <https://arxiv.org/abs/1410.1748>

    and

    Schneider et al.,
    A new Fortran 90 program to compute regular and irregular associated Legendre
    functions,
    Computer Physics Communications,
    Volume 181, Issue 12, December 2010, Pages 2091-2097,
    <https://doi.org/10.1016/j.cpc.2010.08.038>.

    The return value is a list of arrays, where `out[k]` hosts the `2*k+1` values of the
    `k`th level of the tree

                              (0, 0)
                    (-1, 1)   (0, 1)   (1, 1)
          (-2, 2)   (-1, 2)   (0, 2)   (1, 2)   (2, 2)
            ...       ...       ...     ...       ...
    """

    def __init__(
        self, x, scaling, phi=None, with_condon_shortley_phase=True, symbolic=False,
    ):
        sqrt = numpy.vectorize(sympy.sqrt) if symbolic else numpy.sqrt
        # assert numpy.all(numpy.abs(x) <= 1.0)
        fun, args = {
            "natural": (_Natural, [symbolic]),
            "spherical": (_Spherical, [symbolic]),
            "complex spherical": (_ComplexSpherical, [phi, symbolic, False]),
            "complex spherical 1": (_ComplexSpherical, [phi, symbolic, True]),
            "normal": (_Normal, [symbolic]),
            "schmidt": (_Schmidt, [phi, symbolic]),
        }[scaling]
        self.c = fun(*args)

        self.phase = -1 if with_condon_shortley_phase else 1

        self.k = 0
        self.x = x
        self.sqrt1mx2 = sqrt(1 - x ** 2)
        self.last = [None, None]

    def __iter__(self):
        return self

    def __next__(self):
        if self.k == 0:
            out = numpy.array([full_like(self.x, self.c.p0)])
        else:
            z0, z1, c0, c1 = self.c.get_coefficients(self.k)
            # Make sure that self.sqrt1mx2 is listed first
            # https://github.com/sympy/sympy/issues/19399
            a = self.sqrt1mx2 * z0
            b = self.sqrt1mx2 * z1 * self.phase
            out = numpy.concatenate(
                [
                    [self.last[0][0] * a],
                    self.last[0] * numpy.multiply.outer(c0, self.x),
                    [self.last[0][-1] * b],
                ]
            )

            if self.k > 1:
                out[2:-2] -= (self.last[1].T * c1).T

        self.last[1] = self.last[0]
        self.last[0] = out
        self.k += 1
        return out


class _Natural:
    def __init__(self, symbolic):
        self.frac = sympy.Rational if symbolic else lambda x, y: x / y
        self.p0 = 1

    def get_coefficients(self, L):
        z0 = self.frac(1, 2 * L)
        z1 = 2 * L - 1
        c0 = [self.frac(2 * L - 1, L - m) for m in range(-L + 1, L)]
        if L == 1:
            c1 = None
        else:
            c1 = [self.frac(L - 1 + m, L - m) for m in range(-L + 2, L - 1)]
        return z0, z1, c0, c1


class _Spherical:
    def __init__(self, symbolic):
        self.frac = numpy.vectorize(sympy.Rational) if symbolic else lambda x, y: x / y
        self.sqrt = numpy.vectorize(sympy.sqrt) if symbolic else numpy.sqrt
        pi = sympy.pi if symbolic else numpy.pi

        self.p0 = 1 / self.sqrt(4 * pi)

    def get_coefficients(self, L):
        z0 = self.sqrt(self.frac(2 * L + 1, 2 * L))
        z1 = self.sqrt(self.frac(2 * L + 1, 2 * L))
        #
        m = numpy.arange(-L + 1, L)
        c0 = self.sqrt(self.frac((2 * L - 1) * (2 * L + 1), (L + m) * (L - m)))
        #
        if L == 1:
            c1 = None
        else:
            m = numpy.arange(-L + 2, L - 1)
            c1 = self.sqrt(
                self.frac(
                    (L + m - 1) * (L - m - 1) * (2 * L + 1),
                    (2 * L - 3) * (L + m) * (L - m),
                )
            )
        return z0, z1, c0, c1


class _ComplexSpherical:
    def __init__(self, phi, symbolic, geodesic):
        pi = sympy.pi if symbolic else numpy.pi
        imag_unit = sympy.I if symbolic else 1j
        self.sqrt = numpy.vectorize(sympy.sqrt) if symbolic else numpy.sqrt
        self.frac = numpy.vectorize(sympy.Rational) if symbolic else lambda x, y: x / y
        exp = sympy.exp if symbolic else numpy.exp

        # The starting value 1 has the effect of multiplying the entire tree by
        # sqrt(4*pi). This convention is used in geodesy and and spectral
        # analysis.
        self.p0 = 1 if geodesic else 1 / self.sqrt(4 * pi)
        self.exp_iphi = exp(imag_unit * phi)

    def get_coefficients(self, L):
        z0 = self.sqrt(self.frac(2 * L + 1, 2 * L)) / self.exp_iphi
        z1 = self.sqrt(self.frac(2 * L + 1, 2 * L)) * self.exp_iphi
        #
        m = numpy.arange(-L + 1, L)
        c0 = self.sqrt(self.frac((2 * L - 1) * (2 * L + 1), (L + m) * (L - m)))
        #
        if L == 1:
            c1 = None
        else:
            m = numpy.arange(-L + 2, L - 1)
            c1 = self.sqrt(
                self.frac(
                    (L + m - 1) * (L - m - 1) * (2 * L + 1),
                    (2 * L - 3) * (L + m) * (L - m),
                )
            )
        return z0, z1, c0, c1


class _Normal:
    def __init__(self, symbolic):
        self.sqrt = numpy.vectorize(sympy.sqrt) if symbolic else numpy.sqrt
        self.frac = numpy.vectorize(sympy.Rational) if symbolic else lambda x, y: x / y

        self.p0 = 1 / self.sqrt(2)

    def get_coefficients(self, L):
        z0 = self.sqrt(self.frac(2 * L + 1, 2 * L))
        z1 = self.sqrt(self.frac(2 * L + 1, 2 * L))
        #
        m = numpy.arange(-L + 1, L)
        c0 = self.sqrt(self.frac((2 * L - 1) * (2 * L + 1), (L + m) * (L - m)))
        #
        if L == 1:
            c1 = None
        else:
            m = numpy.arange(-L + 2, L - 1)
            c1 = self.sqrt(
                self.frac(
                    (L + m - 1) * (L - m - 1) * (2 * L + 1),
                    (2 * L - 3) * (L + m) * (L - m),
                )
            )
        return z0, z1, c0, c1


class _Schmidt:
    def __init__(self, phi, symbolic):
        self.sqrt = numpy.vectorize(sympy.sqrt) if symbolic else numpy.sqrt
        self.frac = numpy.vectorize(sympy.Rational) if symbolic else lambda x, y: x / y

        if phi is None:
            self.p0 = 2
            self.exp_iphi = 1
        else:
            self.p0 = 1
            imag_unit = sympy.I if symbolic else 1j
            exp = sympy.exp if symbolic else numpy.exp
            self.exp_iphi = exp(imag_unit * phi)

    def get_coefficients(self, L):
        z0 = self.sqrt(self.frac(2 * L - 1, 2 * L)) / self.exp_iphi
        z1 = self.sqrt(self.frac(2 * L - 1, 2 * L)) * self.exp_iphi
        #
        m = numpy.arange(-L + 1, L)
        c0 = (2 * L - 1) / self.sqrt((L + m) * (L - m))
        #
        if L == 1:
            c1 = None
        else:
            m = numpy.arange(-L + 2, L - 1)
            c1 = self.sqrt(self.frac((L + m - 1) * (L - m - 1), (L + m) * (L - m)))
        return z0, z1, c0, c1