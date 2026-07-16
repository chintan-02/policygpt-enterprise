export function formatDocumentFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "Not available";
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unit = units[0];
  for (let index = 1; value >= 1024 && index < units.length; index += 1) {
    value /= 1024;
    unit = units[index];
  }
  return `${value >= 10 ? value.toFixed(0) : value.toFixed(1)} ${unit}`;
}

export function shortenDocumentId(value: string): string {
  const normalized = value.trim();
  if (normalized.length <= 16) return normalized;
  return `${normalized.slice(0, 8)}…${normalized.slice(-4)}`;
}

export function formatDocumentTimestamp(
  value: string | null | undefined,
  style: "short" | "long" = "long",
): string {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not available";
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: style === "short" ? "medium" : "long",
    timeStyle: style === "short" ? undefined : "short",
  }).format(date);
}

export function formatDocumentCount(value: number | null | undefined): string {
  return value === null || value === undefined
    ? "Not available"
    : new Intl.NumberFormat("en-CA").format(value);
}
