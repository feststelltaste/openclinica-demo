-- A dump taken while OpenClinica was still starting contains a held Liquibase
-- lock, which would make the application wait for it indefinitely.
UPDATE databasechangeloglock SET locked = false, lockgranted = NULL, lockedby = NULL;
