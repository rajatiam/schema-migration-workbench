ALTER TABLE accounts ADD COLUMN status TEXT NOT NULL DEFAULT 'active';
CREATE INDEX accounts_status ON accounts(status);
