from . import Channel, select, send, make, close, recv, go, run


def copy(dst: Channel, src: Channel):
    def onrecv(value, ok):
        if ok:
            send(dst, value, lambda: copy(dst, src))
        else:
            close(dst)
    recv(src, onrecv)


def fanin(dst: Channel, src1: Channel, src2: Channel):
    def onrecv1(value, ok):
        if ok:
            send(dst, value, lambda: fanin(dst, src1, src2))
        else:
            copy(dst, src2)

    def onrecv2(value, ok):
        if ok:
            send(dst, value, lambda: fanin(dst, src1, src2))
        else:
            copy(dst, src1)

    select([
        (recv, src1, onrecv1),
        (recv, src2, onrecv2),
    ])


def sendall(dst: Channel, xs: list):
    if xs:
        send(dst, xs[0], lambda: sendall(dst, xs[1:]))
    else:
        close(dst)


def recvall(src: Channel, callback):
    values = []

    def onrecv(value, ok):
        if ok:
            values.append(value)
            recv(src, onrecv)
        else:
            callback(values)
    recv(src, onrecv)


def test_select():
    def callback(result):
        assert [x for x in sorted(result)] == [1, 2, 3, 4, 5, 6]

    c1, c2, c3 = make(), make(), make()
    go(lambda: sendall(c2, [1, 2, 3]))
    go(lambda: sendall(c3, [4, 5, 6]))
    go(lambda: fanin(c1, c2, c3))
    go(lambda: recvall(c1, callback))
    run()
