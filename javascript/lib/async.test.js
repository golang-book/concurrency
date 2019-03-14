import { close, send, make, run, go, recv } from "./async";

test("unbuffered", done => {
  go(() => {
    let ch = make();
    go(async () => {
      await send(ch, 5);
    });
    go(async () => {
      let [value, closed] = await recv(ch);
      expect(value).toBe(5);
      expect(closed).toBe(false);
      done();
    });
  });
  run();
});

test("close unblocks recv", done => {
  go(() => {
    let ch = make();
    go(async () => {
      let [value, closed] = await recv(ch);
      expect(value).toBe(undefined);
      expect(closed).toBe(true);
      done();
    });
    go(() => {
      close(ch);
    });
  });
  run();
});

test("close panics on send", done => {
  go(async () => {
    let ch = make();
    close(ch);
    send(ch, 5).catch(e => {
      expect(e).toBe("send on closed channel");
      done();
    });
  });
  run();
});
