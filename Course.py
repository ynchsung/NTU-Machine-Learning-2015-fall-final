#!/usr/bin/env python3
import sys


class Course():
    def __init__(self, course_id):
        self.course_id = course_id
        self.modules = dict()
        self.structure = None

    def addModule(self, module):
        self.modules[module.getID()] = module
