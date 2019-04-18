import asyncio
from . import go, make, recv, send


def merge(l, r):
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


async def concurrent_merge_sort(xs):
    if len(xs) <= 1:
        return xs
    else:
        lc, rc = make(), make()

        async def left():
            value = await concurrent_merge_sort(xs[:len(xs)//2])
            await send(lc, value)
        go(left())

        async def right():
            value = await concurrent_merge_sort(xs[len(xs)//2:])
            await send(rc, value)
        go(right())

        l, _ = await recv(lc)
        r, _ = await recv(rc)
        return merge(l, r)


def test_concurrent_merge_sort():
    async def main():
        result = await concurrent_merge_sort([2, 3, 1, 5, 4])
        assert result == [1, 2, 3, 4, 5]
    asyncio.run(main())
