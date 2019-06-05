#!/bin/env python
#
import os
import csv
from collections import Counter
import sys
import re
sys.path.append("/xchip/cga_home/gsaksena/svn/CancerGenomeAnalysis/trunk/Python/util/")
import cga_util
#
# program to take as input a set of file data produced by a file system scanner and produce a report containing
# for each file owner
#  1. a count of the files they own
#  2. total size of the files they own
#  3. counts of the number of files < 100M, >= 100M and < 1G, >= 1G and < 10G, >= 10G
#  4. earliest modified date
#  5. latest modified date
#  6. count of files not readable by "others" or group

def summarize_disk_usage(infile,outfile):
    binList = [1000000,1000000000,10000000000]
    extList = [".csv",".bam","gz","tar"]
    nBins = len(binList)
    with open(infile, 'rU') as csvfile:
        reader = csv.DictReader(f=csvfile,dialect='excel-tab',lineterminator= '\n',quoting=csv.QUOTE_MINIMAL)
        info_by_user = dict()
        try:
	  for row in reader:
            user = row['username']
	    size = int(row['size'])
	    if user not in info_by_user:
	        info_by_user[user] = Counter()
		info_by_user[user]["user"] = user
	    info_by_user[user]["fileCnt"] += 1
	    info_by_user[user]["fileSize"] += size
	    binNo=1
	    for binTop in binList:
	        if size <= binTop:
	            info_by_user[user]["fileCntBin"+str(binNo)] += 1
	            info_by_user[user]["fileSizeBin"+str(binNo)] += size
	            break
	        else:
		    binNo += 1
            if binNo == nBins:
	        info_by_user[user]["fileCntBin"+str(binNo)] += 1
		info_by_user[user]["fileSizeBin"+str(binNo)] += size
	    for ext in extList:
	        regEx = ext + "$"
		if re.search(regEx,row['filepath'],flags=re.IGNORECASE):
		  info_by_user[user]["fileType"+ext] += 1
		  info_by_user[user]["fileTypeSize"+ext] += size
        except:
	  print(row['filepath'])

    #print(info_by_user)
    
    fieldnames = ('user','fileCnt',"fileSize","fileCntBin1","fileCntBin2","fileCntBin3","fileCntBin4","fileSizeBin1","fileSizeBin2","fileSizeBin3","fileSizeBin4","fileType.csv","fileType.bam","fileTypegz","fileTypetar","fileTypeSize.csv","fileTypeSize.bam","fileTypeSizegz","fileTypeSizetar")
    cga_util.dump_dict_table(outfile,info_by_user,fields=fieldnames,ragged_ok = True)
    

if __name__ == '__main__':
    scanFile = sys.argv[1]
    sumFile = sys.argv[2]
    summarize_disk_usage(infile=scanFile,outfile=sumFile)
