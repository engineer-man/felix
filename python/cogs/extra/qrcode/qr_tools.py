def GF2_create_tables(order, irreducible_polynomial):
    # Return the antilog (exponent) table and log table of a Galios Field (GF)
    # with an order that is a power of 2

    if order % 2:
        raise ValueError('GF2 only takes orders that are powers of 2')

    # Requires the irreducible_polynomial to be a primitive root of the field GF(order)
    # The QR Code Specification uses GF(256) with irreducible_polynomial = 285
    # Primitive Roots for GF256 are 285,299,301,333,351,355,357,361,369,391,397,425,451,463,487,501

    # The elements of the "antilog table" are: [2**0, 2**1, 2**2, []...] , 2**(order-1)]
    # Instead of calculating each 2**n directly, we can use the previous result and
    # multiply it by 2 so to find 2**n we do 2**(n-1) * 2.
    # All elements of the field must be smaller than the order, so if the result of a
    # multiplication by 2 is >= order, then the Specification tells us to bitwise modulo
    # (which is just XOR) the result with the irreducible_polynomial.

    # Pre fill the element list with 2**0
    antilog = [1]
    # Calculate the remaining order-1 elements by multiplying the "most recent element" by 2.
    # If a element would be >=order, we XOR (^) it with the irreducible_polynomial to reduce it
    # back down to be between 0 and 255 (inclusive). This will generate a unique integer number
    # between 1 and order-2 for each element of the antilog table.
    # The last element in the Table is 1 again and the cycle starts over.
    # This works out this way because we chose irreducible_polynomial to be a primitive root
    # of the Field.
    for _ in range(order-1):
        nxt = antilog[-1] * 2
        if nxt >= order:
            nxt ^= irreducible_polynomial
        antilog.append(nxt)

    # The log Table is a table that, at position n, has the integer value of the location
    # where n appears in the log table.
    # Example with G256: G256 starts like this: [1, 2, 4, 8, 16, 32, 64, 128, 29, 58, 116, [...]
    # So the log table will start like this [None, 0, 1, 25, 2,
    # because 0 does not appear in the log table, the 0th element of the log table is
    # not defined. The element at position 1 in the log table tells us where 1 appears in the
    # log table. The element at position 2 tells us where the number 2 appears in the log table ..
    log = [None]+[antilog.index(n) for n in range(1, order)]
    return (antilog, log)

    # ANTILOG TABLE
    # Allows us to easily calculate 2**n by looking up position n in the antilog table

    # log TABLE
    # The log table allows us to easily multiply 2 numbers ( while working in a GF )
    # by looking up the logs of the numbers.
    # Example: we want to multiply 57 and 158 in GF(256, 285):
    # First we look up the exponent e1 you need so that 2**e1 == 57 using the log table.
    # e1 = 154
    # now we look up e2 so that 2**e2 = 158
    # e2 = 137
    # We want to multipy 57 by 158 -> this means we can just multiply 2**154 by 2**137 which can
    # be done easily by adding the exponents
    # 2**154 * 2**137 = 2**(154+137) = 2**291
    # Because 2**255 = 1 (This is when the log table starts repeating)
    #   -> 2**291 == 2**255 * 2**36 = 2**36
    # So we take the result of the exponent addition modulo 255 to get the exponent of the product
    # Then we use the antilog table to look up 2**36 -> 225
    # So in GF(256, 285): 57 * 158 = 225


ALOG, LOG = GF2_create_tables(256, 285)


# ================================================================================================
# Note on Polynomials:
# ================================================================================================
# Polynomials are represented as lists of coefficients (all coefficients are inside GF(256, 285) )
# with the position in the list representing the degree of the term the coefficient belongs to
# (the first element in the list corresponds to the term with the highest degree)

# The list of coefficients can take one of 2 forms
# 1:
#   A list of exponents (of 2), because all elements coefficient can be written as 2^n
#   Example: [0,1,2,3] represents the (3rd degree) polynomial P(X) = x³ + 2x² + 4x + 8
#   In this form, terms that do not exist are denoted with a coefficient of None
#   Example: [0,None,None] represents the (2nd degree) polynomial P(X) = x²
#
# 2:
#   Polynomials are stored as lists of integer coefficients (all coefficients are inside GF256)
#   In this form, terms that do not exist are have a coefficient of 0
#   Example: [1,0] represents the (1st degree) polynomial P(X) = x

# The following classes implements polynomial multiplication and converting from exponent type
# to integer type

class Polynomial_GF256_base(list):
    def __mul__(self, other):
        # This function multiplies 2 polynomials with coefficients in GF(256, 285)
        # See Step 7 at:
        # https://www.thonky.com/qr-code-tutorial/error-correction-coding

        # If the polynomials are not in exponent form, convert them to exponent form first
        if isinstance(self, Polynomial_GF256_int):
            self = self.to_exp()
        if isinstance(other, Polynomial_GF256_int):
            other = other.to_exp()

        # if you want to add coefficients, you just XOR them (integer form)
        # If you want to multiply coefficients, you convert them into exponent form,
        # add their exponents and take modulo 255 to keep the result inside GF256
        # then convert back to integer form (if needed)

        # Degree of the result polynomial will be the sum of the degrees of the source polys
        target_degree = self.degree + other.degree
        # Create the list to hold the result polynomial (size of list is target degree + 1)
        result_polynomial_coefficients = [0] * (target_degree + 1)
        # Multiply each term of polynomial 1 by each term of polynomial2
        for exponent_of_x1, exponent_of_coefficient1 in enumerate(reversed(self)):
            if exponent_of_coefficient1 is None:
                continue
            for exponent_of_x2, exponent_of_coefficient2 in enumerate(reversed(other)):
                if exponent_of_coefficient2 is None:
                    continue
                # When multiplying the coefficients, add their exponents and mod 255
                coefficient_product = (exponent_of_coefficient1+exponent_of_coefficient2) % 255
                # When multiplying the x_terms, add the exponents
                x_exponent_sum = exponent_of_x1+exponent_of_x2
                # Add (XOR) the integer representation of the coefficient product to the
                # result polynomial at the correct position of the exponent of x
                # To convert the coefficient to integer form we use the ALOG lookup table
                result_polynomial_coefficients[x_exponent_sum] ^= ALOG[coefficient_product]
        # This will generate the result polynomial in integer form in reversed order
        # so before we return it, we reverse it and turn it back to exponent form.
        res = Polynomial_GF256_int(reversed(result_polynomial_coefficients)).to_exp()
        return res

    @property
    def degree(self):
        return len(self) - 1

# These 2 Classes implement the integer and exponent form of polynomials and can be used to pretty
# print them and to convert between them
class Polynomial_GF256_exp(Polynomial_GF256_base):
    def to_int(self):
        return Polynomial_GF256_int([ALOG[x] if x is not None else 0 for x in self])

    def get_str(self):
        return ' + '.join(
            f'{0 if n is None else 2**n}x**{len(self)-i}' for i, n in enumerate(self, 1)
        )

    def copy_with_increased_degree(self, n):
        return Polynomial_GF256_exp(self + [None] * n)

    def multiply_by(self, factor):
        return Polynomial_GF256_exp([(x+factor)%255 if x is not None else None for x in self])

class Polynomial_GF256_int(Polynomial_GF256_base):
    def to_exp(self):
        return Polynomial_GF256_exp([LOG[x] if x else None for x in self])

    def get_str(self):
        return ' + '.join(f'{n}x**{len(self)-i}' for i, n in enumerate(self, 1))

    def copy_with_increased_degree(self, n):
        return Polynomial_GF256_int(self + [0] * n)

    def __xor__(self, other):
        return Polynomial_GF256_int([x^y for x,y in zip(self, other)])

    def discard_leading_zeroes(self):
        while self[0] == 0:
            self = self[1:]
        return Polynomial_GF256_int(self)

def get_matrix_str_full_size(matrix):
    border = '██'
    colors = ['██','  ','▒▒', '░░']
    max_x = max([x for x,y in matrix.keys()])
    min_x = min([x for x,y in matrix.keys()])
    max_y = max([y for x,y in matrix.keys()])
    min_y = min([y for x,y in matrix.keys()])
    res = ''
    res += border*(max_x+3) + '\n'
    for y in range(min_y, max_y+1):
        res += border
        for x in range(min_x, max_x+1):
            res += colors[matrix.get((x,y), -1)]
        res += border + '\n'
    res += border*(max_x+3) + '\n'
    return res

def get_matrix_str_half_size(matrix):
    top = '▀'
    bottom ='▄'
    full = '█'
    empty = ' '
    colors = [[full,top],[bottom,empty]]
    max_x = max([x for x,y in matrix.keys()])
    min_x = min([x for x,y in matrix.keys()])
    max_y = max([y for x,y in matrix.keys()])
    min_y = min([y for x,y in matrix.keys()])
    res = ''
    res += bottom*(max_x+3) + '\n'
    for y in range(min_y, max_y+1,2):
        res += full
        for x in range(min_x, max_x+1):
            res += colors[matrix.get((x,y), 0)][matrix.get((x,y+1), 0)]
        res += full + '\n'
    # res += *(max_x+3) + '\n'
    return res

if __name__ == '__main__':
    l, al = GF2_create_tables(256, 285)
    print(l)
    print(al)
    print(al[(al[57] + al[158]) % 255])
    e = Polynomial_GF256_exp([0, None, 2, None])
    print('exp_polynomial', e, e.get_str())
    i = e.to_int()
    print('int_polynomial', i, i.get_str())
    e2 = i.to_exp()
    print('e2_polynomial ', e2, e2.get_str())
