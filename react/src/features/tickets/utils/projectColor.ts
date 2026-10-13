// Missing colors stay neutral while older API clients are upgraded; never hash keys.
export function getProjectBorderColor(
  projectColor: string | null,
): string | null {
  return projectColor && /^#[0-9a-f]{6}$/i.test(projectColor)
    ? projectColor
    : null;
}
