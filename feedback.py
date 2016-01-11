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


def readTruthFile(pathname):
    with open(pathname, 'rt') as fp:
        cin = csv.reader(fp)
        ret = dict([(row[0], int(row[1])) for row in cin])
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


def appendFeedback(core, ori_path, log_path, enroll_path, truth_path, dst_path):
    logs = readLogFile(log_path)
    enrolls = readEnrollFile(enroll_path)
    truth = readTruthFile(truth_path)

    course_start_time = dict()
    enroll_dict = dict()    # map: (enroll_id -> enroll)
    username_logs = dict()      # map: (username -> {enroll_id -> [logs]})

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
            username_logs[enroll['username']] = dict()
        enroll_dict[enroll['enrollment_id']] = enroll
    for (log_enroll_id, log_list) in logs.items():
        tmp_obj = enroll_dict.get(log_enroll_id, None)
        if tmp_obj is None:
            continue
        this_username = tmp_obj['username']
        if this_username and this_username in username_logs:
            if not log_enroll_id in username_logs[this_username]:
                username_logs[this_username][log_enroll_id] = []
            username_logs[this_username][log_enroll_id] += log_list
    for user_logdict in username_logs.values():
        for lst in user_logdict.values():
            lst.sort(key=lambda x:x['time'])

    feedback_feature_lst = dict()

    print('Start calculate')

    for enroll in enrolls:
        enroll_id = enroll['enrollment_id']
        username = enroll['username']
        course_id = enroll['course_id']
        course_obj = core.getCourseByID(course_id)
        start_time = course_start_time.get(course_id, 0.0)
        thirtyone_time = start_time + 86400 * 30 + 1
        forty_time = start_time + 86400 * 40

        # feedback feature
        userlog_feedback_sum = 0.0
        user_alllog = 0.0
        if username in username_logs:
            for (enroll_id2, log_lst) in username_logs[username].items():
                user_alllog += len(log_lst)
                if enroll_id == enroll_id2 or truth[enroll_id2] == 1:
                    continue
                enroll_obj = enroll_dict.get(enroll_id2, None)
                assert(not enroll_obj is None)
                username2 = enroll['username']
                course_id2 = enroll_obj['course_id']
                start_time2 = course_start_time.get(course_id2, 0.0)
                thirtyone_time2 = start_time2 + 86400 * 30 + 1
                forty_time2 = start_time2 + 86400 * 40
                assert(username == username2)

                idx1 = binarySearchTime(log_lst, thirtyone_time, True)
                idx2 = binarySearchTime(log_lst, forty_time, False)
                userlog_feedback_sum += max(idx2 - idx1, 0)

                ll = max(thirtyone_time, thirtyone_time2)
                rr = min(forty_time, forty_time2)
                if rr - ll > 1e-4 and \
                                log_lst[-1]['time'] - log_lst[0]['time'] > 1e-4:
                    time_length = rr - ll
                    density = len(log_lst) / \
                                (log_lst[-1]['time'] - log_lst[0]['time'])
                    userlog_feedback_sum += time_length * density
                    user_alllog += time_length * density

        if user_alllog > 1e-4:
            feedback_feature_lst[enroll_id] = userlog_feedback_sum / user_alllog
        else:
            feedback_feature_lst[enroll_id] = 0.0

    xx = [[int(x), y] for (x, y) in feedback_feature_lst.items()]
    writeFeatureFile(dst_path, xx)


def main():
    obj_filepath = 'Data/object.csv'
    if len(sys.argv) >= 2:
        obj_filepath = sys.argv[1]
    core = Core(obj_filepath)
    print('Done', file=sys.stderr)

    ori_path = 'Data/sample_train_x_1.csv'
    log_path = 'Data/log_train.csv'
    enroll_path = 'Data/enrollment_train.csv'
    truth_path = 'Data/truth_train.csv'
    dst_path = 'Data/FEEDBACK_Portion_train.csv'
    '''
    ori_path = 'Data/sample_test_x.csv'
    log_path = 'Data/log_test.csv'
    enroll_path = 'Data/enrollment_test.csv'
    truth_path = 'Data/truth_test.csv'
    dst_path = 'Data/FEEDBACK_test.csv'
    '''

    # appending new feature
    appendFeedback(core, ori_path, log_path, enroll_path, truth_path, dst_path)


if __name__ == '__main__':
    main()
