ALTER TABLE User ADD INDEX email_id (email, id);

ALTER TABLE Forum ADD INDEX short_name (short_name);

ALTER TABLE Thread ADD INDEX forum_date (forum, date);

ALTER TABLE Post ADD INDEX forum_date (forum, date);
ALTER TABLE Post ADD INDEX user_date (user, date);
ALTER TABLE Post ADD INDEX thread_date (thread, date);
ALTER TABLE Post DROP PRIMARY INDEX, ADD PRIMARY INDEX (id, thread, date);
