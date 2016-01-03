#!/usr/bin/env python3
import sys
import csv
from Course import Course
from Module import Module


class Core():
    def __init__(self, object_filename):
        self.modules = dict()
        self.courses = dict()
        with open(object_filename, "rt") as fp:
            cDin = csv.DictReader(fp)
            objs = [row for row in cDin]

        for obj in objs:
            new_m = Module(obj)
            if not obj['course_id'] in self.courses:
                self.courses[obj['course_id']] = Course(obj['course_id'])
            self.modules[obj['module_id']] = new_m
            self.courses[obj['course_id']].addModule(new_m)

        for module in self.modules.values():
            module.BuildChildrenRef(self.modules)

    def getModuleByID(self, m_id):
        return self.modules.get(m_id, None)

    def getCourseByID(self, c_id):
        return self.courses.get(c_id, None)


def main():
    obj_filepath = 'Data/object.csv'
    if len(sys.argv) >= 2:
        obj_filepath = sys.argv[1]
    core = Core(obj_filepath)
    print('Done', file=sys.stderr)


if __name__ == '__main__':
    main()
