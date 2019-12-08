from . import select, send, make, close, recv, go, run


def test_buffering():
    def callback(value, ok):
        assert value == 1

    ch = make(3)
    go(lambda: send(ch, 1, lambda: send(ch, 2, lambda: send(ch, 3, lambda: close(ch)))))
    go(lambda: recv(ch, callback))
    run()
