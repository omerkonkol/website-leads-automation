/**
 * Pause execution for a random duration between min and max milliseconds.
 * Defaults mimic real human typing/reading pace (8–25 seconds).
 */
export function randomSleep(
  minMs: number = 8000,
  maxMs: number = 25000
): Promise<void> {
  const delay = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
  console.log(`   ⏳ Waiting ${(delay / 1000).toFixed(1)}s before next message...`);
  return new Promise((resolve) => setTimeout(resolve, delay));
}

/**
 * Longer "coffee break" pause every N messages to look natural.
 * Defaults to 45–90 seconds; pass min/max to override.
 */
export function coffeBreakSleep(
  minMs: number = 45000,
  maxMs: number = 90000
): Promise<void> {
  const delay = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
  console.log(`   ☕ Taking a break for ${(delay / 1000).toFixed(0)}s...`);
  return new Promise((resolve) => setTimeout(resolve, delay));
}
