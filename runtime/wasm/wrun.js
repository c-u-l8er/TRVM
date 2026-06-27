// wrun.js -- Node host for ic32.wasm. Reads a term on stdin, prints the normal
// form on stdout and "interactions=N" on stderr.  usage: echo 'TERM' | node wrun.js
const fs = require("fs");

const bytes = fs.readFileSync(__dirname + "/ic32.wasm");
const input = fs.readFileSync(0);                 // all of stdin (UTF-8 bytes)

WebAssembly.instantiate(bytes, {}).then(({ instance }) => {
  const ex = instance.exports;
  const mem = ex.memory;

  const inPtr  = ex.input_ptr();
  const outPtr = ex.output_ptr();

  // strip trailing whitespace/newline
  let n = input.length;
  while (n > 0 && (input[n-1] === 10 || input[n-1] === 13 || input[n-1] === 32 || input[n-1] === 9)) n--;

  // grow memory if the buffers moved past current size (they won't here, but be safe)
  const heapU8 = new Uint8Array(mem.buffer);
  heapU8.set(input.subarray(0, n), inPtr);

  const outLen = ex.run(n);
  const out = Buffer.from(mem.buffer, outPtr, outLen).toString("utf8");

  process.stdout.write(out + "\n");
  process.stderr.write("interactions=" + ex.last_interactions() + "\n");
}).catch(e => { process.stderr.write("WASM-ERR " + e.message + "\n"); process.exit(1); });
