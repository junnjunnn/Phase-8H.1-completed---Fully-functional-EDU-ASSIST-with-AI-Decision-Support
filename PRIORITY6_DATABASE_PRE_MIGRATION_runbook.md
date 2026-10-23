# EDU ASSIST Pre-Migration Runbook

## Purpose and status

This is a preparation and execution guide for a future, separately authorized

application of

`attendance.0013_attendancerecord_excused_absences`. It does not authorize

database access, backup creation, restore, or migration. The commands below

are documented only; none has been run as part of preparing this runbook.

Run PowerShell commands from `F:\edu_new\BACKEND` unless a step says

otherwise. The Django entry point is `manage.py`; it sets

`DJANGO_SETTINGS_MODULE=config.settings` by default. The active settings use

`config.mysql_compat`, a MySQL-compatible Django backend intended to support

MariaDB. Run the PowerShell blocks in sections 3-5 in the same PowerShell

session so variables set in one block remain available to later blocks.

The reports contain different observations from different dates and database

states. The 2026-08-27 recovery assessment found attendance migrations `0005`

through `0007` unapplied at that time. A later Issue 5.7 report recorded

`0011` as applied, and a rebuild report recorded `0005`-`0007` as applied in

its own captured state. These are historical findings, not proof of the

current state. In particular, do not infer that `0012` is applied. Identify

the exact database target and read its current migration history before

deciding whether `0013` is appropriate.

## Placeholders and stop conditions

Replace every `REPLACE_WITH_...` value only after confirming it from the

intended target or an approved isolation environment. Do not substitute

values from a historical report without reconfirming them. If the target

identity, client tool, permissions, backup destination, restore isolation, or

migration plan is uncertain, stop.

Never run a restore command against the live `edu_assist` server or any server

that could route to it. A different database name on the same live server is

not an isolated database instance. Do not proceed to migration without a

separately authorized change window and approval of the exact target and plan.

## 1. Read-only inspection

### 1.1 Inspect effective Django database settings without secrets

**PowerShell — read-only; run from the backend directory:**

```powershell

Set-Location 'F:\edu_new\BACKEND'

python .\manage.py shell -c "from django.conf import settings; d=settings.DATABASES['default']; print({'engine': d['ENGINE'], 'database': d['NAME'], 'host': d['HOST'], 'port': d['PORT'], 'debug': settings.DEBUG})"

```

This prints only the effective backend, database name, host, port, and debug

flag. It deliberately does not print the database username, password, secret

key, environment-file contents, tokens, or row data. The settings load

`BACKEND\.env`; never use `Get-Content` or another command to display that

file. Confirm the reported values are the intended target before continuing.

### 1.2 Confirm the connected server, database, backend vendor, and version

**PowerShell invoking Django — read-only SQL `SELECT`; no row contents:**

```powershell

python .\manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('SELECT DATABASE(), @@hostname, @@port, VERSION()'); print({'vendor': connection.vendor, 'database_server': c.fetchone()})"

```

The tuple is the connected database name, the database server's reported

hostname, server port, and version string; `vendor` is Django's backend vendor

(expected to identify as `mysql` for this compatibility backend). Compare the

connected database and server with section 1.1 and the independently intended

target. Stop on any mismatch. This query is read-only but does make a database

connection.

### 1.3 Identify available MariaDB/MySQL client tools

**PowerShell — local executable lookup; does not connect to a database:**

```powershell

Get-Command mariadb-dump, mysqldump, mariadb, mysql -ErrorAction SilentlyContinue | Select-Object Name, Source

```

If a dump or client executable is not found, stop and have the approved

operator identify the installed client. Do not download or install a client

as part of this runbook. The reports historically identify a MariaDB server

(10.4.32 at the time of the 2026-08-27 inspection) and a successful logical

dump in a later report; neither establishes the current server version or

which client executable is currently installed.

## 2. Review the complete migration plan

All commands in this section are **Django read-only plan/history inspection**.

They use the configured `default` database and can connect to it. Run them

only after confirming the target in section 1.

```powershell

python .\manage.py showmigrations --plan --database=default

python .\manage.py migrate --plan --database=default

python .\manage.py migrate attendance 0013_attendancerecord_excused_absences --plan --database=default

```

Review and retain the complete output. `showmigrations --plan` marks applied

and unapplied migrations; `migrate --plan` displays the pending project plan;

the targeted plan shows the target migration and its dependencies. Record

every pending dependency in the targeted plan, including earlier attendance

migrations and dependencies from other apps. Do not assume that only `0013`

will run. If `0005` through `0007`, `0012`, or any other dependency is pending,

review its source and effect on the confirmed target before considering

execution. Stop if the plan is unexpected, incomplete, or differs from the

approved plan.

The source for `0013` is

`BACKEND\attendance\migrations\0013_attendancerecord_excused_absences.py`.

It depends on

`attendance.0012_schoolcalendarday_approval_notes_and_more` and adds the

nullable `excused_absences` field to `AttendanceRecord`. This source-level

fact does not establish which migrations have been applied to any database.

## 3. Create a fresh logical backup

**This section creates a database dump file and is not read-only. Do not run

it until backup creation is separately authorized.** It does not restore or

change database rows. Choose an approved absolute destination outside

`F:\edu_new`; do not use a repository path. Choose and verify a protected

separate physical device for the independent copy in section 4.

First set the values from the just-confirmed target. Do not put a password in

these variables, command arguments, shell history, or the runbook.

**PowerShell — local variables and destination directory creation:**

```powershell

$DbHost = 'REPLACE_WITH_VERIFIED_DATABASE_HOST'

$DbPort = 'REPLACE_WITH_VERIFIED_DATABASE_PORT'

$DbName = 'REPLACE_WITH_VERIFIED_DATABASE_NAME'

$DbUser = 'REPLACE_WITH_VERIFIED_DATABASE_ACCOUNT'

$BackupRoot = 'REPLACE_WITH_APPROVED_ABSOLUTE_BACKUP_PATH_OUTSIDE_F:\edu_new'

if ([string]::IsNullOrWhiteSpace($DbHost) -or $DbHost -like 'REPLACE_WITH_*' -or

    [string]::IsNullOrWhiteSpace($DbPort) -or $DbPort -like 'REPLACE_WITH_*' -or

    [string]::IsNullOrWhiteSpace($DbName) -or $DbName -like 'REPLACE_WITH_*' -or

    [string]::IsNullOrWhiteSpace($DbUser) -or $DbUser -like 'REPLACE_WITH_*') {

    throw 'Set all database target placeholders from the confirmed target before continuing.'

}

if ([string]::IsNullOrWhiteSpace($BackupRoot) -or $BackupRoot -like 'REPLACE_WITH_*' -or

    -not [System.IO.Path]::IsPathRooted($BackupRoot)) {

    throw 'Set an approved absolute backup destination before continuing.'

}

$RepoRoot = [System.IO.Path]::GetFullPath('F:\edu_new').TrimEnd('\')

$BackupRoot = [System.IO.Path]::GetFullPath($BackupRoot).TrimEnd('\')

if ($BackupRoot.Equals($RepoRoot, [System.StringComparison]::OrdinalIgnoreCase) -or

    $BackupRoot.StartsWith($RepoRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {

    throw 'The backup destination must be outside the repository.'

}

New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$BackupFile = Join-Path $BackupRoot ("edu_assist_pre_migration_{0}.sql" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))

if (Test-Path -LiteralPath $BackupFile) {

    throw 'The timestamped backup path already exists; select a new destination/name.'

}

```

The filename is generic; it does not assert the database name. The

`REPLACE_WITH_...` values must be set from the inspected target, not inferred

from this example or a report.

Use the MariaDB dump client if present, otherwise the compatible MySQL dump

client. The password option has no value so the client prompts for it; never

append the password to the command.

**PowerShell — logical backup creation:**

```powershell

$DumpCommand = Get-Command mariadb-dump -ErrorAction SilentlyContinue

if (-not $DumpCommand) {

    $DumpCommand = Get-Command mysqldump -ErrorAction Stop

}

& $DumpCommand.Source "--host=$DbHost" "--port=$DbPort" "--user=$DbUser" --password `

    --single-transaction --skip-lock-tables --quick --hex-blob `

    --routines --events --triggers --no-create-db `

    "--result-file=$BackupFile" $DbName

if ($LASTEXITCODE -ne 0) {

    throw "The dump client exited with code $LASTEXITCODE. Treat the output file as incomplete and do not restore it."

}

```

This requests schema and data for the named database, plus routines, events,

and triggers, while suppressing database-creation statements. Do not add

`--databases` or `--add-drop-database`: the dump must not be able to switch

databases when imported. `--result-file` avoids PowerShell text-pipeline

encoding conversions.

The account must have the privileges required to read the selected schema and

include routines/events/triggers. If the client reports privilege or

consistency errors, stop and resolve them through the approved database

operator; do not silently omit objects or treat a failed dump as a backup.

`--single-transaction` provides a consistent snapshot only for transactional

tables (such as InnoDB) and does not protect against concurrent DDL or make

non-transactional tables transactionally consistent. Coordinate a suitable

write/DDL freeze if required by the actual storage engines and operations.

## 4. Verify the backup and create a protected copy

**PowerShell — local file reads and copy operations; no database connection:**

```powershell

$BackupInfo = Get-Item -LiteralPath $BackupFile -ErrorAction Stop

if ($BackupInfo.Length -le 0) {

    throw 'The dump file is empty; do not use it.'

}

$BackupInfo | Select-Object FullName, Length, LastWriteTimeUtc

$BackupHash = Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256

$BackupHash | Select-Object Algorithm, Hash, Path

$DbSwitchStatements = Select-String -LiteralPath $BackupFile `

    -Pattern '^\s*(CREATE\s+(DATABASE|SCHEMA)\b|USE\s+)' -CaseSensitive:$false

if ($DbSwitchStatements) {

    throw 'The dump contains a database-creation or database-switch statement. Do not restore it; review and create a safe working dump first.'

}

```

Do not print or inspect SQL row contents. The statement check must complete

with no matches before using the restore command below. The dump command

intentionally omits database-selection statements; the check is a fail-closed

guard against using a dump produced with different options.

Create an independent copy at an approved destination on a separately

identified physical device. A second folder or drive letter on the same

physical disk is not protection against disk failure. Also create a distinct

working copy for the restore rehearsal; never use the protected original as a

working file. Do not overwrite existing files.

**PowerShell — file copy and byte-integrity comparison:**

```powershell

$CopyFile = 'REPLACE_WITH_APPROVED_ABSOLUTE_COPY_PATH_ON_A_SEPARATE_PHYSICAL_DEVICE'

$WorkingCopy = 'REPLACE_WITH_APPROVED_ABSOLUTE_PATH_FOR_REHEARSAL_WORKING_COPY'

if ([string]::IsNullOrWhiteSpace($CopyFile) -or $CopyFile -like 'REPLACE_WITH_*' -or

    -not [System.IO.Path]::IsPathRooted($CopyFile)) {

    throw 'Set an approved absolute copy path before continuing.'

}

if ([string]::IsNullOrWhiteSpace($WorkingCopy) -or $WorkingCopy -like 'REPLACE_WITH_*' -or

    -not [System.IO.Path]::IsPathRooted($WorkingCopy)) {

    throw 'Set an approved absolute working-copy path before continuing.'

}

$CopyFile = [System.IO.Path]::GetFullPath($CopyFile)

$WorkingCopy = [System.IO.Path]::GetFullPath($WorkingCopy)

$BackupFile = [System.IO.Path]::GetFullPath($BackupFile)

$CopyParent = Split-Path -Parent $CopyFile

$WorkingParent = Split-Path -Parent $WorkingCopy

if ($CopyFile.Equals($BackupFile, [System.StringComparison]::OrdinalIgnoreCase) -or

    $WorkingCopy.Equals($BackupFile, [System.StringComparison]::OrdinalIgnoreCase) -or

    $WorkingCopy.Equals($CopyFile, [System.StringComparison]::OrdinalIgnoreCase)) {

    throw 'Source, protected copy, and working copy must be different files.'

}

foreach ($Destination in @($CopyFile, $WorkingCopy)) {

    if ($Destination.Equals($RepoRoot, [System.StringComparison]::OrdinalIgnoreCase) -or

        $Destination.StartsWith($RepoRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {

        throw 'Backup copies must be outside the repository.'

    }

}

if (-not (Test-Path -LiteralPath $CopyParent -PathType Container) -or

    -not (Test-Path -LiteralPath $WorkingParent -PathType Container)) {

    throw 'Create and secure both destination folders before copying.'

}

if ((Test-Path -LiteralPath $CopyFile) -or (Test-Path -LiteralPath $WorkingCopy)) {

    throw 'A destination already exists; do not overwrite it.'

}

$SourceHash = (Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash

if ($SourceHash -ne $BackupHash.Hash) {

    throw 'The source dump changed since its initial checksum; do not copy it.'

}

Copy-Item -LiteralPath $BackupFile -Destination $CopyFile

$CopyInfo = Get-Item -LiteralPath $CopyFile -ErrorAction Stop

$CopyHash = (Get-FileHash -LiteralPath $CopyFile -Algorithm SHA256).Hash

if ($CopyInfo.Length -ne $BackupInfo.Length -or $CopyHash -ne $BackupHash.Hash -or

    (Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash -ne $BackupHash.Hash) {

    throw 'The copied file does not match the source size and SHA-256.'

}

Copy-Item -LiteralPath $CopyFile -Destination $WorkingCopy

$WorkingInfo = Get-Item -LiteralPath $WorkingCopy -ErrorAction Stop

$WorkingHash = (Get-FileHash -LiteralPath $WorkingCopy -Algorithm SHA256).Hash

if ($WorkingInfo.Length -ne $BackupInfo.Length -or $WorkingHash -ne $BackupHash.Hash) {

    throw 'The rehearsal working copy does not match the source size and SHA-256.'

}

$CopyInfo | Select-Object FullName, Length, LastWriteTimeUtc

Get-FileHash -LiteralPath $CopyFile -Algorithm SHA256 | Select-Object Algorithm, Hash, Path

$WorkingInfo | Select-Object FullName, Length, LastWriteTimeUtc

Get-FileHash -LiteralPath $WorkingCopy -Algorithm SHA256 | Select-Object Algorithm, Hash, Path

```

A matching size and SHA-256 demonstrate that the two files are byte-identical

to each other; they do not prove that the dump is complete, restorable,

consistent, or semantically correct. Keep the original dump unchanged.

Protect both copies as sensitive student/staff data: use approved access

controls and encryption at rest, restrict access, do not commit, email, upload,

or place them in an unapproved sync folder, and apply the organization's

retention/disposal policy.

## 5. Isolated restore rehearsal

**This section creates a database and writes data, but only on a separately

verified isolated MariaDB instance. It is not a migration and is not

authorized by this runbook.**

Prerequisites:

- The isolated instance is a distinct MariaDB server process/instance in an

  environment that cannot route to or share storage with the live database.

  A new database on the live instance is not sufficient.

- Independently verify the isolated server identity, host, port, version,

  network isolation, and disposable status before connecting. Do not infer

  these values from the live server or historical reports.

- Create and protect a local MariaDB client option file through the approved

  credential process. It must contain only the credentials and connection

  settings for the isolated instance, be outside the repository, and have

  access restricted to the required operator. Do not display, log, or commit

  it. If it cannot be protected, stop.

- Use the verified original backup copied to the separately named

  `$WorkingCopy` file from section 4.

  Recheck its size, SHA-256, and absence of `CREATE DATABASE`/`USE` statements

  in that working file. Do not edit or overwrite the original or protected

  copy.

**PowerShell — read-only statement check of the rehearsal working copy:**

```powershell

$DbSwitchStatements = Select-String -LiteralPath $WorkingCopy `

    -Pattern '^\s*(CREATE\s+(DATABASE|SCHEMA)\b|USE\s+)' -CaseSensitive:$false

if ($DbSwitchStatements) {

    throw 'The working copy contains a database-creation or database-switch statement. Do not restore it.'

}

```

The fresh dump was requested without `--databases` and with

`--no-create-db`; therefore the restore selects the rehearsal database on the

isolated instance using the client argument. If a dump contains embedded

`CREATE DATABASE`, `CREATE SCHEMA`, or `USE` statements, those statements can

override the selected database or create the live database name. **Do not

restore such a dump as-is.** Stop, generate/review a new statement-free

working dump or obtain a separately reviewed transformation, then repeat the

checks. Never point a restore command at the live instance, even if the

database argument appears to name a rehearsal database.

Create a uniquely named empty database on the isolated instance. Replace the

option-file path and database-name placeholders with values confirmed for

that disposable environment. Use only a valid identifier chosen for this

rehearsal.

Use `mariadb` below when that client is available from section 1.3. If only

the compatible `mysql` client is installed, substitute its confirmed

executable name; do not assume the client exists merely because the server is

MariaDB. In the Command Prompt commands below, replace every placeholder

before running the command and inspect the complete rendered line. Use

absolute option-file and SQL-file paths with no `%` characters so Command

Prompt does not expand them as environment variables. The protected option

file must specify the confirmed isolated host and port.

**Command Prompt — read-only server identity check on the isolated instance:**

```text

mariadb --defaults-extra-file="REPLACE_WITH_ACL_PROTECTED_ISOLATED_CLIENT_OPTION_FILE" --execute="SELECT DATABASE(), @@hostname, @@port, VERSION();"

```

Confirm the returned server hostname, port, and version against the

independently approved isolated-instance details before creating any database.

`DATABASE()` is expected to be `NULL` when no default database is selected.

Stop if the result is unexpected or cannot be independently matched to the

isolated instance. The option file must be the first client option, as shown.

**Command Prompt — database creation on the isolated instance only:**

```text

mariadb --defaults-extra-file="REPLACE_WITH_ACL_PROTECTED_ISOLATED_CLIENT_OPTION_FILE" --execute="CREATE DATABASE `REPLACE_WITH_UNIQUE_REHEARSAL_DATABASE_NAME` CHARACTER SET utf8mb4;"

```

`--defaults-extra-file` must be the first client option. Its file must point

only to the isolated instance. The database identifier inside the SQL must be

replaced with the same unique rehearsal database name used below. If the

client reports an error or the server identity is uncertain, stop.

**Command Prompt — import the verified working copy into that isolated

database only:**

```text

mariadb --defaults-extra-file="REPLACE_WITH_ACL_PROTECTED_ISOLATED_CLIENT_OPTION_FILE" --database="REPLACE_WITH_UNIQUE_REHEARSAL_DATABASE_NAME" < "REPLACE_WITH_ABSOLUTE_PATH_TO_VERIFIED_WORKING_COPY.sql"

```

The option file is used instead of putting a password in the command line or

redirecting a password prompt together with SQL input. The dump's absence of

database-switching statements and the isolated connection are both mandatory

safeguards. Verify the restore on the isolated instance using an approved,

read-only schema/migration review before drawing conclusions. A successful

client exit alone does not prove application-level recovery.

## 6. Separately authorized migration execution

Do not run this until the target has been reconfirmed, the complete project

and targeted dependency plans have been reviewed, the backup and independent

copy have been verified, the isolated restore rehearsal has been reviewed,

and explicit approval has been given for this exact database and migration.

Re-run sections 1 and 2 immediately before execution and stop if the target or

plan changed.

**Django — write operation; separately authorized execution only:**

```powershell

python .\manage.py migrate attendance 0013_attendancerecord_excused_absences --database=default --noinput

```

This targeted migration command can also apply any unapplied dependencies in

its dependency graph. Do not use it as a substitute for reviewing the complete

plan; do not add `--fake`, `flush`, seed, reset, or unrelated migration

commands. After a separately approved execution, use the read-only plan and

history commands in section 2 to confirm the resulting migration state.

## 7. Unresolved prerequisites and readiness

No prerequisite below is marked complete by this documentation. Historical

reports are not operational verification of the present target.

- [ ] Confirm the intended live target and effective settings without

  disclosing credentials.

- [ ] Confirm the connected database server, database name, Django vendor,

  server version, and compatibility with the installed dump/client tools.

- [ ] Confirm the current applied/unapplied migration state and review the

  complete pending project plan, including every dependency of `0013`.

- [ ] Choose and approve an absolute backup destination outside the

  repository; create a fresh logical backup and verify nonzero size and

  SHA-256.

- [ ] Verify that the dump has no embedded database creation/switch statements

  and contains the required schema, data, routines, events, and triggers.

- [ ] Make and hash-verify a protected copy on a separate physical device;

  the recovery report's 2026-10-20 copy was reported on the same physical disk

  as its source.

- [ ] Identify and verify a genuinely isolated, disposable MariaDB instance

  and protected client credentials; complete and review a restore rehearsal.

- [ ] Review the exact pending migration/dependency effects and obtain

  separate explicit authorization for execution against the identified

  target.

**Readiness decision: NOT READY for migration execution.** Current target

identity, current migration state, a fresh pre-migration backup, independent

physical-device copy, isolated restore rehearsal, and explicit migration

authorization remain to be established. No operational verification is

claimed.