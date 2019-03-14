function removeRandomElement(arr) {
  // pick an element randomly
  let idx = Math.floor(Math.random() * arr.length);
  return arr.splice(idx, 1);
}

class Channel {
  constructor(capacity) {
    this.capacity = capacity;
    this.closed = false;
    this.buffer = [];
  }
}

class PendingOperation {
  constructor(method, channel, callback, value = null) {
    this.method = method;
    this.channel = channel;
    this.callback = callback;
    this.value = value;
  }
}

class PendingOperationCollection {
  constructor() {
    this.list = [];
  }

  add(op) {
    this.list.push(op);
  }

  contains(method, channel) {
    return (
      this.list.findIndex(
        op => op.method === method && op.channel === channel
      ) >= 0
    );
  }

  next(method, channel) {
    let idxs = [];
    this.list.forEach((op, idx) => {
      if (op.method === method && op.channel === channel) {
        idxs.push(idx);
      }
    });
    if (idxs.length === 0) {
      return undefined;
    }
    let idx = removeRandomElement(idxs);
    return this.list.splice(idx, 1);
  }

  remove_all(predicate) {
    let removed = [];
    let kept = [];
    this.list.forEach(op => {
      if (predicate(op)) {
        removed.push(op);
      } else {
        kept.push(op);
      }
    });
    this.list = kept;
    return this.removed;
  }
}

class Scheduler {
  constructor() {
    this.execution_stack = [];
    this.pending = new PendingOperationCollection();
  }

  go(/* ... args */) {
    let args = Array.from(arguments);
    this.execution_stack.push(args);
  }

  make(capacity) {
    return new Channel(capacity);
  }

  len(channel) {
    return channel.buffer.length;
  }

  cap(channel) {
    return channel.capacity;
  }

  send(channel, value, callback) {
    callback = callback || (() => {});

    if (channel.closed) {
      throw "send on closed channel";
    }

    // first, if anything is currently waiting, send it immediately
    let receiver = this.pending.next("recv", channel);
    if (receiver) {
      this.go(receiver.callback, value, false);
      this.go(callback);
      return;
    }

    // next, if the channel is buffered and there's room left in the buffer, store it immediately
    if (channel.buffer.length < channel.capacity) {
      channel.buffer.push(value);
      this.go(callback);
      return;
    }

    // finally, we need to block, so push onto the senders queue
    this.pending.add(new PendingOperation("send", channel, callback, value));
  }

  recv(channel, callback) {
    callback = callback || (() => {});

    if (channel.closed) {
      this.go(callback, undefined, true);
      return;
    }

    // first, if anything is currently waiting, receive it immediately
    let sender = this.pending.next("send", channel);
    if (sender) {
      this.go(callback, sender.value, false);
      this.go(sender.callback);
      return;
    }

    // next, if the channel is buffered and there's values in the buffer, receive them immediately
    if (channel.buffer.length > 0) {
      let value = channel.buffer.shift();
      this.go(callback, value, false);
      return;
    }

    // finally, we need to block, so push onto the receivers queue
    this.pending.add(new PendingOperation("recv", channel, callback));
  }

  close(channel) {
    channel.closed = true;

    let pending = this.pending.remove_all(op => op.channel === channel);
    pending.forEach(op => {
      if (op.method === "send") {
        throw "send on closed channel";
      } else {
        this.go(op.callback, undefined, true);
      }
    });
  }

  select(cases = []) {
    // special case, block forever
    if (cases.length === 0) {
      this.pending.add(new PendingOperation(null, null, null));
    }

    let ready = cases.filter(args => {
      let method = args[0];
      let channel = args[1];
      if (method === "send") {
        return (
          channel.closed ||
          channel.buffer.length > 0 ||
          this.pending.contains("recv", channel)
        );
      } else if (method === "recv") {
        return (
          channel.closed ||
          channel.buffer.length < channel.buffer.capacity ||
          this.pending.contains("send", channel)
        );
      } else {
        throw "select case must be recv or send";
      }
    });
    // if one of the cases is ready right now, proceed at random
    if (ready.length > 0) {
      let op = removeRandomElement(ready);
      if (op.method === "send") {
        this.send(op.channel, op.value, op.callback);
      } else if (op.method === "recv") {
        this.recv(op.channel, op.callback);
      }
      return;
    }

    let pendingCases = [];
    let cleanup = () => {
      pendingCases.forEach(cb =>
        this.pending.remove_all(op => op.callback === cb)
      );
    };

    // if nothing is ready we're going to have to wait
    cases.forEach(args => {
      let method = args[0];
      let channel = args[1];
      if (method === "send") {
        let value = args[2];
        let callback = args[3];
        let wrapper = () => {
          cleanup();
          callback();
        };
        this.pending.push(
          new PendingOperation(method, channel, wrapper, value)
        );
        pendingCases.push(wrapper);
      } else if (method === "recv") {
        let callback = args[2];
        let wrapper = (value, closed) => {
          cleanup();
          callback(value, closed);
        };
        this.pending.push(new PendingOperation(method, channel, wrapper));
        pendingCases.push(wrapper);
      }
    });
  }

  run() {
    while (true) {
      let ctx = this.execution_stack.shift();
      if (!ctx) {
        if (this.pending.list.length == 0) {
          // main exit
          return;
        }
        throw "all goroutines are asleep - deadlock!";
      }
      ctx[0].apply(null, ctx.slice(1));
    }
  }
}

let sch = new Scheduler();
sch.go(() => {
  let ch = sch.make(3);
  sch.send(ch, 5, () => {
    sch.send(ch, 7, () => {
      sch.send(ch, 8, () => {
        sch.recv(ch, (value, closed) => {
          console.log("VALUE", value);
        });
      });
    });
  });
});
sch.run();
