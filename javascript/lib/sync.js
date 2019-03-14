import { instance as scheduler, Channel, Operation } from "./scheduler";

export function go(callback, ...args) {
  scheduler.go(callback, ...args);
}
export function make(capacity) {
  return new Channel(capacity || 0);
}
export function len(channel) {
  return channel.buffer.length;
}
export function cap(channel) {
  return channel.capacity;
}
export function send(channel, value, callback) {
  scheduler.submit(
    new Operation("send", channel, callback || (() => {}), value)
  );
}
export function recv(channel, callback) {
  scheduler.submit(
    new Operation("recv", channel, callback || (() => {}), undefined)
  );
}
export function close(channel) {
  scheduler.submit(new Operation("close", channel, undefined, undefined));
}
export function select(cases, callback) {
  scheduler.select(
    cases.map(c => {
      let op = new Operation(c[0], c[1], c[2], null);
      if (op.method === "send") {
        op.value = c[2];
        op.callback = c[3];
      }
      return op;
    }),
    callback || (() => {})
  );
}
export function run() {
  scheduler.run();
}
