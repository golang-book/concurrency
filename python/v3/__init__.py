from dataclasses import dataclass
from .scheduler import Channel, ReceiveOperation, Scheduler, SendOperation, DefaultOperation, Operation
from inspect import signature
from typing import List, Tuple


global_scheduler = Scheduler()


def go(callback: callable) -> None:
    global_scheduler.go(callback)


def make() -> Channel:
    return Channel()


def len(channel: Channel) -> int:
    return 0


def cap(channel: Channel) -> int:
    return 0


def send(channel: Channel, value: any, callback: callable = None) -> None:
    callback = callback or (lambda: None)
    global_scheduler.send(channel, value, callback)


def receive(channel: Channel, callback: callable) -> None:
    if callback:
        # support functions which only have a single argument
        if callback.__code__.co_argcount == 1:
            original = callback
            callback = (lambda value, ok: original(value))
    else:
        callback = (lambda value, ok: None)
    global_scheduler.receive(channel, callback)


def close(channel: Channel) -> None:
    global_scheduler.close(channel)


def select(cases: List[Tuple], callback: callable = None) -> None:
    callback = callback or (lambda: None)

    def to_op(case: Tuple) -> Operation:
        if case[0] == "send":
            return SendOperation(case[1], case[2], case[3])
        elif case[0] == "receive":
            return ReceiveOperation(case[1], case[2])
        elif case[0] == "default":
            return DefaultOperation(case[1])
        else:
            raise Exception(
                "invalid select case:{}".format(case))

    global_scheduler.select([to_op(case) for case in cases], callback)


def run() -> None:
    global_scheduler.run()
