# PHP runtime security baseline

The Laravel application runs on PHP. Composer dependency audits do **not** patch
vulnerabilities in the PHP interpreter.

## PHP2Shell (21 October 2026)

CVE-2026-109618 and CVE-2026-109619 affect PHP web-serving runtimes and can
allow unauthenticated remote code execution.

Minimum fixed upstream PHP releases:

| PHP series | Minimum fixed release |
| --- | --- |
| 8.5 | 8.5.12 |
| 8.4 | 8.4.27 |
| 8.3 | 8.3.36 |
| 8.2 | 8.2.35 |

PHP 8.2 is listed for incident reference; this application's Composer requirement
is currently `^8.3`. PHP 8.1 and older are unsupported upstream.

**Before running or deploying Laravel**, verify the PHP version of the actual
web-serving process, not only the developer machine's CLI:

```sh
php -v
composer check-platform-reqs
composer audit
php artisan test
```

Upgrade the PHP interpreter via the runtime/package manager and restart the
web server, PHP-FPM workers, or containers as applicable. `composer update`
alone does not upgrade PHP. Inspect container images and hosting runtimes
separately. Do not expose a vulnerable runtime to the public internet.

This repository does not currently declare a deployment image or a CI runtime
matrix; `composer.json`'s `^8.3` requirement is **not** a security guarantee.
Before tightening the Composer PHP constraint, regenerate and validate
`composer.lock` with Composer in an approved runtime. Do not edit the lock
content hash by hand.

Sources:
- https://www.php.net/releases/8_5_12.php
- https://www.cyber.gc.ca/en/alerts-advisories/al26-026-critical-vulnerabilities-impacting-php-cve-2026-109618-and-cve-2026-109619
