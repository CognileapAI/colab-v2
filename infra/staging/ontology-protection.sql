-- Administrative ownership policy, not product schema. Run as DB administrator.
-- No LOGIN and no membership: routine deployment cannot assume the owner role.
-- SELECT/INSERT/UPDATE remain available for reviewed dictionary additions/corrections.
-- DDL and DELETE/TRUNCATE require a separately authorized administrator workflow.
BEGIN;
DO $$
BEGIN
  IF current_database() <> 'colab_ai' THEN
    RAISE EXCEPTION 'ontology protection requires colab_ai';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='colab_ontology_guardian') THEN
    CREATE ROLE colab_ontology_guardian NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
  END IF;
  IF EXISTS (SELECT FROM pg_roles WHERE rolname='colab_ontology_guardian'
             AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls))
     OR EXISTS (SELECT FROM pg_auth_members WHERE roleid='colab_ontology_guardian'::regrole
                OR member='colab_ontology_guardian'::regrole) THEN
    RAISE EXCEPTION 'ontology guardian must be isolated NOLOGIN role';
  END IF;
  IF EXISTS (SELECT FROM pg_roles WHERE rolname IN ('colab_owner','colab_ai_app')
             AND (rolsuper OR rolcreatedb OR rolcreaterole)) THEN
    RAISE EXCEPTION 'routine ontology roles have administrative privileges';
  END IF;
END $$;
ALTER DATABASE colab_ai OWNER TO colab_ontology_guardian;
REVOKE CREATE ON DATABASE colab_ai FROM PUBLIC, colab_owner;
GRANT CONNECT ON DATABASE colab_ai TO colab_owner;
ALTER SCHEMA public OWNER TO colab_ontology_guardian;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO colab_owner;
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
           WHERE n.nspname='public' AND c.relkind IN ('r','p') AND left(c.relname,3)='d9_' LOOP
    EXECUTE format('ALTER TABLE public.%I OWNER TO colab_ontology_guardian', t.relname);
    EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC, colab_owner', t.relname);
    EXECUTE format('GRANT SELECT, INSERT, UPDATE ON TABLE public.%I TO colab_owner', t.relname);
    IF EXISTS (SELECT FROM pg_roles WHERE rolname='colab_ai_app') THEN
      EXECUTE format('REVOKE ALL ON TABLE public.%I FROM colab_ai_app', t.relname);
      EXECUTE format('GRANT SELECT ON TABLE public.%I TO colab_ai_app', t.relname);
    END IF;
    IF has_table_privilege('colab_owner', format('public.%I',t.relname), 'DELETE,TRUNCATE') THEN
      RAISE EXCEPTION 'ontology destructive privilege remains on %',t.relname;
    END IF;
  END LOOP;
  IF EXISTS (SELECT FROM pg_roles WHERE rolname='colab_ai_app') THEN
    GRANT CONNECT ON DATABASE colab_ai TO colab_ai_app;
    GRANT USAGE ON SCHEMA public TO colab_ai_app;
  END IF;
END $$;
COMMIT;
