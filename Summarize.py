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
        info_by_user = dict()
	for row in reader:
            user = row['username']
	    size = int(row['size'])
	    print(size)
	    if user not in info_by_user:
	        info_by_user[user] = Counter()
	    info_by_user[user]["fileCnt"] += 1
	    info_by_user[user]["fileSize"] += size
	    if size <= sizeBin1:
	        info_by_user[user]["fileCntBin1"] += 1
	        info_by_user[user]["fileSizeBin1"] += size
	    elif size <= sizeBin2:
	        info_by_user[user]["fileCntBin2"] += 1
	        info_by_user[user]["fileSizeBin2"] += size
	    elif size <= sizeBin3:
	        info_by_user[user]["fileCntBin3"] += 1
	        info_by_user[user]["fileSizeBin3"] += size
	    else:
	        info_by_user[user]["fileCntBin4"] += 1
	        info_by_user[user]["fileSizeBin4"] += size
    
    print(info_by_user)

    

if __name__ == '__main__':
    scanFile = sys.argv[1]
    summarize_disk_usage(infile=scanFile)
