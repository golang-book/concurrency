from typing import List
import threading
from . import go, make, receive, run, send


# Original functions:
#
# func ConcurrentMergeSort(xs []int) []int {
#     switch len(xs) {
#     case 0:
#         return nil
#     case 1, 2:
#         return merge(xs[:1], xs[1:])
#     default:
#         lc, rc := make(chan []int), make(chan []int)
#         go func() {
#             lc <- ConcurrentMergeSort(xs[:len(xs)/2])
#         }()
#         go func() {
#             rc <- ConcurrentMergeSort(xs[len(xs)/2:])
#         }()
#         return merge(<-lc, <-rc)
#     }
# }
#
#
# func merge(l, r []int) []int {
#     m := make([]int, 0, len(l)+len(r))
#     for len(l) > 0 || len(r) > 0 {
#         switch {
#         case len(l) == 0:
#             m = append(m, r[0])
#             r = r[1:]
#         case len(r) == 0:
#             m = append(m, l[0])
#             l = l[1:]
#         case l[0] <= r[0]:
#             m = append(m, l[0])
#             l = l[1:]
#         case l[0] > r[0]:
#             m = append(m, r[0])
#             r = r[1:]
#         }
#     }
#     return m
# }

def merge(l: List[int], r: List[int]) -> List[int]:
    m = []
    while len(l) > 0 or len(r) > 0:
        if len(l) == 0:
            m.append(r[0])
            r = r[1:]
        elif len(r) == 0:
            m.append(l[0])
            l = l[1:]
        elif l[0] <= r[0]:
            m.append(l[0])
            l = l[1:]
        else:
            m.append(r[0])
            r = r[1:]
    return m


def concurrent_merge_sort(xs: List[int], callback: callable):
    if len(xs) <= 1:
        callback(xs)
    else:
        lc, rc = make(), make()
        go(lambda: concurrent_merge_sort(xs[:len(xs)//2], lambda l:
                                         send(lc, l)))
        go(lambda: concurrent_merge_sort(xs[len(xs)//2:], lambda r:
                                         send(rc, r)))
        receive(lc, lambda l:
                receive(rc, lambda r:
                        callback(merge(l, r))))


def test_concurrent_merge_sort():
    def callback(result):
        assert result == [1, 2, 3, 4, 5]
    concurrent_merge_sort([2, 3, 1, 5, 4], callback)
    run()
