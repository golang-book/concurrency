from random import randint
import builtins
import asyncio


class WaitingQueue(list):
    def enqueue(self, x):
        self.append(x)

    def dequeue(self, x=None):
        if x is None:
            x = self.pop(0)
        else:
            # attempt to remove the passed in item from the queue
            idx = self.index(x)
            if idx is not None:
                self.pop(idx)
        return x


class Channel:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = []
        self.closed = False
        self.waiting_to_send = WaitingQueue()
        self.waiting_to_recv = WaitingQueue()


# Scheduling Methods

def go(task):
    if task:
        asyncio.create_task(task)


# Channel Methods

def make(capacity=0):
    return Channel(capacity)


def len(channel):
    return builtins.len(channel.buffer)


def cap(channel):
    return channel.capacity


async def send(channel, value):
    # "A send on a nil channel blocks forever."
    if channel is None:
        await asyncio.Future()

    # "A send on a closed channel proceeds by causing a run-time panic."
    if channel.closed:
        raise Exception("send on closed channel")

    # "A send on an unbuffered channel can proceed if a receiver is ready."
    if channel.waiting_to_recv:
        future = channel.waiting_to_recv.dequeue()
        future.set_result((value, True))
        return

    # "A send on a buffered channel can proceed if there is room in the buffer."
    if len(channel) < cap(channel):
        channel.buffer.append(value)
        return

    future = asyncio.Future()
    channel.waiting_to_send.enqueue((value, future))
    await future


async def recv(channel):
    # "Receiving from a nil channel blocks forever."
    if channel is None:
        await asyncio.Future()

    # if there is a value in the buffer, receive it
    if len(channel) > 0:
        # pop the first element, because:
        # "Channels act as first-in-first-out queues.
        # For example, if one goroutine sends values on a channel and
        # a second goroutine receives them,
        # the values are received in the order sent. "
        value = channel.buffer.pop(0)
        return value, True

    # "if anything is currently blocked on sending for this channel, receive it"
    if channel.waiting_to_send:
        value, future = channel.waiting_to_send.dequeue()
        future.set_result(None)
        return value, True

    # "A receive operation on a closed channel can always proceed immediately,
    # yielding the element type's zero value after any previously sent values have been received."
    if channel.closed:
        return None, False

    future = asyncio.Future()
    channel.waiting_to_recv.enqueue(future)
    value, ok = await future
    return value, ok


def close(channel):
    # if the channel is already closed, we panic
    if channel.closed:
        raise Exception("close of closed channel")

    channel.closed = True

    # complete any senders
    while channel.waiting_to_send:
        _, future = channel.waiting_to_send.dequeue()
        future.set_exception(Exception("send on closed channel"))

    # complete any receivers
    while channel.waiting_to_recv:
        future = channel.waiting_to_recv.dequeue()
        future.set_result((None, False))


# Selection

# used to indicate the default case in a select
default = object()


async def select(cases):
    # block forever
    if builtins.len(cases) == 0:
        await asyncio.Future()

    def is_ready(case):
        if case[0] == send:
            return case[1].closed or len(case[1]) < cap(case[1]) or case[1].waiting_to_recv
        elif case[0] == recv:
            return case[1].closed or len(case[1]) > 0 or case[1].waiting_to_send
        elif case[0] == default:
            return False

    # first see if any of the cases are ready to proceed
    ready = [case for case in cases if is_ready(case)]
    if ready:
        # pick a random one
        case = ready[randint(0, builtins.len(ready)-1)]
        if case[0] == send:
            await send(case[1], case[2])
            await case[3]()
        elif case[0] == recv:
            value, ok = await recv(case[1])
            await case[2](value, ok)
        return

    # next see if there's a default case
    defaults = [case for case in cases if case[0] == default]
    if defaults:
        await defaults[0]()
        return

    # finally we will enqueue each case into the waiting queues
    # we also update each callback so it will cleanup all the
    # other cases so only one is fired

    futures = []
    for case in cases:
        future = asyncio.Future()
        if case[0] == send:
            case[1].waiting_to_send.enqueue((case[2], future))
        elif case[0] == recv:
            case[1].waiting_to_recv.enqueue(future)

    # wait for one to complete
    done, _ = asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED)

    # remove the others
    for i, case in enumerate(cases):
        future = futures[i]
        if case[0] == send:
            case[1].waiting_to_send.dequeue((case[2], future))
        elif case[0] == recv:
            case[1].waiting_to_recv.dequeue(future)

    for i, future in enumerate(futures):
        if future == done[0]:
            if cases[i][0] == send:
                await future
                await cases[i][3]()
            elif cases[i][0] == recv:
                value, ok = await future
                await cases[i][2](value, ok)
