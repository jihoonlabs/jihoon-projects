#!/usr/bin/env bash
# CI（GitHub Actions）と同じ検査をローカルで実行する。
#
# 使い方:
#   scripts/ci-check.sh            変更のある領域だけを検査（比較元は origin/main）
#   scripts/ci-check.sh react      react/ を検査
#   scripts/ci-check.sh vue        vue/ を検査
#   scripts/ci-check.sh laravel    laravel/ を検査
#   scripts/ci-check.sh all        すべて検査
#
# 環境変数:
#   CI_CHECK_BASE   変更を判定する比較元（既定: origin/main）
#
# 依存関係はインストール済みであることを前提とし、ここではインストールしない。

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="${CI_CHECK_BASE:-origin/main}"
# Laravel のテストは .env がなくても動くよう、CI と同じテスト用キーを使う（既存の .env は変更しない）
TEST_APP_KEY='base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='

results=()
failed=0

run() {
  local label="$1" dir="$2"
  shift 2

  printf '\n== %s\n' "$label"
  if (cd "$ROOT/$dir" && "$@"); then
    results+=("OK  $label")
  else
    results+=("NG  $label")
    failed=1
  fi
}

check_react() {
  run 'React: テスト' react pnpm test:run
  run 'React: Lint' react pnpm exec eslint .
  run 'React: 型チェック' react pnpm exec tsc --noEmit
  run 'React: 静的ビルド' react env TICKET_STATIC_EXPORT=true \
    NEXT_PUBLIC_API_URL= NEXT_PUBLIC_DEMO_MODE=true pnpm build
}

check_vue() {
  run 'Vue: テスト' vue pnpm test:run
  run 'Vue: Lint' vue pnpm lint
  run 'Vue: 型チェック' vue pnpm typecheck
  run 'Vue: 整形' vue pnpm format:check
  run 'Vue: 静的生成' vue env NUXT_PUBLIC_API_URL= \
    NUXT_PUBLIC_DEMO_MODE=true pnpm generate
}

check_laravel() {
  # CI はファイルを指定して整形を確認する。ローカルでは比較元からの変更ファイルを対象にする
  run 'Laravel: 整形（変更ファイル）' laravel vendor/bin/pint --test --diff="$BASE"

  if [ -f "$ROOT/laravel/.env" ]; then
    run 'Laravel: テスト' laravel php artisan test
  else
    run 'Laravel: テスト' laravel env APP_KEY="$TEST_APP_KEY" php artisan test
  fi
}

# 比較元からの差分と作業ツリーの変更を合わせ、変更のある領域を返す
changed_areas() {
  {
    git -C "$ROOT" diff --name-only "$BASE"...HEAD 2>/dev/null
    git -C "$ROOT" diff --name-only HEAD
    git -C "$ROOT" ls-files --others --exclude-standard
  } | cut -d/ -f1 | sort -u | grep -E '^(react|vue|laravel)$' || true
}

target="${1:-changed}"

case "$target" in
  react) check_react ;;
  vue) check_vue ;;
  laravel) check_laravel ;;
  all)
    check_react
    check_vue
    check_laravel
    ;;
  changed)
    areas="$(changed_areas)"
    if [ -z "$areas" ]; then
      echo "比較元 $BASE から react/・vue/・laravel/ に変更はありません。"
      exit 0
    fi
    for area in $areas; do
      "check_$area"
    done
    ;;
  *)
    echo "使い方: $0 [react|vue|laravel|all]" >&2
    exit 2
    ;;
esac

printf '\n== 結果\n'
printf '%s\n' "${results[@]}"

exit "$failed"
