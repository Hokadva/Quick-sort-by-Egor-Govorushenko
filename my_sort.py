"""
Quick sort realization
"""
#pylint: disable=R0912
from typing import Optional, Callable


NUM_OF_MEDIAN_CANDIDATES = 3
MIN_ARRAY_SIZE = 1000


def my_sort(
        array: list, reverse: bool=False, key: Optional[Callable]=None,
        cmp: Optional[Callable]=None) -> list:
    """
    A quick erase option that takes a pivot of 5 (NUM_OF_MEDIAN_CANDIDATES - const)
    array elements whose numbers are - 0 1 2 3 4 (calculated using the formula:
    len(array)*(i + 1)/NUM_OF_MEDIAN_CANDIDATES) - 1;
    for all i < NUM_OF_MEDIAN_CANDIDATES). key translate element to
    comparable element. cmp(x,y) - func, which compare key(x) and key(y).
    """
    if not array:
        return []

    if key is None:
        def key(x):
            return x

    if cmp is None:
        def cmp(x, y):
            return key(x) < key(y)

    def new_cmp(x, y):
        return cmp(key(x), key(y)) ^ reverse

    arr_len = len(array)

    if arr_len == 1:
        return array

    if (arr_len < MIN_ARRAY_SIZE or
        arr_len <= NUM_OF_MEDIAN_CANDIDATES or NUM_OF_MEDIAN_CANDIDATES == 1):
        pivot = array[arr_len // 2]

    else:
        candidates = [array[arr_len * (nm + 1) // NUM_OF_MEDIAN_CANDIDATES - 1]
                      for nm in range(NUM_OF_MEDIAN_CANDIDATES)]

        for pivot in candidates:
            counter = 0
            for el in candidates:
                counter += int(new_cmp(el, pivot))
                if counter > NUM_OF_MEDIAN_CANDIDATES // 2:
                    break

            if counter == NUM_OF_MEDIAN_CANDIDATES // 2:
                break

    lw_elements = []
    eq_elements = []
    hg_elements = []

    for element in array:
        if key(element) == key(pivot):
            eq_elements.append(element)
        elif new_cmp(element, pivot):
            lw_elements.append(element)
        else:
            hg_elements.append(element)

    return (my_sort(lw_elements, reverse, key, cmp)
            + eq_elements + my_sort(hg_elements, reverse, key, cmp))
