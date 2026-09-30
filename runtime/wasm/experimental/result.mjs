// ABI v2 adapter. Guest status is independent of candidate result text.
export function readResult(ex, length, outputBytes, status) {
  const failures = { 1: "guest-input", 2: "guest-parse", 3: "guest-step-limit", 4: "output-limit", 5: "guest-resource-limit", 6: "guest-limits" };
  if (status !== 0) return { status: "refused", reason: failures[status] || "guest-status-unknown" };
  const op = ex.output_ptr();
  if (!Number.isInteger(length) || length < 0 || op < 0 || op + length > ex.memory.buffer.byteLength)
    return { status: 'failed', reason: 'guest-output-range' };
  // Independent host bound; typed guest overflow is handled above.
  if (length >= 16777215 || length > outputBytes)
    return { status: 'refused', reason: 'output-limit' };
  try {
    const output = new TextDecoder('utf-8', { fatal: true }).decode(new Uint8Array(ex.memory.buffer, op, length));
    return { status: 'candidate', output, interactions: ex.last_interactions() };
  } catch { return { status: 'failed', reason: 'guest-output-encoding' }; }
}
