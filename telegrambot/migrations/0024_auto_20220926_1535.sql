-- Add new 'id' column
ALTER TABLE telegrambot_telegrambot ADD COLUMN id SERIAL;

-- Drop old constraints and indexes
ALTER TABLE telegrambot_telegrambot DROP CONSTRAINT telegrambot_telegrambot_pkey CASCADE;
DROP INDEX telegrambot_group_bot_id_c74ddb4b_like;
DROP INDEX telegrambot_telegrambot_token_8ab3980c_like;

-- Set new primary key for telegrambot
ALTER TABLE telegrambot_telegrambot ADD PRIMARY KEY (id);

-- Convert old references with the new primary key
WITH tokens AS (
    SELECT g.id AS g_id, b.id AS b_id
    FROM telegrambot_group g
    JOIN telegrambot_telegrambot b on g.bot_id = b.token
) UPDATE telegrambot_group
    SET bot_id = t.b_id
    FROM tokens t
    WHERE bot_id IS NOT NULL;

-- Convert character varying column to integer
ALTER TABLE telegrambot_group
    ALTER COLUMN bot_id
        TYPE INTEGER
        USING bot_id::INTEGER;

-- Recreate foreign key constraint
ALTER TABLE telegrambot_group
    ADD CONSTRAINT telegrambot_group_bot_id_c74ddb4b_fk_telegramb
        FOREIGN KEY (bot_id) REFERENCES telegrambot_telegrambot
        DEFERRABLE INITIALLY DEFERRED;
