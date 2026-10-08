# AI共通作業ルール

このファイルは全Agentが共有する最小の不変ルールだけを持つ。
作業方法は `docs/agent/profiles/` のProfileを必要に応じて切り替える。

## 共通
- Git・コード・テスト・現在の作業MDを実装事実の正とする。
- 未実行の検証を成功扱いしない。
- 既存dirty/untrackedと他作業者の変更を、明示承認なしに上書き・削除・stash・resetしない。
- 承認済み責任・仕様の範囲内では自律的に調査・実装・修正・検証する。
- 新仕様、UX、公開契約、構成、責任範囲を変える必要がある時だけユーザー判断へ戻す。
- 承認範囲外のbranch操作・merge・commit・push・worktree作成は行わない。

## Profile
作業MDがProfileを指定している場合は、そのProfileを追加ルールとして使う。
指定がなければ `continuation` を既定とする。
Profileはこの共通ルールを弱めない。
