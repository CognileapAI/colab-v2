\set ON_ERROR_STOP on
-- Apply as a cluster administrator after 0025. These are permission groups;
-- grant exactly one to a dedicated NOBYPASSRLS runtime login outside this file.
-- No passwords, app-role membership, schema changes or RLS-bypass policies.
BEGIN;
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='colab_operator_reporter') THEN
    CREATE ROLE colab_operator_reporter NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='colab_operator_exporter') THEN
    CREATE ROLE colab_operator_exporter NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
  IF EXISTS (SELECT FROM pg_roles WHERE rolname IN ('colab_operator_reporter','colab_operator_exporter')
             AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN
    RAISE EXCEPTION 'operator permission groups have unsafe role attributes';
  END IF;
  IF EXISTS (SELECT FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member
             WHERE r.rolname IN ('colab_operator_reporter','colab_operator_exporter')) THEN
    RAISE EXCEPTION 'operator permission groups must not inherit other roles';
  END IF;
  IF EXISTS (SELECT FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner
             WHERE r.rolname IN ('colab_operator_reporter','colab_operator_exporter')) THEN
    RAISE EXCEPTION 'operator permission groups must not own tables';
  END IF;
END $$;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM colab_operator_reporter,colab_operator_exporter;
GRANT USAGE ON SCHEMA public TO colab_operator_reporter,colab_operator_exporter;
REVOKE CREATE ON SCHEMA public FROM colab_operator_reporter,colab_operator_exporter;
GRANT SELECT(id,name) ON d1_lab TO colab_operator_reporter,colab_operator_exporter;
GRANT SELECT(id,lab_id,name) ON d1_account TO colab_operator_reporter,colab_operator_exporter;
GRANT SELECT ON d2_operator_audit,d3_operator_audit,d6_operator_audit
 TO colab_operator_reporter;
GRANT SELECT ON d2_operator_export,d3_operator_export,d5_operator_export,d6_operator_export,d8_operator_export
 TO colab_operator_reporter,colab_operator_exporter;
GRANT UPDATE(receipt_hash,received_at) ON d2_operator_export,d3_operator_export,d5_operator_export,d6_operator_export,d8_operator_export
 TO colab_operator_exporter;
DO $$
BEGIN
  IF has_column_privilege('colab_operator_reporter','d1_account','email','SELECT')
     OR has_column_privilege('colab_operator_exporter','d1_account','email','SELECT') THEN
    RAISE EXCEPTION 'operator name lookup must not include account email';
  END IF;
  IF has_schema_privilege('colab_operator_reporter','public','CREATE')
     OR has_schema_privilege('colab_operator_exporter','public','CREATE') THEN
    RAISE EXCEPTION 'public schema permissions unexpectedly allow operator DDL';
  END IF;
END $$;
COMMIT;
