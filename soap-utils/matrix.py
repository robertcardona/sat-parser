"""
This file contains the IntervalMatrix class and associated objects.

This handles matrices with interval objects as entries.
"""

# https://stackoverflow.com/questions/33533148/
from typing import Generator, Iterator, Literal, NoReturn

import portion as P

class IntervalMatrix():
    """
    A class used to represent a matrix of m rows by n columns whose entries
        are interval objects.

    Attributes
    ----------
    m : int
        The number of rows in the matrix.
    n : int 
        The number of columns in the matrix
    array : list[list[P]]
        A two dimensional m-by-n array of Portion interval objects.
    """

    def __init__(
        self,
        m: int,
        n: int,
        array: list[list[P]] | None = None
        # symmetric: bool = False
    ) -> None:
        """
        Parameters
        ----------
        m : int
            The number of rows in the matrix.
        n : int
            The number of columns in the matrix
        array : list[list[P]] | None
            A two dimensional m-by-n array of Portion interval objects, or None.
        symmetric : bool
            If True, class can assume the matrix is symmetric.
        """
        self.dim_row = m
        self.dim_col = n

        # self.symmetric = symmetric

        if array is not None:
            self.array = array
        else:
            self.array = self.empty_array(m, n)

        if len(self.array) != m:
            error_message = f"`array` should have {m} elements"
            raise ValueError(error_message)
        for row in self.array:
            if len(row) != n:
                error_message = f"Every row in `array` should have {n} entries"
                raise ValueError(error_message)

        return None

    def get_slice_at(self, t: float) -> list[list[int]]:
        array = [[0 for i in range(self.dim_row)] for j in range(self.dim_col)]
        
        indices = IntervalMatrix.get_indices(self.dim_row, self.dim_col)
        for i, j in indices:
            if t in self[i, j]:
                array[i][j] = 1

        return array

    def is_symmetric(self) -> bool:
        if self.dim_row != self.dim_col:
            return False

        #[(i, j) for i in range(m) for j in range(i + 1, n)]
        indices = IntervalMatrix.get_indices(self.dim_row, self.dim_col)
        indices = [(i, j) for (i, j) in indices if i > j]
        for i, j in indices:
            if self[i, j] != self[j, i]:
                return False

        return True

    def get_diagonal(self) -> list[P]:
        return [self[i, i] for i in range(min(self.dim_row, self.dim_col))]
    
    def set_diagonal(self, value: P) -> None:
        for i in range(min(self.dim_row, self.dim_col)):
            self[i, i] = value

    def get_dimension(self) -> tuple[int, int]:
        return self.dim_row, self.dim_col

    def get_k_walks(self, k: int) -> "IntervalMatrix":
        return self**k

    def get_k_cumulant(self, k: int) -> "IntervalMatrix" | Literal[0]:
        if self.dim_row != self.dim_col:
            raise ValueError("Dimension mismatch error in k-cumulant")

        matrices = [IntervalMatrix.identity_matrix(self.dim_row)]

        for i in range(1, k + 1):
            matrices.append(self * matrices[-1])

        # require `__radd__` for this sum to work
        return sum(matrices)

    @staticmethod
    def get_indices(rows: int, columns: int) -> list[tuple[int, int]]:
        return [(i, j) for i in range(rows) for j in range(columns)]

    @staticmethod
    def empty_array(m: int, n: int) -> list[list[P]]:
        return [[P.empty() for c in range(n)] for r in range(m)]

    @staticmethod
    def identity_matrix(m: int) -> "IntervalMatrix":
        matrix = IntervalMatrix(m, m)
        for i in range(m):
            matrix[i, i] = P.open(-P.inf, P.inf)
        return matrix
    
    @staticmethod
    def constant_matrix(m: int, n: int, value: P) -> "IntervalMatrix":
        array = [[value for i in range(n)] for j in range(m)]
        return IntervalMatrix(m, m, array)

    def __getitem__(self, index: tuple[int, int]) -> P:
        return self.array[index[0]][index[1]]

    def __setitem__(self, index: tuple[int, int], value: P) -> None:
        self.array[index[0]][index[1]] = value

    def __iter__(self) -> Iterator:
        return IntervalMatrixIterator(self)

    def __add__(self, other: "IntervalMatrix") -> "IntervalMatrix":
        if self.dim_row != other.dim_row or self.dim_col != other.dim_col:
            raise ValueError("Dimension mismatch error in addition")
        
        matrix = IntervalMatrix(self.dim_row, self.dim_col)

        indices = IntervalMatrix.get_indices(self.dim_row, self.dim_col)

        for i, j in indices:
            matrix[i, j] = self[i, j] | other[i, j]
            
        return matrix

    # https://stackoverflow.com/questions/51036121/
    def __radd__(self, other) -> "IntervalMatrix":
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __mul__(self, other: "IntervalMatrix") -> "IntervalMatrix":
        if self.dim_col != other.dim_row:
            raise ValueError("Dimension mismatch error in multiplication")

        matrix = IntervalMatrix(self.dim_row, other.dim_col)

        indices = IntervalMatrix.get_indices(self.dim_row, other.dim_col)
        for i, j in indices:
            for k in range(self.dim_col):
                matrix[i, j] |= (self[i, k] & other[k, j])

        return matrix

    def __pow__(self, n: int) -> "IntervalMatrix":
        if self.dim_row != self.dim_col:
            raise ValueError("Dimension mismatch error in power")

        if n <= 0:
            return IntervalMatrix.identity_matrix(self.dim_row)
        elif n % 2 == 0:
            return (self * self)**(n // 2)
        else:
            return self * (self * self)**((n - 1) // 2)

    def __lshift__(self, t: int | float) -> "IntervalMatrix":
        shift = lambda x : x - t
        interval_shift = lambda x : x.replace(lower = shift, upper = shift)

        matrix = IntervalMatrix(self.dim_row, self.dim_col)

        indices = IntervalMatrix.get_indices(self.dim_row, self.dim_col)
        for i, j in indices:
            matrix[i, j] = self[i, j].apply(interval_shift)

        return matrix

    def __rshift__(self, t: int | float) -> "IntervalMatrix":
        shift = lambda x : x + t
        interval_shift = lambda x : x.replace(lower = shift, upper = shift)

        matrix = IntervalMatrix(self.dim_row, self.dim_col)

        indices = IntervalMatrix.get_indices(self.dim_row, self.dim_col)
        for i, j in indices:
            matrix[i, j] = self[i, j].apply(interval_shift)

        return matrix

    def __invert__(self) -> "IntervalMatrix":
        matrix = IntervalMatrix(self.dim_row, self.dim_col)

        indices = IntervalMatrix.get_indices(self.dim_row, self.dim_col)
        for i, j in indices:
            matrix[i, j] = ~self[i, j]

        return matrix



    def __eq__(self, other: object) -> bool:
        
        if not isinstance(other, IntervalMatrix):
            return NotImplemented

        if self.dim_col != other.dim_col or self.dim_row != other.dim_row:
            return False
        
        indices = IntervalMatrix.get_indices(self.dim_row, self.dim_col)
        for i, j in indices:
            if self[i, j] != other[i, j]:
                return False

        return True
        
    def __str__(self) -> str:
        array = [["" for i in range(self.dim_row)] for j in range(self.dim_col)]

        indices = IntervalMatrix.get_indices(self.dim_row, self.dim_col)
        
        width = 0
        for i, j in indices:
            array_ij =  str(self[i, j])
            array[i][j] = array_ij
            
            width = max(width, len(array[i][j]))

        for i, j in indices:
            array[i][j] = "{:<{}}".format(array[i][j], width)

        rows = []
        for row in array:
            rows.append(" ".join(row))
        return "\n".join(rows)



class IntervalMatrixIterator():

    def __init__(self, matrix: IntervalMatrix) -> None:
        self.matrix = matrix
        self.index = (0, 0)

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> P:
        dim_row = self.matrix.dim_row
        dim_col = self.matrix.dim_col

        if self.index[0] == dim_row:
            raise StopIteration()

        result = self.matrix[self.index]

        if self.index[1] + 1 == dim_col:
            self.index = (self.index[0] + 1, 0)
        else:
            self.index = (self.index[0], self.index[1] + 1)

        return result

def matrix_enumerate(
    matrix: IntervalMatrix
) -> Generator[tuple[tuple[int, int], P], None, None]:

    dim_row = matrix.dim_row
    dim_col = matrix.dim_col

    index = (0, 0)
    counter = 0
    for element in matrix:
        yield index, element
        
        counter += 1
        index = (counter // dim_col, counter % dim_col)

if __name__ == "__main__":
    matrix = IntervalMatrix(4, 4)
    
    # test __iter__ and __init__ with `array = None`
    count = 0
    for entry in matrix:
        assert entry == P.empty()
        count += 1
    assert count == 16

    # test constant_matrix
    matrix_const = IntervalMatrix.constant_matrix(4, 4, P.closed(-P.inf, P.inf))
    for entry in matrix_const:
        assert entry == P.closed(-P.inf, P.inf) 

    # test set_diagonal, get_diagonal
    matrix_id = IntervalMatrix.identity_matrix(3)
    assert True not in [P.empty() == e for e in matrix_id.get_diagonal()]

    matrix = IntervalMatrix(3, 3)
    assert False not in [P.empty() == e for e in matrix.get_diagonal()]

    matrix.set_diagonal(P.open(-P.inf, P.inf))
    assert matrix == matrix_id

    # test `is_symmetric`
    assert matrix.is_symmetric()
    matrix[0, 2] = P.closed(-P.inf, P.inf)
    assert matrix.is_symmetric() == False
    matrix[2, 0] = P.closed(-P.inf, P.inf)
    assert matrix.is_symmetric()

    # test __init__ with array defined
    array_a = [
        [P.open(-P.inf,P.inf), P.closed(0, 6), P.closed(6, 10), P.empty()],
        [P.empty(), P.open(-P.inf,P.inf), P.closed(1, 4), P.closed(3, 7)],
        [P.empty(), P.empty(), P.open(-P.inf,P.inf), P.closed(0, 8)],
        [P.empty(), P.empty(), P.empty(), P.open(-P.inf,P.inf)]
    ]

    array_b = [
        [P.open(-P.inf,P.inf), P.closed(0, 6), P.closed(1, 4) | P.closed(6, 10), P.closed(3, 8)],
        [P.empty(), P.open(-P.inf,P.inf), P.closed(1, 4), P.closed(1, 7)],
        [P.empty(), P.empty(), P.open(-P.inf,P.inf), P.closed(0, 8)],
        [P.empty(), P.empty(), P.empty(), P.open(-P.inf,P.inf)]
    ]

    array_c = [
        [P.open(-P.inf,P.inf), P.closed(0, 6), P.closed(1, 4) | P.closed(6, 10), P.closed(1, 8)],
        [P.empty(), P.open(-P.inf,P.inf), P.closed(1, 4), P.closed(1, 7)],
        [P.empty(), P.empty(), P.open(-P.inf,P.inf), P.closed(0, 8)],
        [P.empty(), P.empty(), P.empty(), P.open(-P.inf,P.inf)]
    ]

    matrix = IntervalMatrix(4, 4, array_a)
    matrix_b = IntervalMatrix(4, 4, array_b)
    matrix_c = IntervalMatrix(4, 4, array_c)

    # test __eq__, __add__, and __mul__
    assert matrix + matrix == matrix
    assert matrix * matrix == matrix_b
    assert matrix * matrix * matrix == matrix_c
    assert not matrix * matrix == matrix

    # test __pow__
    assert matrix**2 == matrix_b
    assert matrix**3 == matrix_c

    # test `get_k_cumulant`
    assert matrix.get_k_cumulant(0) == IntervalMatrix.identity_matrix(4)
    assert matrix.get_k_cumulant(1) == matrix 
    assert matrix.get_k_cumulant(2) == matrix_b 
    assert matrix.get_k_cumulant(3) == matrix_c
    # print(matrix.get_k_cumulant(3))

    # test << and >> operators
    assert (matrix_c << 1)[0, 2] == P.closed(0, 3) | P.closed(5, 9)
    assert (matrix_c >> 1)[0, 2] == P.closed(2, 5) | P.closed(7, 11)

    # test ~ operator
    assert matrix_b + ~matrix_b == matrix_const

    # for (i, j), element in matrix_enumerate(matrix):
    #     print(f"matrix[{i}, {j}] = {element}")
    #     print(f"{i * matrix.dim_col + j}")

    # for index, element in enumerate(matrix):
    #     print(f"matrix[{index}] = {element}")

    for x, y in zip(matrix_enumerate(matrix), matrix):
        assert x[1] == y
        # print(f"{x[1] = }, {y = }")

    # interval = P.closed(1, 4) | P.closed(6, 10)
    # print(f"{P.closed(-P.inf, P.inf) - interval = }")

    # for i in interval:
        # print(f"{i = }")
    print(f"{matrix.get_slice_at(3)}")