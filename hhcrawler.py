#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test HeadHunter API. This script retrieves vacancies and employers
from defined request and store them to database.
For parrallel request to HeadHunter API used gevent.

Requirements:
 - gevent
 - umysql
 - singleton.py
 - dbpool.py

For install requirements you can use pip:
pip install gevent
pip install umysql

For correct application work please execute
next sql queries on your MySQL or MariaDB server
#===============================================================
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
#===============================================================
"""

from hhapi import *
from gevent import monkey, pool
monkey.patch_all()
from dbpool import DBPool
from singleton import singleton


@singleton
class ResourceManager(object):
    def __init__(self, db):
        self.db = db

    def save(self, resource):
        if not (isinstance(resource, ResourceRequest)):
            return False

        data = resource.map_data()
        if not data:
            print "Invalid data: %s" % resource.data["id"]
            return False

        if (isinstance(resource, VacancyResource) and resource.is_outdated):
            sql = "UPDATE %s as vac SET " % resource.table
            sql += ", ".join("%s='%s'" %
                             (field, unicode(value).replace("'", r"\'"))
                             for field, value in data.items())
            sql += " WHERE vac.id=%s" % data["id"]
        else:
            sql = "INSERT INTO %s(" % resource.table
            sql += ", ".join(key for key in data) + ") "
            sql += "VALUES(" + ", ".join("'" +
                                         unicode(value).replace("'", r"\'")
                                         + "'"
                                         for value in data.values()) + ")"
        sql = sql.replace("'NULL'", "NULL")

        return self.db.execute(sql)

    def get_existed_resources(self, ids, resource=VacancyResource):
        if (not hasattr(ids, '__iter__')):
            ids = [ids]

        table = VacancyResource.table if resource == VacancyResource\
            else EmployerResource.table

        sql = "SELECT res.id FROM %s as res WHERE res.id IN(" % table
        sql += ", ".join(unicode(id).replace("'", r"\'") for id in ids) + ")"

        res = self.db.execute(sql)

        if (hasattr(res, 'rows')):
            results = res.rows
            return [row[0] for row in results]
        else:
            return []

    def test_vacancy_outdated(self, vacancy):
        if (hasattr(vacancy, "id") and hasattr(vacancy, "published_at")):
            return False

        sql = "SELECT vac.id FROM %s vac\
               WHERE vac.id = %s\
               AND vac.published_at < '%s'" % (VacancyResource.table,
                                               vacancy["id"],
                                               vacancy["published_at"])
        res = self.db.execute(sql)
        if (hasattr(res, 'rows')):
            results = res.rows
            if (len(results) > 0):
                return results[0]
            else:
                return False
        else:
            return False


@singleton
class ResourceCrawler(object):
    def __init__(self, rm, taskPool):
        self.rm = rm
        self.pool = taskPool

    def crawl_them_all(self, request):
        if not (isinstance(request, APIRequest) and request.execute()):
            return False
        for page in request:
            self.crawl_request(page)

    def crawl_resource(self, resource):
        if not (isinstance(resource, ResourceRequest) and resource.execute()):
            return False
        print "Processing resource: %s, url: %s" % (resource.data["id"],
                                                    resource.url)
        return self.rm.save(resource)

    def crawl_request(self, request):
        if not (isinstance(request, APIRequest) and request.execute()):
            return False

        items = request.data["items"]

        emp_ids = set(map(lambda item: int(item["employer"]["id"]), items))
        existed_emps = set(self.rm.get_existed_resources(emp_ids,
                                                         EmployerResource))
        new_emps = emp_ids - existed_emps

        vac_ids = map(lambda item: int(item["id"]), items)
        existed_ids = self.rm.get_existed_resources(vac_ids)
        new_vacs = filter(lambda item: int(item["id"])
                          not in existed_ids, items)
        existed_vacs = filter(lambda item: int(item["id"])
                              in existed_ids, items)

        resources = []

        for emp in new_emps:
            er = EmployerResource(emp)
            resources.append(er)

        for new in new_vacs:
            vr = VacancyResource(new["id"])
            resources.append(vr)

        for exist in existed_vacs:
            if (self.rm.test_vacancy_outdated(exist)):
                vr = VacancyResource(exist["id"])
                vr.is_outdated = True
                resources.append(vr)

        for resource in resources:
            self.pool.spawn(self.crawl_resource, resource)

        self.pool.join()


###========================================================================
###========================================================================
###========================================================================


if __name__ == "__main__":

    #DB settings
    DB_HOST = "127.0.0.1"
    DB_PORT = 3306
    DB_USER = "root"
    DB_PASS = "123"
    DB_DB = "hhcache"
    DB_POOL_SIZE = 10
    DB_ERROR_REPORTING = True

    #Parrallel requests count to hh api. hh api has limit ~25 req/sec
    TASK_POOL_SIZE = 25

    db_pool = DBPool(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_DB,
                     DB_POOL_SIZE, DB_ERROR_REPORTING)

    task_pool = pool.Pool(TASK_POOL_SIZE)

    rm = ResourceManager(db_pool)
    rc = ResourceCrawler(rm, task_pool)

    vr = VacanciesRequest("Python")

    rc.crawl_them_all(vr)
