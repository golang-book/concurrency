import { close, send, make, run, go, recv } from "./sync";

test("unbuffered", done => {
  go(() => {
    let ch = make();
    go(() => {
      send(ch, 5);
    });
    go(() => {
      recv(ch, (value, closed) => {
        expect(value).toBe(5);
        expect(closed).toBe(false);
        done();
      });
    });
  });
  run();
});

test("close unblocks recv", done => {
  go(() => {
    let ch = make();
    go(() => {
      recv(ch, (value, closed) => {
        expect(value).toBe(undefined);
        expect(closed).toBe(true);
        done();
      });
    });
    go(() => {
      close(ch);
    });
  });
  run();
});

test("close panics on send", done => {
  go(() => {
    let ch = make();
    close(ch);
    go(() => {
      expect(() => {
        send(ch, 5);
      }).toThrow();
      done();
    });
  });
  run();
});
