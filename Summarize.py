#!/bin/env python
import os
import csv
from collections import Counter
import sys
#
# program to take as input a set of file data produced by a file system scanner and produce a report containing
# for each file owner
#  1. a count of the files they own
#  2. total size of the files they own
#  3. counts of the number of files < 100M, >= 100M and < 1G, >= 1G and < 10G, >= 10G
#  4. earliest modified date
#  5. latest modified date
#  6. count of files not readable by "others" or group

def summarize_disk_usage(infile):
    sizeBin1=1000000
    sizeBin2=1000000000
    sizeBin3=10000000000
    with open(infile, 'r') as csvfile:
        reader = csv.DictReader(f=csvfile,dialect='excel-tab',lineterminator= '\n',quoting=csv.QUOTE_NONE)
	fileCnt = Counter()
	fileSize = Counter()
	fileSizeBin1 = Counter()
	fileSizeBin2 = Counter()
	fileSizeBin3 = Counter()
	fileSizeBin4 = Counter()
	fileTotSizeBin1 = Counter()
	fileTotSizeBin2 = Counter()
	fileTotSizeBin3 = Counter()
	fileTotSizeBin4 = Counter()
        for row in reader:
            user = row['username']
	    fileCnt[user] += 1
	    fileSize[user] += row['size']
	    if row['size'] <= sizeBin1:
	        fileSizeBin1[user] += 1
	        fileTotSizeBin1[user] += row['size']
	    elif row['size'] <= sizeBin2:
	        fileSizeBin2[user] += 1
	        fileTotSizeBin2[user] += row['size']
	    elif row['size'] <= sizeBin3:
	        fileSizeBin3[user] += 1
	        fileTotSizeBin3[user] += row['size']
	    else:
	        fileSizeBin4[user] += 1
	        fileTotSizeBin4[user] += row['size']
        print(cnt)

    

if __name__ == '__main__':
    scanFile = sys.argv[1]
    summarize_disk_usage(infile=scanFile)
