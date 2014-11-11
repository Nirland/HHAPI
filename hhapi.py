#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple client implementation Head Hunter API
"""

import urllib
import json
from abc import ABCMeta, abstractmethod


class APIRequest(object):
    baseURL = "https://api.hh.ru/"
    resource = "/"

    def __init__(self):
        self.params = {}
        self.rawParams = []
        self.data = None

    @property
    def url(self):
        url = self.baseURL + self.resource
        if (self.params):
            url += "?" + urllib.urlencode(self.params)
        if (self.rawParams):
            addedParams = "&".join(param for param in self.rawParams)
            url += "&" + addedParams
        return url

    def execute(self):
        try:
            response = urllib.urlopen(self.url)
            if not response.getcode() == 200:
                print response.read()
                return False
            self.data = json.loads(unicode(response.read(), "utf-8"))
            return self.data
        except:
            print "Could not connect to %s" % self.url
            return False


class VacanciesRequest(APIRequest):
    resource = "vacancies/"

    def __init__(self, text, area=(1, 2019), period=7,
                 order_by="publication_time", page=0, per_page=300):
        super(VacanciesRequest, self).__init__()
        self.params["text"] = text.encode("utf-8")
        self.params["period"] = period
        self.params["order_by"] = order_by
        self.params["page"] = page
        self.params["per_page"] = per_page
        self.rawParams.append("&".join("area=%d" % region for region in area))

        self.curpage = -1
        self.numpages = 0
        self.found = 0

    def __iter__(self):
        return self

    def next(self):
        if (not self.found) or (self.curpage == self.numpages - 1):
            raise StopIteration

        self.curpage += 1
        self.params["page"] = self.curpage
        return self

    def execute(self):
        data = super(VacanciesRequest, self).execute()
        if not data:
            return False

        self.numpages = data["pages"]
        self.found = data["found"]
        return data

    @classmethod
    def fromEmployer(cls, id):
        obj = cls.__new__(cls)
        super(VacanciesRequest, obj).__init__()
        obj.params["employer_id"] = str(long(id))
        return obj


class ResourceRequest(APIRequest):
    __metaclass__ = ABCMeta

    table = None

    def __init__(self, id):
        super(ResourceRequest, self).__init__()
        self.resource += str(long(id))

    @abstractmethod
    def map_data(self):
        pass


class VacancyResource(ResourceRequest):
    resource = "vacancies/"
    table = "vacancies"

    def __init__(self, id):
        super(VacancyResource, self).__init__(id)
        self._outdated = False

    @property
    def is_outdated(self):
        return self._outdated

    @is_outdated.setter
    def is_outdated(self, value):
        if (isinstance(value, bool)):
            self._outdated = value

    def map_data(self):
        if not (self.data):
            return False
        try:
            salary = {}
            if (self.data["salary"] is None):
                salary["from"] = "NULL"
                salary["to"] = "NULL"
            else:
                if (self.data["salary"]["from"] is None):
                    salary["from"] = "NULL"
                else:
                    salary["from"] = self.data["salary"]["from"]
                if (self.data["salary"]["to"] is None):
                    salary["to"] = "NULL"
                else:
                    salary["to"] = self.data["salary"]["to"]

            date = self.data["published_at"].replace("T", " ").split("+")[0]

            mapped = {"id": self.data["id"],
                      "name": self.data["name"],
                      "description": self.data["description"],
                      "published_at": date,
                      "employer_id": self.data["employer"]["id"],
                      "salary_from": salary["from"],
                      "salary_to": salary["to"],
                      "employment": self.data["employment"]["name"],
                      "area": self.data["area"]["name"],
                      "schedule": self.data["schedule"]["name"],
                      "url": self.data["alternate_url"],
                      "type": self.data["type"]["id"],
                      "experience": self.data["experience"]["name"]}
            return mapped
        except:
            return False


class EmployerResource(ResourceRequest):
    resource = "employers/"
    table = "employers"

    def map_data(self):
        if not (self.data):
            return False
        try:
            if (self.data["logo_urls"] is not None):
                logo = self.data["logo_urls"].get("240", "NULL")
            else:
                logo = "NULL"

            mapped = {"id": self.data["id"],
                      "name": self.data["name"],
                      "description": self.data["description"],
                      "url": self.data["alternate_url"],
                      "site": self.data["site_url"],
                      "logo": logo}
            return mapped
        except:
            return False


###========================================================================
###========================================================================
###========================================================================


if __name__ == "__main__":
    vr = VacanciesRequest("Python")
    vr.execute()
    for page in vr:
        data = page.execute()
        for resource in data["items"]:
            res = VacancyResource(resource["id"])
            vacancy = res.execute()
            emp = EmployerResource(resource["employer"]["id"])
            employer = emp.execute()
