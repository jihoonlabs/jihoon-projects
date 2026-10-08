export function getProjectBorderColor(projectKey: string | null): string | null {
  if (!projectKey?.trim()) return null;

  // Derive the accent from the immutable key so renames and reloads keep it stable.
  let hash = 2166136261;
  for (const character of projectKey.trim().toUpperCase()) {
    hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  }

  return `hsl(${(hash >>> 0) % 360} 42% 80%)`;
}
