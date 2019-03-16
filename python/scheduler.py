from dataclasses import dataclass
from typing import Callable, List
from random import randint


def remove_all(arr: List, predicate: Callable[any, bool]):
    removed = [(idx, el) for idx, el in enumerate(arr) if predicate(el)]
    for idx, _ in reversed(removed):
        arr.pop(idx)
    return [el for _, el in removed]


def remove_random(arr: List, predicate: Callable[any, bool]):
    idxs = [idx for idx, el in enumerate(arr) if predicate(el)]
    if len(idxs) == 0:
        return None
    idx = idxs[randint(0, len(idxs))]
    return arr.pop(idx)


@dataclass
class Channel:
    capacity: int
    closed: bool
    buffer: List


@dataclass
class Operation:
    method: str
    channel: Channel
    callback: Callable
    value: any


class Scheduler(object):
    def __init__(self):
        self.execution_stack = []
        self.pending: List[Operation] = []

    def go(self, callback: Callable, *args):
        self.execution_stack.append([callback] + args)

    def submit(self, operation: Operation):
        if operation.method == "send":
            self.send(operation)
        elif operation.method == "recv":
            self.recv(operation)
        elif operation.method == "close":
            self.close(operation)

    def send(self, operation: Operation):
        channel, value, callback = operation.channel, operation.value, operation.callback

        if channel.closed:
            raise "send on closed channel"

        receiver = remove_random(
            self.pending, lambda op: op.method == "recv" and op.channel == channel)
        if receiver:
            self.go(receiver.callback, value, False)
            self.go(callback)
            return

        if len(channel.buffer) < channel.capacity:
            channel.buffer.append(value)
            self.go(callback)
            return

        self.pending.append(operation)

    def recv(self, operation: Operation):
        pass

    def close(self, operation: Operation):
        pass

    def select(self, operations: List[Operation], callback: Callable):
        pass

    def run(self):
        pass
