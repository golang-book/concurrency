from . import Channel, select, send, make, close, receive, go, run


def copy(dst: Channel, src: Channel):
    def onreceive(value, ok):
        if ok:
            send(dst, value, lambda: copy(dst, src))
        else:
            close(dst)
    receive(src, onreceive)


def fanin(dst: Channel, src1: Channel, src2: Channel):
    def onreceive1(value, ok):
        if ok:
            send(dst, value, lambda: fanin(dst, src1, src2))
        else:
            copy(dst, src2)

    def onreceive2(value, ok):
        if ok:
            send(dst, value, lambda: fanin(dst, src1, src2))
        else:
            copy(dst, src1)

    select([
        ("receive", src1, onreceive1),
        ("receive", src2, onreceive2),
    ])


def sendall(dst: Channel, xs: list):
    if xs:
        send(dst, xs[0], lambda: sendall(dst, xs[1:]))
    else:
        close(dst)


def receiveall(src: Channel, callback):
    values = []

    def onreceive(value, ok):
        if ok:
            values.append(value)
            receive(src, onreceive)
        else:
            callback(values)
    receive(src, onreceive)


def test_select():
    def callback(result):
        assert [x for x in sorted(result)] == [1, 2, 3, 4, 5, 6]

    c1, c2, c3 = make(), make(), make()
    go(lambda: sendall(c2, [1, 2, 3]))
    go(lambda: sendall(c3, [4, 5, 6]))
    go(lambda: fanin(c1, c2, c3))
    go(lambda: receiveall(c1, callback))
    run()
