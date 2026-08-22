SELECT 'd1_lab', count(*) FROM d1_lab
UNION ALL SELECT 'd1_lab_profile', count(*) FROM d1_lab_profile
UNION ALL SELECT 'd1_account', count(*) FROM d1_account
UNION ALL SELECT 'd2_member_role', count(*) FROM d2_member_role
UNION ALL SELECT 'd3_dataset', count(*) FROM d3_dataset
UNION ALL SELECT 'd3_dataset_description', count(*) FROM d3_dataset_description
UNION ALL SELECT 'd6_project', count(*) FROM d6_project
UNION ALL SELECT 'alembic_version_platform', count(*) FROM alembic_version_platform;
