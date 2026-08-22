-- 행 수만 맞고 내용이 뒤바뀐 복원을 잡기 위한 내용 지문.
SELECT md5(string_agg(v, '|' ORDER BY v)) FROM (
  SELECT id||name||opened_at::text AS v FROM d1_lab
  UNION ALL SELECT id||lab_id||name||email FROM d1_account
  UNION ALL SELECT account_id||role FROM d2_member_role
  UNION ALL SELECT id||lab_id||owner_account_id||uploader_account_id||coalesce(source_label,'-') FROM d3_dataset
  UNION ALL SELECT dataset_id||name FROM d3_dataset_description
  UNION ALL SELECT id||type||name||status FROM d6_project
  UNION ALL SELECT lab_id||coalesce(university,'-')||coalesce(principal_investigator,'-') FROM d1_lab_profile
  UNION ALL SELECT version_num FROM alembic_version_platform
) s;
