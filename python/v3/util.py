from random import randint
from typing import List, Callable, TypeVar

T = TypeVar('T')


def remove_all(arr: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """Removes a random element from the list which matches the predicate."""
    idxs = [idx for idx, el in enumerate(arr) if predicate(el)]
    return [arr.pop(idx) for idx in reversed(idxs)]


def remove_first(xs: List[T], predicate: Callable[[T], bool]) -> T:
    """Removes the first element from the list which matches the predicate."""
    idx = next((idx for idx, x in enumerate(xs) if predicate(x)), None)
    if idx is not None:
        return xs.pop(idx)


def remove_random(arr: List[T], predicate: Callable[[T], bool]) -> T:
    """Removes a random element from the list which matches the predicate."""
    idxs = [idx for idx, el in enumerate(arr) if predicate(el)]
    if len(idxs) == 0:
        return None
    idx = idxs[randint(0, len(idxs)-1)]
    return arr.pop(idx)
