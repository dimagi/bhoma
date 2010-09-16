BEGIN;
ALTER TABLE "phone_synclog" ADD COLUMN "last_seq" integer;
UPDATE "phone_synclog" SET "last_seq" = 0;
COMMIT;