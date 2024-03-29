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
        d['time'] = convertDateTime(d['time'])
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


def binarySearchTime(lst, val, eq):
    (l, r) = (0, len(lst))
    while l < r:
        mid = int((l + r) / 2)
        if val > lst[mid]['time']:
            l = mid + 1
        elif val < lst[mid]['time']:
            r = mid
        else:
            if eq:
                r = mid
            else:
                l = mid + 1

    return l


def appendFeatures(core, ori_path, log_path, enroll_path, dst_path):
    features = readFeatureFile(ori_path)
    logs = readLogFile(log_path)
    enrolls = readEnrollFile(enroll_path)
    new_features = dict([(a, b + [0.0] * 7) for (a, b) in features.items()])

    course_start_time = dict()
    enroll_username = dict()    # map: (enroll_id -> username)
    username_logs = dict()      # map: (username -> [logs])

    for log_list in logs.values():
        for log in log_list:
            module_obj = core.getModuleByID(log['object'])
            if module_obj:
                course_id = module_obj.getCourseID()
                this_time = log['time']
                if not course_id in course_start_time:
                    course_start_time[course_id] = this_time
                elif course_start_time[course_id] > this_time:
                    course_start_time[course_id] = this_time

    for enroll in enrolls:
        if not enroll['username'] in username_logs:
            username_logs[enroll['username']] = []
        enroll_username[enroll['enrollment_id']] = enroll['username']

    for (log_enroll_id, log_list) in logs.items():
        this_username = enroll_username.get(log_enroll_id, None)
        if this_username and this_username in username_logs:
            username_logs[this_username] += log_list

    for user_logs in username_logs.values():
        user_logs.sort(key=lambda x:x['time'])

    miss = 0
    for enroll in enrolls:
        enroll_id = enroll['enrollment_id']
        course_id = enroll['course_id']
        course_obj = core.getCourseByID(course_id)
        start_time = course_start_time.get(course_id, 0.0)
        thirtyone_time = start_time + 86400 * 30 + 1
        forty_time = start_time + 86400 * 40

        # new feature 1: duration
        # the distance between last log time and course start time
        duration = 0.0
        # new feature 2: variance
        # the variance of the distance between each log and course start time
        # new feature 3: mean
        # the mean of the distance between each log and course start time
        stat = []
        # new feature 4~6: portion of video, vertical, sequential log
        sets = {
            'sequential': set(),
            'vertical': set(),
            'video': set(),
        }
        # new feature 7: 31 ~ 40 days number of other logs from same username
        (idx1, idx2) = (0, 0)
        # new feature 8: 31 ~ 40 days portion of feature 7 to all logs of the
        #                user
        userlog_portion = 0.0

        if enroll['username'] in username_logs:
            idx1 = binarySearchTime(username_logs[enroll['username']], \
                                                        thirtyone_time, True)
            idx2 = binarySearchTime(username_logs[enroll['username']], \
                                                        forty_time, False)
            if len(username_logs[enroll['username']]) > 0:
                userlog_portion = float(max(0, idx2 - idx1)) / \
                                        len(username_logs[enroll['username']])

        for log in logs[enroll_id]:
            module_id = log['object']
            module_obj = course_obj.getCourseModuleByID(module_id)

            if module_obj and (module_obj.getCategory() in sets):
                sets[module_obj.getCategory()].add(module_id)
            if module_obj:
                now_timestamp = log['time']
                delta = now_timestamp - start_time
                stat.append(delta)
                duration = delta

        if enroll_id in new_features:
            new_features[enroll_id][-1] = userlog_portion
            #new_features[enroll_id][-2] = float(max(0, idx2 - idx1))
            new_features[enroll_id][-2] = float(len(sets['sequential'])) / \
                                course_obj.getCategoryModuleSize('sequential')
            new_features[enroll_id][-3] = float(len(sets['vertical'])) / \
                                course_obj.getCategoryModuleSize('vertical')
            new_features[enroll_id][-4] = float(len(sets['video'])) / \
                                course_obj.getCategoryModuleSize('video')
            if len(stat) == 0:
                new_features[enroll_id][-5] = 0.0
            else:
                new_features[enroll_id][-5] = statistics.mean(stat)

            if len(stat) < 2:
                new_features[enroll_id][-6] = 0.0
            else:
                new_features[enroll_id][-6] = statistics.variance(stat)

            new_features[enroll_id][-7]= duration
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
    dst_path = 'Data/feature_train_N_V_M_P3_OLP_x.csv'
    '''
    ori_path = 'Data/sample_test_x.csv'
    log_path = 'Data/log_test.csv'
    enroll_path = 'Data/enrollment_test.csv'
    dst_path = 'Data/feature_test_N_V_M_P3_OLP_x.csv'

    # appending new feature
    appendFeatures(core, ori_path, log_path, enroll_path, dst_path)


if __name__ == '__main__':
    main()
