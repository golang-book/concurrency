import asyncio
from . import Channel, select, send, make, close, recv, go


async def copy(dst, src):
    while True:
        value, ok = await recv(src)
        if not ok:
            break
        await send(dst, value)
    close(dst)


async def fanin(dst, src1, src2):
    done1, done2 = False, False
    while True:
        if done1 and done2:
            break
        if done1:
            await copy(dst, src2)
            done2 = True
        elif done2:
            await copy(dst, src1)
            done1 = True
        else:
            async def f1(value, ok):
                nonlocal done1
                if not ok:
                    done1 = True
                else:
                    await send(dst, value)

            async def f2(value, ok):
                nonlocal done2
                if not ok:
                    done2 = True
                else:
                    await send(dst, value)

            await select([
                (recv, src1, f1),
                (recv, src2, f2),
            ])


async def sendall(dst, xs):
    for x in xs:
        await send(dst, x)
    close(dst)


async def recvall(src):
    values = []
    while True:
        value, ok = await recv(src)
        if not ok:
            break
        values.append(value)
    return values


def test_select():
    async def main():
        c1, c2, c3 = make(), make(), make()
        go(sendall(c2, [1, 2, 3]))
        go(sendall(c3, [4, 5, 6]))
        go(fanin(c1, c2, c3))

        result = await recvall(c1)
        assert [x for x in sorted(result)] == [1, 2, 3, 4, 5, 6]
    asyncio.run(main())
