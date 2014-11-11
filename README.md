HHAPI
=====

Simple client implementation Head Hunter API and retrieve needed information using Gevent for parralel requests

Requirements:
- gevent
- umysql

For install requirements you can use pip:

<code>pip install gevent</code>

<code>pip install umysql</code>

For correct application work please execute
next sql queries on your MySQL or MariaDB server

```sql
CREATE DATABASE `hhcache`;
CREATE TABLE `vacancies` (
`rowid` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`id` INT(10) UNSIGNED NOT NULL,
`name` VARCHAR(150) NOT NULL,
`description` TEXT NOT NULL,
`published_at` DATETIME NOT NULL,
`employer_id` INT(10) UNSIGNED NOT NULL,
`salary_from` INT(10) UNSIGNED NULL DEFAULT NULL,
`salary_to` INT(10) UNSIGNED NULL DEFAULT NULL,
`employment` VARCHAR(150) NULL DEFAULT NULL,
`area` VARCHAR(150) NOT NULL,
`schedule` VARCHAR(150) NULL DEFAULT NULL,
`url` VARCHAR(255) NOT NULL,
`type` VARCHAR(50) NOT NULL,
`experience` VARCHAR(150) NULL DEFAULT NULL,
PRIMARY KEY (`rowid`),
UNIQUE INDEX `uindId` (`id`),
INDEX `indEmployer_id` (`employer_id`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB;
CREATE TABLE `employers` (
`rowid` INT UNSIGNED NOT NULL AUTO_INCREMENT,
`id` INT UNSIGNED NOT NULL,
`name` VARCHAR(150) NOT NULL,
`description` TEXT NOT NULL,
`url` VARCHAR(150) NOT NULL,
`site` VARCHAR(150) NULL,
`logo` VARCHAR(250) NULL,
PRIMARY KEY (`rowid`),
UNIQUE INDEX `uindId` (`id`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB;
```
