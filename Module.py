#!/usr/bin/env python3
import sys


class Module():
    def __init__(self, obj_dict):
        self.module_id = obj_dict['module_id']
        self.course_id = obj_dict['course_id']
        self.category = obj_dict['category']
        self.start = obj_dict['start']
        self.test = 0
        self.children = dict()
        chds = obj_dict['children'].strip().split(' ')
        for chd in chds:
            if chd:
                self.children[chd] = None

    def BuildChildrenRef(self, modules):
        for chd in self.children.keys():
            if chd in modules:
                self.children[chd] = modules[chd]

    def getID(self):
        return self.module_id

    def getCourseID(self):
        return self.course_id

    def getCategory(self):
        return self.category

    def getStart(self):
        return self.start
