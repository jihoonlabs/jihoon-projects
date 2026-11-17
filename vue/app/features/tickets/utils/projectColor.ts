/**
 * サーバーに保存されたプロジェクトの色を、安全に使える #RRGGBB のときだけ返す。
 * 色がない古いデータや不正な値は中立（null）のままにし、名前やキーから色を作らない。
 */
export function getProjectBorderColor(
  projectColor: string | null,
): string | null {
  return projectColor && /^#[0-9a-f]{6}$/i.test(projectColor)
    ? projectColor
    : null;
}
