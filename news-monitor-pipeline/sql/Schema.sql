CREATE TABLE IF NOT EXISTS `Snapshot` (
	`snapshot_key` VARCHAR(255) NOT NULL,
	`verlag_id` INTEGER NOT NULL,
	`snapshot_timestamp` DATETIME NOT NULL,
	PRIMARY KEY(`snapshot_key`)
);


CREATE TABLE IF NOT EXISTS `Artikel` (
	`url` VARCHAR(255) NOT NULL,
	`titel` VARCHAR(255) NOT NULL,
	`autor` VARCHAR(255),
	`score` DECIMAL(10,4),
	`datum` DATE,
	`zusammenfassung` VARCHAR(255),
	`text` TEXT,
	PRIMARY KEY(`url`)
);


CREATE TABLE IF NOT EXISTS `Verlag` (
	`id` INTEGER NOT NULL AUTO_INCREMENT,
	`name` VARCHAR(255),
	PRIMARY KEY(`id`)
);


CREATE TABLE IF NOT EXISTS `inhalten_in` (
	`url` VARCHAR(255) NOT NULL,
	`snapshot_key` VARCHAR(255) NOT NULL,
	PRIMARY KEY(`url`, `snapshot_key`)
);


ALTER TABLE `Snapshot`
ADD FOREIGN KEY(`verlag_id`) REFERENCES `Verlag`(`id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `inhalten_in`
ADD FOREIGN KEY(`url`) REFERENCES `Artikel`(`url`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `inhalten_in`
ADD FOREIGN KEY(`snapshot_key`) REFERENCES `Snapshot`(`snapshot_key`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
