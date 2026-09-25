-- Read-only verification. Missing objects/roles or inherited destructive rights fail.
WITH RECURSIVE reachable(oid) AS (
  SELECT oid FROM pg_roles WHERE rolname IN ('colab_owner','colab_ai_app')
  UNION
  SELECT m.roleid FROM pg_auth_members m JOIN reachable r ON m.member=r.oid
), guardian AS (
  SELECT oid FROM pg_roles WHERE rolname='colab_ontology_guardian'
    AND NOT (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls)
), protected AS (
  SELECT c.oid,c.relowner FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='public' AND c.relkind IN ('r','p') AND left(c.relname,3)='d9_'
)
SELECT CASE WHEN
  current_database()='colab_ai'
  AND (SELECT count(*) FROM guardian)=1
  AND (SELECT datdba FROM pg_database WHERE datname=current_database())=(SELECT oid FROM guardian)
  AND (SELECT nspowner FROM pg_namespace WHERE nspname='public')=(SELECT oid FROM guardian)
  AND NOT EXISTS (SELECT FROM pg_auth_members WHERE roleid=(SELECT oid FROM guardian) OR member=(SELECT oid FROM guardian))
  AND (SELECT count(*) FROM pg_roles WHERE rolname IN ('colab_owner','colab_ai_app') AND NOT (rolsuper OR rolcreatedb OR rolcreaterole))=2
  AND NOT EXISTS (SELECT FROM (VALUES ('d9_method_term'),('d9_topic_synonym'),('d9_place_alias'),('d9_concept'),('d9_concept_edge')) required(name)
                  WHERE NOT EXISTS (SELECT FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                                    WHERE n.nspname='public' AND c.relname=required.name AND c.relkind IN ('r','p')
                                      AND c.relowner=(SELECT oid FROM guardian)))
  AND NOT EXISTS (SELECT FROM reachable r JOIN pg_roles p ON p.oid=r.oid
                  WHERE p.rolsuper OR p.rolcreatedb OR p.rolcreaterole OR p.oid=(SELECT oid FROM guardian))
  AND NOT EXISTS (SELECT FROM reachable r CROSS JOIN protected p
                  WHERE p.relowner=r.oid OR has_table_privilege(r.oid,p.oid,'DELETE,TRUNCATE,TRIGGER,REFERENCES'))
  AND NOT EXISTS (SELECT FROM protected WHERE relowner<>(SELECT oid FROM guardian)
                  OR has_table_privilege('colab_owner',oid,'DELETE,TRUNCATE,TRIGGER,REFERENCES')
                  OR has_table_privilege('colab_ai_app',oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER,REFERENCES')
                  OR NOT has_table_privilege('colab_owner',oid,'SELECT')
                  OR NOT has_table_privilege('colab_ai_app',oid,'SELECT'))
THEN 'ONTOLOGY_PROTECTED' ELSE 'ONTOLOGY_UNPROTECTED' END;
