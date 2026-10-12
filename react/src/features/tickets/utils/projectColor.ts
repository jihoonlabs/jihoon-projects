function getProjectHue(projectKey: string | null): number | null {
  if (!projectKey?.trim()) return null;

  // Derive the accent from the immutable key so renames and reloads keep it stable.
  let hash = 2166136261;
  for (const character of projectKey.trim().toUpperCase()) {
    hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  }
  return (hash >>> 0) % 360;
}

export function getProjectBorderColor(
  projectKey: string | null,
): string | null {
  const hue = getProjectHue(projectKey);
  return hue === null ? null : `hsl(${hue} 42% 80%)`;
}

export function getProjectBackgroundColor(
  projectKey: string | null,
): string | null {
  const hue = getProjectHue(projectKey);
  return hue === null ? null : `hsl(${hue} 42% 94%)`;
}
