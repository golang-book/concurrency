from random import randint
import builtins


class WaitingQueue(list):
    total = 0

    def enqueue(self, x):
        WaitingQueue.total += 1
        self.append(x)

    def dequeue(self, x=None):
        if x is None:
            x = self.pop(0)
            WaitingQueue.total -= 1
        else:
            # attempt to remove the passed in item from the queue
            idx = self.index(x)
            if idx is not None:
                self.pop(idx)
                WaitingQueue.total -= 1
        return x


class Channel:
    def __init__(self):
        self.closed = False
        self.waiting_to_send = WaitingQueue()
        self.waiting_to_recv = WaitingQueue()


# Scheduling Methods

execution_queue = []


def go(callback):
    if callback:
        execution_queue.append(callback)


def run():
    WaitingQueue.total = 0

    while execution_queue:
        f = execution_queue.pop(0)
        f()

    if WaitingQueue.total > 0:
        raise Exception("fatal error: all goroutines are asleep - deadlock")


# Channel Methods

def make():
    return Channel()


def len(channel):
    return 0


def cap(channel):
    return 0


def send(channel, value, callback):
    # "A send on a nil channel blocks forever."
    if channel is None:
        WaitingQueue.total += 1
        return

    # "A send on a closed channel proceeds by causing a run-time panic."
    if channel.closed:
        raise Exception("send on closed channel")

    # "A send on an unbuffered channel can proceed if a receiver is ready."
    if channel.waiting_to_recv:
        receiver = channel.waiting_to_recv.dequeue()
        go(callback)
        go(lambda: receiver(value, True))
        return

    channel.waiting_to_send.enqueue((value, callback))


def recv(channel, callback):
    # "Receiving from a nil channel blocks forever."
    if channel is None:
        WaitingQueue.total += 1
        return

    # "if anything is currently blocked on sending for this channel, receive it"
    if channel.waiting_to_send:
        value, sender = channel.waiting_to_send.dequeue()
        go(lambda: callback(value, True))
        go(sender)
        return

    # "A receive operation on a closed channel can always proceed immediately,
    # yielding the element type's zero value after any previously sent values have been received."
    if channel.closed:
        go(lambda: callback(None, False))
        return

    channel.waiting_to_recv.enqueue(callback)


def close(channel):
    # if the channel is already closed, we panic
    if channel.closed:
        raise Exception("close of closed channel")

    channel.closed = True

    # complete any senders
    while channel.waiting_to_send:
        value, callback = channel.waiting_to_send.dequeue()
        send(channel, value, callback)

    # complete any receivers
    while channel.waiting_to_recv:
        callback = channel.waiting_to_recv.dequeue()
        recv(channel, callback)


# Selection

# used to indicate the default case in a select
default = object()


def select(cases, callback=None):
    def is_ready(case):
        if case[0] == send:
            return case[1].closed or case[1].waiting_to_recv
        elif case[0] == recv:
            return case[1].closed or case[1].waiting_to_send
        elif case[0] == default:
            return False

    # first see if any of the cases are ready to proceed
    ready = [case for case in cases if is_ready(case)]
    if ready:
        # pick a random one
        case = ready[randint(0, builtins.len(ready)-1)]
        if case[0] == send:
            send(case[1], case[2], case[3])
        elif case[0] == recv:
            recv(case[1], case[2])
        go(callback)
        return

    # next see if there's a default case
    defaults = [case for case in cases if case[0] == default]
    if defaults:
        defaults[0]()
        go(callback)
        return

    # finally we will enqueue each case into the waiting queues
    # we also update each callback so it will cleanup all the
    # other cases so only one is fired

    wrapped = []

    def cleanup():
        for case in wrapped:
            if case[0] == send:
                case[1].waiting_to_send.dequeue((case[2], case[3]))
            elif case[0] == recv:
                case[1].waiting_to_recv.dequeue(case[2])
        go(callback)

    # overwrite all the callbacks and enqueue into the waiting queues
    for case in cases:
        if case[0] == send:
            new_case = (case[0], case[1], case[2],
                        lambda: (cleanup(), case[3]()))
            case[1].waiting_to_send.enqueue((new_case[2], new_case[3]))
            wrapped.append(new_case)
        elif case[0] == recv:
            new_case = (case[0], case[1],
                        lambda value, ok: (cleanup(), case[2](value, ok)))
            case[1].waiting_to_recv.enqueue(new_case[2])
            wrapped.append(new_case)
