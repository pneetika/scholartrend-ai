export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function formatScore(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function durationLabel(startedAt: string, completedAt: string): string {
  const durationMs = Math.max(0, new Date(completedAt).getTime() - new Date(startedAt).getTime());
  if (durationMs < 1_000) {
    return `${durationMs} ms`;
  }
  return `${(durationMs / 1_000).toFixed(1)} s`;
}

