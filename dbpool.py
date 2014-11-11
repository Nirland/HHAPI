#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple DB pool for parallel db requests from greenlets
"""

from gevent.queue import Queue
import sys
import umysql


class DBPool(object):
    def __init__(self, DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_DB,
                 size=10, error_reporting=False):
        self.pool = Queue()

        for i in range(size):
            con = umysql.Connection()
            try:
                con.connect(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_DB)
                self.pool.put_nowait(con)
            except:
                sys.exit("Could not connect to database")
        self.error_reporting = error_reporting

    def execute(self, sql, params=()):
        con = self.pool.get()
        res = False
        try:
            if (params):
                res = con.query(sql, params)
            else:
                res = con.query(sql)
        except umysql.SQLError, e:
            if self.error_reporting:
                print "Code: %s\nMessage: %s\nSQL: %s\n"\
                    % (e[0], e[1], sql.encode("utf-8"))
        finally:
            self.pool.put_nowait(con)
        return res

    def __del__(self):
        self.close()

    def close(self):
        while not self.pool.empty():
            con = self.pool.get_nowait()
            con.close()
