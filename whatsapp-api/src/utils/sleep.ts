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
 * Pauses between 45–90 seconds.
 */
export function coffeBreakSleep(): Promise<void> {
  const delay = Math.floor(Math.random() * 45000) + 45000;
  console.log(`   ☕ Taking a break for ${(delay / 1000).toFixed(0)}s...`);
  return new Promise((resolve) => setTimeout(resolve, delay));
}
