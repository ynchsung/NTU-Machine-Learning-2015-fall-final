#!/usr/bin/env python3
import sys
import csv
import statistics
from datetime import datetime
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
        tmp = [row for row in cin]
        ret = dict([(row[0], row) for row in tmp[1:]])
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
    features.sort(key=lambda x: int(x[0]))
    with open(pathname, 'wt') as fp:
        cWriter = csv.writer(fp)
        for feature in features:
            cWriter.writerow(feature)


def convertDateTime(str_dt):
    dt_obj = datetime.strptime(str_dt, '%Y-%m-%dT%H:%M:%S')
    return dt_obj.timestamp()


def appendFeatures(core, ori_path, log_path, enroll_path, dst_path):
    features = readFeatureFile(ori_path)
    logs = readLogFile(log_path)
    enrolls = readEnrollFile(enroll_path)
    new_features = dict([(a, b + [0.0] * 7) \
                                    for (a, b) in features.items()])

    course_start_time = dict()
    for log_list in logs.values():
        for log in log_list:
            module_obj = core.getModuleByID(log['object'])
            if module_obj:
                course_id = module_obj.getCourseID()
                this_time = convertDateTime(log['time'])
                if not course_id in course_start_time:
                    course_start_time[course_id] = this_time
                elif course_start_time[course_id] > this_time:
                    course_start_time[course_id] = this_time

    miss = 0
    for enroll in enrolls:
        enroll_id = enroll['enrollment_id']
        course_id = enroll['course_id']
        course_obj = core.getCourseByID(course_id)
        start_time = course_start_time.get(course_id, 0.0)

        # new feature 1: duration
        # the distance between last log time and course start time
        duration = 0.0
        # new feature 2: variance
        # the variance of the distance between each log and course start time
        stat = []
        # new feature 3~5: portion of video, vertical, sequential log
        sets = {
            'sequential': set(),
            'vertical': set(),
            'video': set(),
        }
        # new feature 6: score
        # 1pt for access event, 2pt for nagivate event, 3pt for problem event
        score = 0.0
        # new feature 7: total learning time
        last_timestamp = None
        tot_time = 0.0

        for log in logs[enroll_id]:
            module_id = log['object']
            module_obj = course_obj.getCourseModuleByID(module_id)

            if module_obj and (module_obj.getCategory() in sets):
                sets[module_obj.getCategory()].add(module_id)
            if module_obj:
                now_timestamp = convertDateTime(log['time'])
                delta = now_timestamp - start_time
                stat.append(delta)
                duration = delta

                if log['event'] == 'access':
                    score += 1.0
                elif log['event'] == 'nagivate':
                    score += 2.0
                elif log['event'] == 'problem':
                    score += 3.0

                if last_timestamp is None:
                    if log['event'] != 'page_close':
                        last_timestamp = now_timestamp
                elif log['event'] == 'page_close':
                    tot_time += (now_timestamp - last_timestamp)
                    last_timestamp = None

        if enroll_id in new_features:
            new_features[enroll_id][-1] = tot_time
            new_features[enroll_id][-2] = score
            new_features[enroll_id][-3] = float(len(sets['sequential'])) / \
                                course_obj.getCategoryModuleSize('sequential')
            new_features[enroll_id][-4] = float(len(sets['vertical'])) / \
                                course_obj.getCategoryModuleSize('vertical')
            new_features[enroll_id][-5] = float(len(sets['video'])) / \
                                course_obj.getCategoryModuleSize('video')
            if len(stat) < 2:
                new_features[enroll_id][-6] = 0.0
            else:
                new_features[enroll_id][-6] = statistics.variance(stat)
            new_features[enroll_id][-7] = duration
        else:
            miss += 1

    writeFeatureFile(dst_path, list(new_features.values()))
    print('Miss: %d'%(miss,))


def main():
    obj_filepath = 'Data/object.csv'
    if len(sys.argv) >= 2:
        obj_filepath = sys.argv[1]
    core = Core(obj_filepath)
    print('Done', file=sys.stderr)

    '''
    ori_path = 'Data/sample_train_x_1.csv'
    log_path = 'Data/log_train.csv'
    enroll_path = 'Data/enrollment_train.csv'
    dst_path = 'Data/feature_train_new_time_variance_portion_score_totaltime_x.csv'
    '''
    ori_path = 'Data/sample_test_x.csv'
    log_path = 'Data/log_test.csv'
    enroll_path = 'Data/enrollment_test.csv'
    dst_path = 'Data/feature_test_new_time_variance_portion_score_totaltime_x.csv'

    # appending new feature
    appendFeatures(core, ori_path, log_path, enroll_path, dst_path)


if __name__ == '__main__':
    main()
