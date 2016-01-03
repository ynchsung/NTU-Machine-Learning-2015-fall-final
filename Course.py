#!/usr/bin/env python3
import sys


class Course():
    def __init__(self, course_id):
        self.course_id = course_id
        self.modules = dict()
        self.category_buckets = dict()
        self.structure = None

    def addModule(self, module):
        self.modules[module.getID()] = module
        if not module.getCategory() in self.category_buckets:
            self.category_buckets[module.getCategory()] = dict()
        self.category_buckets[module.getCategory()][module.getID()] = module

    def getCourseModule(self, mid):
        return self.modules.get(mid, None)

    def getCategoryModuleSize(self, cate):
        return len(self.category_buckets.get(cate, {}))
