# Runbook: PostgreSQL database restore

Covers requirement `rel.backup_configured`. This runbook explains how to restore the
leav_tracker_har PostgreSQL database from its automated backups. It also holds the
restore-test log, which must have at least one completed entry before go-live.

## Backup configuration (source of truth: `infra/main.tf`)

| Setting | Value |
|---|---|
| Server | `psql-lev-trak-har` (Azure Database for PostgreSQL Flexible Server, v16) |
| Resource group | `lev-trak-har` |
| Primary region | `uksouth` |
| Automated backups | Enabled (platform managed: daily snapshots plus continuous WAL archiving) |
| Retention | `backup_retention_days = 35` (meets the 30-day minimum) |
| Off-region copy | `geo_redundant_backup_enabled = true`, so backups are replicated to the paired region (`ukwest`) |
| Point-in-time recovery | Supported to any second inside the 35-day retention window |

Notes:
- `geo_redundant_backup_enabled` can only be set when a server is created. If someone
  turns it off in Terraform, the server is replaced. Do not change it without a migration plan.
- Restores always create a **new** server. The existing server is never overwritten in place.

## Prerequisites

- Azure CLI (`az`) logged in with Contributor (or higher) on resource group `lev-trak-har`.
- Read/write access to the secret store that holds the app's database settings
  (`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
  read by `backend/config/settings/base.py`).
- A restore target name that is not in use yet, e.g. `psql-lev-trak-har-restore-<yyyymmdd>`.

## Procedure A: point-in-time restore (same region)

Use this for logical damage such as bad migrations, accidental deletes or data corruption.

1. Pick the restore point. This is a UTC timestamp from **before** the incident and inside
   the last 35 days. Check the earliest restore point available:

   ```bash
   az postgres flexible-server show \
     --resource-group lev-trak-har --name psql-lev-trak-har \
     --query "{earliestRestore: backup.earliestRestoreDate, retention: backup.backupRetentionDays, geo: backup.geoRedundantBackup}"
   ```

2. Restore to a new server:

   ```bash
   az postgres flexible-server restore \
     --resource-group lev-trak-har \
     --name psql-lev-trak-har-restore-<yyyymmdd> \
     --source-server psql-lev-trak-har \
     --restore-time "<YYYY-MM-DDTHH:MM:SSZ>"
   ```

3. Do **Network and access** (below), then **Repoint the application** and **Validate**.

## Procedure B: geo-restore (regional outage in `uksouth`)

Use this when the primary region is unavailable. The restored server is built from the
geo-replicated backup in the paired region. Expect up to about 1 hour of data loss, since
geo-replication runs asynchronously.

```bash
az postgres flexible-server geo-restore \
  --resource-group lev-trak-har \
  --name psql-lev-trak-har-geo-<yyyymmdd> \
  --source-server /subscriptions/<subscription-id>/resourceGroups/lev-trak-har/providers/Microsoft.DBforPostgreSQL/flexibleServers/psql-lev-trak-har \
  --location ukwest
```

Then continue with **Network and access**, **Repoint the application** and **Validate**.

## Network and access

The primary server has `public_network_access_enabled = false` and is reached through
private endpoint `pe-psql-lev-trak-har` and the `privatelink.postgres.database.azure.com`
DNS zone. The restored server needs the same setup:

1. Create a private endpoint for the restored server on the shared VNet subnet (`subnet_id`),
   attached to the same private DNS zone group. For geo-restore, use a subnet that can reach `ukwest`.
2. Check that `<restored-server>.postgres.database.azure.com` resolves to a private IP from inside
   the Container Apps environment.
3. The admin login stays `psqladmin` and the password is copied from the source server. If the
   password has to be rotated, do it now and record the new value in the secret store.

## Repoint the application

1. Set `POSTGRES_HOST` to the FQDN of the restored server in the secret store that the
   container app reads. If the password was rotated, update `POSTGRES_PASSWORD` too.
2. Restart the backend container app revision so Django reads the new settings.
3. Do not run `manage.py migrate` against the restored database until validation passes.
4. Afterwards, bring Terraform back in line with the server that is now live (import the restored
   server, or rename/promote it). Otherwise the next `terraform apply` will not match what is running.

## Validate

Connect to the restored server (`psql "host=<restored-fqdn> dbname=postgres user=psqladmin sslmode=require"`)
and run:

```sql
-- Schema is at the expected migration level
SELECT app, name, applied FROM django_migrations ORDER BY applied DESC LIMIT 5;

-- Core tables are present and populated
SELECT count(*) FROM accounts_user;
SELECT count(*) FROM leave_leaverequest;

-- Newest data matches the chosen restore point
SELECT max(created_at) FROM leave_leaverequest;
```

Then check the application:

- `GET /healthz/` returns HTTP 200.
- A test user can log in and see their leave requests.

When the restore is confirmed good and the incident is closed, decommission the old server.

## Restore test log

A restore test (Procedure A, into a throwaway server that is deleted afterwards) **must be
completed and recorded here before go-live**. After that, repeat it at least once a year and
after any major change to the infrastructure.

| Date (UTC) | Procedure | Restore point used | Restored server | Validation result | Time to restore | Performed by |
|---|---|---|---|---|---|---|
| _pending — required before go-live_ | A (PITR) | | | | | |
