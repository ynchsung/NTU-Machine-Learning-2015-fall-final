#!/usr/bin/env python3
import sys
import csv
from Course import Course
from Module import Module


class Core():
    def __init__(self, object_filename):
        self.modules = dict()
        self.courses = dict()
        with open(object_filename, 'rt') as fp:
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


def readFeatureFile(pathname):
    with open(pathname, 'rt') as fp:
        cin = csv.reader(fp)
        ret = dict([(row[0], row) for row in cin])
    return ret


def readLogFile(pathname):
    with open(pathname, 'rt') as fp:
        cDin = csv.DictReader(fp)
        data = [row for row in cDin]

    ret = {}
    for d in data:
        if not d['enrollment_id'] in ret:
            ret[d['enrollment_id']] = []
        ret[d['enrollment_id']].append(d)
    return ret


def readEnrollFile(pathname):
    with open(pathname, 'rt') as fp:
        cDin = csv.DictReader(fp)
        ret = [row for row in cDin]
    return ret


def writeFeatureFile(pathname, features):
    features.sort(key=lambda x: x[0])
    with open(pathname, 'wt') as fp:
        cWriter = csv.writer(fp)
        for feature in features:
            cWriter.writerow(feature)


def appendFeatures(core, ori_path, log_path, enroll_path, dest_path):
    features = readFeatureFile(ori_path)
    logs = readLogFile(log_path)
    enrolls = readEnrollFile(enroll_path)
    new_features = dict([(a, b + [0.0, 0.0, 0.0]) \
                                    for (a, b) in features.items()])

    miss = 0
    for enroll in enrolls:
        enroll_id = enroll['enrollment_id']
        course_id = enroll['course_id']
        course_obj = core.getCourseByID(course_id)
        sets = {
            'sequential': set(),
            'vertical': set(),
            'video': set(),
        }
        for log in logs[enroll_id]:
            module_id = log['object']
            module_obj = course_obj.getCourseModuleByID(module_id)
            if module_obj and (module_obj.getCategory() in sets):
                sets[module_obj.getCategory()].add(module_id)

        if enroll_id in new_features:
            new_features[enroll_id][-1] = float(len(sets['sequential'])) / \
                                course_obj.getCategoryModuleSize('sequential')
            new_features[enroll_id][-2] = float(len(sets['vertical'])) / \
                                course_obj.getCategoryModuleSize('vertical')
            new_features[enroll_id][-3] = float(len(sets['video'])) / \
                                course_obj.getCategoryModuleSize('video')
        else:
            miss += 1

    writeFeatureFile(dest_path, list(new_features.values()))
    print('Miss: %d'%(miss,))


def main():
    obj_filepath = 'Data/object.csv'
    if len(sys.argv) >= 2:
        obj_filepath = sys.argv[1]
    core = Core(obj_filepath)
    print('Done', file=sys.stderr)

    # appending new feature
    appendFeatures(core, 'Data/feature_train_x.csv', 'Data/log_train.csv', \
                    'Data/enrollment_train.csv', 'Data/feature_train2_x.csv')


if __name__ == '__main__':
    main()
