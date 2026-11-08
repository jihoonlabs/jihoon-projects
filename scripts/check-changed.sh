#!/usr/bin/env bash
# CI（GitHub Actions）と同じ検査をローカルで実行する。
#
# 使い方:
#   scripts/check-changed.sh            変更のある領域だけを検査（比較元は origin/main）
#   scripts/check-changed.sh react      react/ を検査
#   scripts/check-changed.sh vue        vue/ を検査（vue/package.json があるコミットのみ）
#   scripts/check-changed.sh laravel    laravel/ を検査
#   scripts/check-changed.sh all        すべて検査（Vue アプリがなければ SKIP と表示し、未実行として判定に残す）
#
# 環境変数:
#   CI_CHECK_BASE   変更を判定する比較元（既定: origin/main）
#
# CI との違い: Laravel の整形確認は、CI が指定する固定ファイルではなく比較元からの変更ファイルを対象にする。
# 依存関係はインストール済みであることを前提とし、ここではインストールしない。
# 比較元を判定できないときは、検査を省略して成功扱いにせず終了コード 2 で止める。
# macOS 標準の Bash 3.2 でも動くよう、mapfile など新しい構文は使わない。

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="${CI_CHECK_BASE:-origin/main}"
# Laravel のテストは .env がなくても動くよう、CI と同じテスト用キーを使う（既存の .env は変更しない）
TEST_APP_KEY='base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='

results=()
failed=0

stop() {
  echo "check-changed: $1" >&2
  exit 2
}

run() {
  local label="$1" dir="$2"
  shift 2

  printf '\n== %s\n' "$label"
  if (cd "$ROOT/$dir" && "$@"); then
    results+=("OK    $label")
  else
    results+=("NG    $label")
    failed=1
  fi
}

skip() {
  printf '\n== %s\n%s\n' "$1" "$2"
  results+=("SKIP  $1（$2）")
}

# 比較元を使う前に、Git 管理下であること・比較元が存在すること・共通祖先があることを確かめる
require_base() {
  git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
    stop 'Git 管理下のリポジトリで実行してください。'
  git -C "$ROOT" rev-parse --verify --quiet "${BASE}^{commit}" >/dev/null ||
    stop "比較元 $BASE が見つかりません。git fetch するか CI_CHECK_BASE を指定してください。"
  git -C "$ROOT" merge-base "$BASE" HEAD >/dev/null 2>&1 ||
    stop "比較元 $BASE と HEAD の共通祖先が見つかりません（浅い clone の可能性があります）。"
}

# 比較元からのコミット済み変更と、作業ツリー・ステージ・未追跡の変更を、リポジトリ相対パスで CHANGED に集める（重複なし）。
# Git は日本語や空白を含むパスを引用符とエスケープ付きで出力するため、-z（NUL 区切り）で受け取って生のパスのまま扱う。
CHANGED=()
collect_changed_files() {
  local list file known seen

  require_base
  list="$(mktemp)" || stop '一時ファイルを作成できませんでした。'
  if ! {
    git -C "$ROOT" diff -z --name-only "$BASE"...HEAD &&
      git -C "$ROOT" diff -z --name-only HEAD &&
      git -C "$ROOT" ls-files -z --others --exclude-standard
  } > "$list"; then
    rm -f "$list"
    stop '変更ファイルを取得できませんでした。'
  fi

  CHANGED=()
  while IFS= read -r -d '' file; do
    seen=0
    # 空配列の展開は Bash 3.2 の set -u でエラーになるため、要素があるときだけ比べる
    if [ "${#CHANGED[@]}" -gt 0 ]; then
      for known in "${CHANGED[@]}"; do
        if [ "$known" = "$file" ]; then
          seen=1
          break
        fi
      done
    fi
    [ "$seen" -eq 1 ] || CHANGED+=("$file")
  done < "$list"
  rm -f "$list"
}

check_react() {
  run 'React: テスト' react pnpm test:run
  run 'React: Lint' react pnpm exec eslint .
  run 'React: 型チェック' react pnpm exec tsc --noEmit
  run 'React: 静的ビルド' react env TICKET_STATIC_EXPORT=true \
    NEXT_PUBLIC_API_URL= NEXT_PUBLIC_DEMO_MODE=true pnpm build
}

check_vue() {
  if [ ! -f "$ROOT/vue/package.json" ]; then
    skip 'Vue' 'このコミットに Vue アプリ（vue/package.json）がありません'
    return
  fi

  run 'Vue: テスト' vue pnpm test:run
  run 'Vue: Lint' vue pnpm lint
  run 'Vue: 型チェック' vue pnpm typecheck
  run 'Vue: 整形' vue pnpm format:check
  run 'Vue: 静的生成' vue env NUXT_PUBLIC_API_URL= \
    NUXT_PUBLIC_DEMO_MODE=true pnpm generate
}

check_laravel() {
  local php_files=() file

  # Pint の --diff はリポジトリ相対パスに laravel/ を重ねて対象を見失うため、対象ファイルをここで決めて渡す
  collect_changed_files
  if [ "${#CHANGED[@]}" -gt 0 ]; then
    for file in "${CHANGED[@]}"; do
      case "$file" in
        laravel/*.php)
          # 削除されたファイルは整形の対象外
          if [ -f "$ROOT/$file" ]; then
            php_files+=("${file#laravel/}")
          fi
          ;;
      esac
    done
  fi

  if [ "${#php_files[@]}" -eq 0 ]; then
    skip 'Laravel: 整形（変更ファイル）' "比較元 $BASE から変更された PHP ファイルがありません"
  else
    run 'Laravel: 整形（変更ファイル）' laravel vendor/bin/pint --test "${php_files[@]}"
  fi

  if [ -f "$ROOT/laravel/.env" ]; then
    run 'Laravel: テスト' laravel php artisan test
  else
    run 'Laravel: テスト' laravel env APP_KEY="$TEST_APP_KEY" php artisan test
  fi
}

# 変更のある領域（react・vue・laravel）を 1 行ずつ返す。判定できなければ止める
changed_areas() {
  local file react=0 vue=0 laravel=0

  collect_changed_files
  if [ "${#CHANGED[@]}" -gt 0 ]; then
    for file in "${CHANGED[@]}"; do
      case "$file" in
        react/*) react=1 ;;
        vue/*) vue=1 ;;
        laravel/*) laravel=1 ;;
      esac
    done
  fi

  [ "$react" -eq 0 ] || echo react
  [ "$vue" -eq 0 ] || echo vue
  [ "$laravel" -eq 0 ] || echo laravel
}

target="${1:-changed}"

case "$target" in
  react) check_react ;;
  vue)
    [ -f "$ROOT/vue/package.json" ] ||
      stop 'このコミットに Vue アプリ（vue/package.json）がないため、Vue の検査はできません。'
    check_vue
    ;;
  laravel) check_laravel ;;
  all)
    check_react
    check_vue
    check_laravel
    ;;
  changed)
    # 判定に失敗したら（終了コード 2）、変更なしとして扱わずにそのまま止める
    areas="$(changed_areas)" || exit 2
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
skipped=0
if [ "${#results[@]}" -gt 0 ]; then
  printf '%s\n' "${results[@]}"
  skipped="$(printf '%s\n' "${results[@]}" | grep -c '^SKIP' || true)"
fi

# SKIP は合格ではない。未実行の検査がある場合は、すべて検証済みとは表示しない
if [ "$failed" -ne 0 ]; then
  echo '判定: NG（失敗した検査があります）'
elif [ "$skipped" -gt 0 ]; then
  echo "判定: 実行した検査は OK。ただし ${skipped} 件は未実行（SKIP）のため、すべてを検証済みとは扱わないでください。"
else
  echo '判定: 実行したすべての検査が OK'
fi

exit "$failed"
