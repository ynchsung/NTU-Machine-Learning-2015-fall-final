#!/usr/bin/env python3
import sys
import csv


def readFeatureFile(pathname):
    with open(pathname, 'rt') as fp:
        cin = csv.reader(fp)
        ret = dict([(row[0], row[1:]) for row in cin])
    return ret


def writeFeatureFile(pathname, features):
    with open(pathname, 'wt') as fp:
        cWriter = csv.writer(fp)
        for feature in features:
            cWriter.writerow(feature)


if __name__ == '__main__':
    a = readFeatureFile(sys.argv[1])
    b = readFeatureFile(sys.argv[2])

    for (x, y) in a.items():
        y += b[x]

    c = [[x] + y for (x, y) in a.items()]
    c.sort(key=lambda x: int(x[0]))
    writeFeatureFile(sys.argv[3], c)
