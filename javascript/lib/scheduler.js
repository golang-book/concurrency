function remove_all(arr, predicate) {
  let removed = [];
  let idxs = [];
  arr.forEach((op, idx) => {
    if (predicate(op)) {
      removed.push(op);
      idxs.push(idx);
    }
  });
  idxs.reverse().forEach(idx => {
    arr.splice(idx, 1);
  });
  return removed;
}

function remove_random(arr, predicate) {
  let idxs = arr
    .map((op, idx) => (predicate(op) ? idx : -1))
    .filter(idx => idx >= 0);
  if (idxs.length === 0) {
    return undefined;
  }
  let idx = idxs[Math.floor(Math.random() * idxs.length)];
  return arr.splice(idx, 1)[0];
}

export class Channel {
  constructor(capacity) {
    this.capacity = capacity;
    this.closed = false;
    this.buffer = [];
  }
}

export class Operation {
  constructor(method, channel, callback, value = null) {
    this.method = method;
    this.channel = channel;
    this.callback = callback;
    this.value = value;
  }
}

export class Scheduler {
  constructor() {
    this.execution_stack = [];
    this.pending = [];
  }

  go(callback, ...args) {
    this.execution_stack.push(Array.from(arguments));
  }

  submit(operation) {
    switch (operation.method) {
      case "send":
        this.send(operation);
        break;
      case "recv":
        this.recv(operation);
        break;
      case "close":
        this.close(operation);
        break;
    }
  }

  send(operation) {
    let { channel, value, callback } = operation;

    if (channel.closed) {
      throw "send on closed channel";
    }

    // first, if anything is currently waiting, send it immediately
    let receiver = remove_random(
      this.pending,
      op => op.method === "recv" && op.channel === channel
    );
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
    this.pending.push(operation);
  }

  recv(operation) {
    let { channel, callback } = operation;

    if (channel.closed) {
      this.go(callback, undefined, true);
      return;
    }

    // first, if anything is currently waiting, receive it immediately
    let sender = remove_random(
      this.pending,
      op => op.method === "send" && op.channel === channel
    );
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
    this.pending.push(operation);
  }

  close(operation) {
    let { channel } = operation;

    channel.closed = true;

    let pending = remove_all(this.pending, op => op.channel === channel);
    pending.forEach(op => {
      if (op.method === "send") {
        throw "send on closed channel";
      } else {
        this.go(op.callback, undefined, true);
      }
    });
  }

  select(operations, callback) {
    // special case, block forever
    if (operations.length === 0) {
      this.pending.push(new Operation(null, null, null));
      return;
    }

    let ready = operations.filter(op => {
      let { method, channel } = op;
      switch (method) {
        case "send":
          return (
            channel.closed ||
            channel.buffer.length > 0 ||
            this.pending.find(
              op => op.method === "recv" && op.channel === channel
            )
          );
          break;
        case "recv":
          return (
            channel.closed ||
            channel.buffer.length < channel.buffer.capacity ||
            this.pending.find(
              op => op.method === "send" && op.channel === channel
            )
          );
          break;
        default:
          throw "select case must be recv or send";
          break;
      }
    });
    // if one of the operations is ready right now, proceed at random
    if (ready.length > 0) {
      this.submit(removeRandomElement(ready));
      return;
    }

    let pending = [];
    let cleanup = () => {
      pending.forEach(op => remove_all(this.pending, o => o === op));
      callback();
    };

    // if nothing is ready we're going to have to wait
    operations.forEach(op => {
      let { callback } = op;
      op.callback = () => {
        callback();
        cleanup();
      };
      this.pending.push(op);
      pending.plush(op);
    });
  }

  run() {
    while (true) {
      let ctx = this.execution_stack.shift();
      if (!ctx) {
        if (this.pending.length == 0) {
          // main exit
          return;
        }
        throw "all goroutines are asleep - deadlock!";
      }
      ctx[0].apply(null, ctx.slice(1));
    }
  }
}

let instance = new Scheduler();

export { instance };
