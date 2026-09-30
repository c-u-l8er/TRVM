import { createReducerHost, LIMITS } from './host.mjs';

// Streaming input cap prevents the CLI from buffering an unbounded request.
let size = 0, chunks = [], refused = false;
for await (const chunk of process.stdin) {
  size += chunk.length;
  if (size > LIMITS.inputBytes) { refused = true; break; }
  chunks.push(chunk);
}
if (refused) {
  console.log(JSON.stringify({ status: 'refused', reason: 'input-limit' }));
  process.exitCode = 2;
} else {
  try {
    const input = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks));
    const result = await createReducerHost().reduce(input);
    console.log(JSON.stringify(result));
    process.exitCode = result.status === 'candidate' ? 0 : 2;
  } catch {
    console.log(JSON.stringify({ status: 'failed', reason: 'host-initialization-or-input-encoding' }));
    process.exitCode = 2;
  }
}
