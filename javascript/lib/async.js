import * as sync from "./sync";
export let make = sync.make;
export let len = sync.len;
export let cap = sync.cap;
export let close = sync.close;
export let run = sync.run;
export async function go(callback, ...args) {
  sync.go(callback, ...args);
}
export async function send(channel, value) {
  await new Promise((resolve, reject) => {
    sync.send(channel, value, resolve);
  });
}
export async function recv(channel) {
  return await new Promise((resolve, reject) => {
    sync.recv(channel, (value, closed) => resolve([value, closed]));
  });
}
export async function select(cases) {
  await new Promise((resolve, reject) => {
    sync.select(cases, resolve);
  });
}
