# Railwayで公開デモを動かす

この構成は、React / Next.jsの画面とLaravel APIを**同じサービス・同じHTTPSドメイン**で公開します。SQLiteのDBファイルとLaravelの暗号化キーはRailway Volumeへ保存します。デモ用の架空データだけを使います。

## 料金と停止条件

- Railway Hobbyは月額最低 **$5** で、月ごとに請求されます。最初の$5分の利用クレジットが含まれ、超過利用は追加請求の対象です。
- RailwayのWorkspace UsageでCompute Usageのメール警告とHard limitを設定します。上限に達するとサービスが停止し、それ以上のCompute利用を止めます。Hobbyの月額最低料金、税金、カード会社の為替手数料は別途確認してください。
- 使わなくなったときはプロジェクトとVolumeのデータを必要に応じてダウンロードした後、サービス／Volumeを削除して利用を止めます。停止だけではVolumeなどに料金が残る場合があるため、不要になったリソースを削除します。

## 事前準備

1. GitHub上のリポジトリへこの設定を含めます。
2. Railwayで **New Project → Deploy from GitHub repo** を選び、リポジトリを接続します。
3. サービスの地域を **Southeast Asia (Singapore)** に設定します。
4. サービスに **Volume** を追加し、Mount Pathを `/data` にします。SQLite DBとデモ用アプリキーはここに保存されます。
5. Networkingで公開ドメインを生成します。Railwayが提供する`RAILWAY_PUBLIC_DOMAIN`を使って、アプリURLとSanctumのドメインを起動時に設定します。
6. サービスのVariablesに次を設定します。

   - `PORT=8080` (RailwayのNetworkingが示すTarget Portも`8080`)
   - `DB_DATABASE=/data/database.sqlite`
   - `TICKET_DEMO_MODE=true`
   - `APP_DEBUG=false`

   `APP_KEY`は初回起動時に生成してVolumeの`/data/app.key`へ保存します。GitHubへ秘密値を登録しません。

## 사용량 상한과 백업

1. Railway **Workspace → Usage**에서 Compute Usage Hard limit을 **$5**로 지정하고, 이메일 경고도 설정합니다. 상한에 도달하면 데모가 중단될 수 있습니다.
2. 서비스의 Volume 설정에서 백업 스케줄을 켭니다. 데모 DB이므로 **Daily**를 사용합니다. Railway는 Daily 백업을 6일 보관한다고 문서화합니다.
3. 로그인 화면의 공개 데모 계정으로 사용자/관리자 역할을 확인하고, 티켓 이동 및 재접속 후 데이터 유지 여부를 점검합니다.

## 동작 방식과 제한

- 컨테이너 시작 시 `/up` 헬스 체크를 통과하고, SQLite migration을 수행합니다.
- 처음 빈 DB에만 `DemoSeeder`가 실행됩니다. 이후 재배포에서는 기존 DB를 유지하며 데모 seeder를 반복 실행하지 않습니다.
- DB 파일을 Volume에 두지 않으면 재배포 때 데이터가 사라질 수 있습니다.
- Hard limit에 닿으면 비용 초과를 막기 위해 사이트가 오프라인이 됩니다.
- Railway 사용량은 CPU, 메모리, 저장 공간, 네트워크에 따라 변동합니다. $5가 항상 최종 청구액이라는 뜻은 아니므로 상한 설정을 확인합니다.
- 공개 데모에는 실제 후보자 정보나 실제 티켓을 입력하지 않습니다.

## 지금까지 준비된 점과 미확인 점

- Railway 공식 Laravel 배포 절차는 GitHub 저장소 연결과 공개 도메인 발급을 지원합니다.
- 이 프로젝트는 Next.js와 Laravel이 별도 디렉터리에 있어, Dockerfile이 Next 화면을 정적 export한 뒤 Laravel의 `public/` 아래에 배치합니다.
- 프로젝트의 기존 배포 자료는 Alwaysdata 전용이므로 Railway 배포 설정은 새로 준비한 것입니다. Railway 계정에서 실제 빌드, DB 영속화, 로그인/권한, 드래그앤드롭 동작을 확인한 뒤 공개 링크를 공유합니다.
