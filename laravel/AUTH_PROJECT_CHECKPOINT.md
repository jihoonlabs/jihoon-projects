# 認証機能チェックポイント

最終更新：2026-09-23

作業ブランチ：`feature/auth-login`

最新コミット：`d101f36 fix: harden CSRF token handling`

## 現在の状況

Next.jsとLaravelを使用した認証機能の実装が完了しています。

- メールアドレスによる会員登録・ログイン
- メールアドレス認証および再送
- Google・LINEログイン
- パスワード再設定
- active・suspendedアカウントの制御
- Laravel SanctumによるSPAセッション認証
- パスワード変更後の既存セッション無効化
- CSRF Cookieの取得およびXSRF Tokenの送信処理

## 認証方針

- メール・Google・LINEアカウントは自動連携しない
- 未認証または停止中のアカウントはログイン不可
- アカウントの存在や状態が外部から判別されない応答を使用する
- パスワード変更後は既存セッションを無効化する
- 認証関連の主要処理にはRate Limitを適用する

## フロントエンド確認・改善状況

- LoginFormのコード確認およびテスト作成
- RegisterFormのコード確認およびテスト作成
- ForgotPasswordFormのコード確認およびテスト作成
- ResetPasswordFormのコード確認およびテスト作成
- ログイン・会員登録・パスワード再設定関連の入力チェックテスト作成
- MSWを使用した認証API通信テスト作成
- CSRF Cookieの解析およびToken未取得時のエラー処理を改善
- MSWのCSRF handlerにCookie設定処理を追加
- `axios.ts`の責任と使用箇所を確認
- `apiClient`は共通のAxios設定として維持
- `noticeApi.ts`・`postApi.ts`ではGETリクエストに使用されていることを確認
- 現時点では`fetchWithCsrf`との統合・共通化は行わない
- 認証関連テスト13ファイルの内容を再確認し、追加修正不要と判断

## 確認状況

- Laravel：57 tests、230 assertions（全件成功）
- React：14 test files、47 tests（全件成功）
- React lint完了
- React production build完了
- `git diff --check`完了
- メール・Google・LINEログインをブラウザで確認済み
- パスワード再設定の一連の動作を確認済み

## 次の作業

- 認証関連READMEの整理
- `main`ブランチへのマージ準備

## 作業ルール

- 一度に一つのファイルまたは機能を確認する
- 必要な変更だけを行い、既存機能を不用意に変更しない
- 自動テストとブラウザ確認を分けて実施する
- ページは薄く保ち、実際の動作はコンポーネント側で確認する
- 不要な共通化や過剰なコメントを避ける