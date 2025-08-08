-- Migration: convert filters.model/backdrop to TEXT[]
BEGIN;
ALTER TABLE filters
  ALTER COLUMN model TYPE TEXT[] USING (CASE WHEN model IS NULL OR model = '' THEN NULL ELSE ARRAY[model] END),
  ALTER COLUMN backdrop TYPE TEXT[] USING (CASE WHEN backdrop IS NULL OR backdrop = '' THEN NULL ELSE ARRAY[backdrop] END);
DROP INDEX IF EXISTS idx_filters_combo;
CREATE INDEX IF NOT EXISTS idx_filters_combo_arr ON filters (collection);
COMMIT;