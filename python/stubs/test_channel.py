from . import go, make, run, send


def test_send_on_nil_channel():
    ch = None
    go(lambda: send(ch, 5, lambda: None))
    raised = False
    try:
        run()
    except:
        raised = True
    assert raised
