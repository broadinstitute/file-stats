#!/bin/env python
#
import os
import csv
from collections import Counter
import sys
import re
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

def TB_from_bytes(bytes):
    TB = '{size:.2f}'.format(size=bytes/1.1e12)
    return TB


def summarize_disk_usage(infile,outfile):
    binList = [1e6,1e9,1e10,1e11,1e12,1e21]
    binNameList = ["<1 MB","<1 GB","< 10GB","< 100GB","< 1TB","> 1TB"]
    cntBinNameList = ["Cnt " + s for s in binNameList]
    sizeBinNameList = ["Size " + s for s in binNameList]
    TBsizeBinNameList = ["Size " + s + " (TB)" for s in binNameList]
    extList = ["csv","bam","gz","tar"]
    cntExtList = ["Cnt " + s for s in extList]
    sizeExtList = ["Size " + s for s in extList]
    TBsizeExtList = ["Size " + s + " (TB)" for s in extList]
    nBins = len(binList)
    nExts = len(extList)
    with open(infile, 'rU') as csvfile:
        info_by_user = dict()
        reader = csv.DictReader(f=csvfile,dialect='excel-tab',lineterminator= '\n',quoting=csv.QUOTE_MINIMAL)
#        try:
        for row in reader:
            user = row['username']
            size = int(row['size'])
            if user not in info_by_user:
                info_by_user[user] = Counter()
                info_by_user[user]["user"] = user
            info_by_user[user]["fileCnt"] += 1
            info_by_user[user]["fileSize"] += size
            if info_by_user[user]["Last access"] < row["last_access"]:
                info_by_user[user]["Last access"] = row["last_access"]
            if info_by_user[user]["Last modified"] < row["last_modified"]:
                info_by_user[user]["Last modified"] = row["last_modified"]
            for index, binTop in enumerate(binList,start=0):
                if size <= binTop:
                    info_by_user[user][cntBinNameList[index]] += 1
                    info_by_user[user][sizeBinNameList[index]] += size
                    break
            for idx, ext in enumerate(extList,start=0):
                if row['filepath'].lower().endswith(ext):
                  info_by_user[user][cntExtList[idx]] += 1
                  info_by_user[user][sizeExtList[idx]] += size
       # except:
#	  print(row['filepath'])

# normalize
    for user in info_by_user:
        info_by_user[user]["TBfileSize"]='{size:.2f}'.format(size=info_by_user[user]["fileSize"]/1.1e12)
	for idx, bin in enumerate(sizeBinNameList,start=0):
            #info_by_user[user][TBsizeBinNameList[idx]]='{size:.2f}'.format(size=info_by_user[user][sizeBinNameList[idx]]/1.1e12)
            info_by_user[user][TBsizeBinNameList[idx]]=TB_from_bytes(info_by_user[user][sizeBinNameList[idx]])
	for idx, bin in enumerate(sizeExtList,start=0):
            #info_by_user[user][TBsizeExtList[idx]]='{size:.2f}'.format(size=info_by_user[user][sizeExtList[idx]]/1.1e12)
            info_by_user[user][TBsizeExtList[idx]]=TB_from_bytes(info_by_user[user][sizeExtList[idx]])
    
    fieldnames = ["user","fileCnt","fileSize","TBfileSize","Last access","Last modified"]
    fieldnames.extend(cntBinNameList)
    fieldnames.extend(TBsizeBinNameList)
    fieldnames.extend(cntExtList)
    fieldnames.extend(TBsizeExtList)
    fieldnames.extend(sizeBinNameList)
    fieldnames.extend(sizeExtList)
    cga_util.dump_dict_table(outfile,info_by_user,fields=fieldnames,ragged_ok = True)
    #cga_util.dump_dict_table(outfile,info_by_user)
    

if __name__ == '__main__':
    scanFile = sys.argv[1]
    sumFile = sys.argv[2]
    summarize_disk_usage(infile=scanFile,outfile=sumFile)
