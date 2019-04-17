from typing import Callable, List, Union, Tuple
from .util import remove_all, remove_first, remove_random


class Channel:
    def __init__(self):
        self.closed = False


class SendOperation:
    def __init__(self, channel: Channel, value: any, callback: Callable):
        self.channel = channel
        self.value = value
        self.callback = callback


class ReceiveOperation:
    def __init__(self, channel: Channel, callback: Callable[[any], bool]):
        self.channel = channel
        self.callback = callback


class DefaultOperation:
    def __init__(self, callback: Callable):
        self.callback = callback


Operation = Union[DefaultOperation, ReceiveOperation, SendOperation]


class Scheduler:
    def __init__(self):
        self.execution_queue: List[Callable] = []
        self.blocked: List[Operation] = []

    def go(self, callback: Callable):
        self.execution_queue.append(callback)

    def send(self, channel: Channel, value: any, callback: Callable):
        # "A send on a nil channel blocks forever."
        if channel is not None:
            # "A send on a closed channel proceeds by causing a run-time panic."
            if channel.closed:
                raise Exception("send on closed channel")

            # "A send on an unbuffered channel can proceed if a receiver is ready."
            recv_op = remove_first(self.blocked,
                                   lambda op: type(op) == ReceiveOperation and op.channel == channel)
            if recv_op:
                self.go(lambda: recv_op.callback(value, True))
                self.go(lambda: callback())
                return

        # add the send operation to the blocked list
        send_op = SendOperation(channel, value, callback)
        self.blocked.append(send_op)

    def receive(self, channel: Channel, callback: Callable[[any, bool], None]):
        # "Receiving from a nil channel blocks forever."
        if channel is not None:
            # "if anything is currently blocked on sending for this channel, receive it"
            send_op = remove_first(self.blocked,
                                   lambda op: type(op) == SendOperation and op.channel == channel)
            if send_op:
                self.go(lambda: callback(send_op.value, True))
                self.go(lambda: send_op.callback())
                return

            # "A receive operation on a closed channel can always proceed immediately, yielding the element type's zero value after any previously sent values have been received."
            if channel.closed:
                self.go(lambda: callback(None, False))
                return

        # "The expression blocks until a value is available."
        recv_op = ReceiveOperation(channel, callback)
        self.blocked.append(recv_op)

    def close(self, channel: Channel):
        # if the channel is already closed, we panic
        if channel.closed:
            raise Exception("close of closed channel")

        channel.closed = True

        # complete any blocked receivers
        recv_ops = remove_all(self.blocked,
                              lambda op: type(op) == ReceiveOperation and op.channel == channel)
        for recv_op in recv_ops:
            self.receive(recv_op.channel, recv_op.callback)

        # if there are any blocked senders, we panic
        send_ops = remove_all(self.blocked,
                              lambda op: type(op) == SendOperation and op.channel == channel)
        for send_op in send_ops:
            self.send(send_op.channel, send_op.value, send_op.callback)

    def select(self, cases: List[Operation], callback: Callable):
        def is_ready(op: Operation) -> bool:
            if type(op) == DefaultOperation:
                return False
            elif type(op) == ReceiveOperation:
                return op.channel.closed or filter(lambda send_op: type(send_op) == SendOperation and send_op.channel == op.channel, self.blocked)
            elif type(op) == SendOperation:
                return op.channel.closed or filter(lambda recv_op: type(recv_op) == ReceiveOperation and recv_op.channel == op.channel, self.blocked)

        # if any case is ready, pick one at random and run it
        op = remove_random(cases, is_ready)
        if op:
            if type(op) == ReceiveOperation:
                self.receive(op.channel, op.callback)
            else:
                self.send(op.channel, op.value, op.callback)
            callback()
            return

        # if there's a default case, run that
        op = next((op for op in cases if type(op) == DefaultOperation), None)
        if op:
            op.callback()
            callback()
            return

        def cleanup():
            remove_all(self.blocked, lambda op: op in cases)
            callback()

        for op in cases:
            original = op.callback
            if type(op) == ReceiveOperation:
                op.callback = (
                    lambda value, ok: original(value, ok), cleanup())
            else:
                op.callback = (
                    lambda: original(), cleanup())
            self.blocked.append(op)

    def run(self):
        while self.execution_queue:
            # get the next goroutine off the queue
            f = self.execution_queue.pop(0)
            # run the next goroutine
            f()

        if self.blocked:
            self.blocked = []
            raise Exception("all goroutines are asleep - deadlock!")

        # main exit
