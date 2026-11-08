/**
 * 要求の中断（AbortError）かを判定する。
 * fetch の中断や protectedRequest の中断は DOMException で届き、実行環境によっては Error を継承しないため、
 * instanceof ではなく name で判定する。
 */
export function isAbortError(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'name' in error &&
    error.name === 'AbortError'
  );
}
