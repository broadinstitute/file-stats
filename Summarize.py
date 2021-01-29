#!/bin/env python
#
import cProfile
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
    TB = '{size:.3f}'.format(size=bytes/1.1e12)
    return TB



def summarize_disk_usage(infile,outfile,login_by_userid,user_id,username_by_login,tally_extensions):
    binList = [1e6,1e9,1e10,1e11,1e12,1e21]
    binNameList = ["<1M","<1G","<10G","<100G","<1T",">1T"]
    cntBinNameList = ["Cnt" + s for s in binNameList]
    sizeBinNameList = ["Size" + s for s in binNameList]
    TBsizeBinNameList = ["TB" + s for s in binNameList]
    extList = ["csv","bam","gz","tar"]
    cntExtList = ["Cnt" + s for s in extList]
    sizeExtList = ["Size" + s for s in extList]
    TBsizeExtList = ["TB" + s for s in extList]
    day = 60*60*24
    ageBinList = [7*day, 30*day, 90*day, 365*day, 2*365*day,100*365*day]
    ageNameList = ['a<1w','a<1m','a<1q','a<1y','a<2y','a>2y']
    cntAgeNameList = ["Cnt" + s for s in ageNameList]
    sizeAgeNameList = ["Size" + s for s in ageNameList]
    TBsizeAgeNameList = ["TB" + s for s in ageNameList]

    nBins = len(binList)
    nExts = len(extList)
    #now = cga_util.get_datestamp()
    # 6__2019_06_11__02_56_13.txt or 6__2019_06_11__02_56_13.files.txt etc
    #file_datestamp = infile[-24:-4]
    fn_base_base = os.path.basename(infile)
    while '.' in fn_base_base:
        (fn_base_base, ext) = os.path.splitext(fn_base_base)
    file_datestamp = fn_base_base[-20:]

    #print(file_datestamp)
    # assumes tabs and newlines have already been dropped from filenames, though those should trigger an exception later.
    # newline='\n' in the open now causes an exception in DictReader if \r is found in a filename
    # encoding=ascii, errors=backslashreplace filters out other weird characters
    #with open(infile, 'r', newline='\n', encoding='ascii', errors='backslashreplace') as csvfile:
    with open(infile) as csvfile:
        info_by_user = dict()
        reader = csv.DictReader(f=csvfile,dialect='excel-tab')
        for i,row in enumerate(reader):
            if i%1000000 == 0:
                print(i)
                #print(row['filepath'])

            dupe = row.get('dupe','NA')
            if dupe not in ('0','False','NA') : #tolerate missing dupe field
                continue
            uid = row['uid']
            if uid in user_id:
                uid = user_id[uid]
            user = row['username']
            if user in login_by_userid:
                user = login_by_userid[user]
            filepath = row['filepath']
            (root,extension) = os.path.splitext(filepath)
            (root_2,extension_2) = os.path.splitext(root)
            (root_3,extension_3) = os.path.splitext(root_2)
            if extension:
                extension_key = 'zz' + extension.lower()
            else:
                extension_key = None
            if extension_2:
                extension_2_key = extension_key + extension_2.lower()
            else:
                extension_2_key = None
            if extension_3:
                extension_3_key = extension_2_key + extension_3.lower()
            else:
                extension_3_key = None

            # dot_position = filepath.rfind('.')
            # if dot_position != -1:
            #     extension = filepath[dot_position:]
            #     extension_key = "zz" + extension
            # else:
            #     extension_key = None


            log_file(uid, user, row, info_by_user, file_datestamp, login_by_userid, username_by_login, binList,
                     cntBinNameList, sizeBinNameList, extList, cntExtList, sizeExtList, ageBinList, cntAgeNameList,
                     sizeAgeNameList,i)
            log_file("_ALL_", "_ALL_", row, info_by_user, file_datestamp, login_by_userid, username_by_login, binList,
                     cntBinNameList, sizeBinNameList, extList, cntExtList, sizeExtList, ageBinList, cntAgeNameList,
                     sizeAgeNameList,i)
            if tally_extensions:
                if extension_key is not None:
                    log_file(uid, extension_key, row, info_by_user, file_datestamp, login_by_userid, username_by_login, binList,
                             cntBinNameList, sizeBinNameList, extList, cntExtList, sizeExtList, ageBinList, cntAgeNameList,
                             sizeAgeNameList,i)
                if extension_2_key is not None:
                    log_file(uid, extension_2_key, row, info_by_user, file_datestamp, login_by_userid, username_by_login, binList,
                             cntBinNameList, sizeBinNameList, extList, cntExtList, sizeExtList, ageBinList, cntAgeNameList,
                             sizeAgeNameList,i)
                if extension_3_key is not None:
                    log_file(uid, extension_3_key, row, info_by_user, file_datestamp, login_by_userid, username_by_login, binList,
                             cntBinNameList, sizeBinNameList, extList, cntExtList, sizeExtList, ageBinList, cntAgeNameList,
                             sizeAgeNameList,i)



# normalize
    fieldnames = ["uid","user","username","fileCnt","fileSize","TBfileSize","Last access","Last modified"]
    fieldnames.extend(cntBinNameList)
    fieldnames.extend(TBsizeBinNameList)
    fieldnames.extend(cntExtList)
    fieldnames.extend(TBsizeExtList)
    fieldnames.extend(cntAgeNameList)
    fieldnames.extend(TBsizeAgeNameList)
    fieldnames.extend(sizeBinNameList)
    fieldnames.extend(sizeExtList)
    fieldnames.extend(sizeAgeNameList)


    pruned_users = []
    for user in info_by_user:
        info_by_user[user]["TBfileSize"]=TB_from_bytes(info_by_user[user]["fileSize"])
        for idx, bin in enumerate(sizeBinNameList,start=0):
            #info_by_user[user][TBsizeBinNameList[idx]]='{size:.2f}'.format(size=info_by_user[user][sizeBinNameList[idx]]/1.1e12)
            info_by_user[user][TBsizeBinNameList[idx]]=TB_from_bytes(info_by_user[user][sizeBinNameList[idx]])
        for idx, bin in enumerate(sizeExtList,start=0):
            #info_by_user[user][TBsizeExtList[idx]]='{size:.2f}'.format(size=info_by_user[user][sizeExtList[idx]]/1.1e12)
            info_by_user[user][TBsizeExtList[idx]]=TB_from_bytes(info_by_user[user][sizeExtList[idx]])
        for idx, bin in enumerate(sizeAgeNameList,start=0):
            #info_by_user[user][TBsizeExtList[idx]]='{size:.2f}'.format(size=info_by_user[user][sizeExtList[idx]]/1.1e12)
            info_by_user[user][TBsizeAgeNameList[idx]]=TB_from_bytes(info_by_user[user][sizeAgeNameList[idx]])
        # queue up rare extensions for removal, for outside of this loop
        if user.startswith('zz.'):
            if info_by_user[user]['fileCnt'] < 100 and info_by_user[user]['fileSize'] < 1e9:
                pruned_users.append(user)
        # avoid blanks for zero counts in output
        for f in fieldnames:
            if info_by_user[user][f] == 0:
                info_by_user[user][f] = '0'

    for user in pruned_users:
        del info_by_user[user]

    

    cga_util.dump_dict_table(outfile,info_by_user,fields=fieldnames,ragged_ok = True)
    #cga_util.dump_dict_table(outfile,info_by_user)


def log_file(uid, user, row, info_by_user, file_datestamp, login_by_userid, username_by_login, binList, cntBinNameList,
             sizeBinNameList, extList, cntExtList, sizeExtList, ageBinList, cntAgeNameList, sizeAgeNameList, i):

    try:
        size = int(row['size'])
    except:
        # Size ought to be kept in the second column, following filepath, to make this check work well.
        msg = "Size column must be numeric.  Possible newline or tab in filename: %s"%repr(row['filepath'])
        print('row %d: %s'%(i,msg))
        print(row)
        return

    if user not in info_by_user:
        info_by_user[user] = Counter()
        info_by_user[user]["uid"] = uid
        info_by_user[user]["user"] = user
        info_by_user[user]["username"] = username_by_login.get(user, 'NA')
        info_by_user[user]["Last access"] = "0"
        info_by_user[user]["Last modified"] = "0"
    info_by_user[user]["fileCnt"] += 1
    info_by_user[user]["fileSize"] += size
    if info_by_user[user]["Last access"] < row["last_access"] and row["last_access"] < file_datestamp:
        info_by_user[user]["Last access"] = row["last_access"]
    if info_by_user[user]["Last modified"] < row["last_modified"] and row["last_modified"] < file_datestamp:
        info_by_user[user]["Last modified"] = row["last_modified"]
    for index, binTop in enumerate(binList):
        if size <= binTop:
            info_by_user[user][cntBinNameList[index]] += 1
            info_by_user[user][sizeBinNameList[index]] += size
            break
    for idx, ext in enumerate(extList):
        if row['filepath'].lower().endswith(ext):
            info_by_user[user][cntExtList[idx]] += 1
            info_by_user[user][sizeExtList[idx]] += size
            break

    #print(row["last_access"])
    #print(file_datestamp)
    age = cga_util.get_timestamp_delta(row["last_access"], file_datestamp)

    #print(age)
    for index, binTop in enumerate(ageBinList):
        if age <= binTop:
            info_by_user[user][cntAgeNameList[index]] += 1
            info_by_user[user][sizeAgeNameList[index]] += size
            break

if __name__ == '__main__':
    infile = sys.argv[1]

    user_id = {}
    login_by_userid = {}
    username_by_login = {}
    userdb_path = '/sysman/scratch/apsg/alosada/gsaksena/dev/users.csv' #'../users.csv'
    with open(userdb_path) as fid:
        reader = csv.reader(fid,dialect='excel')
        for line in reader:
            login_by_userid[line[0]] = line[1]
            user_id[line[1]] = line[0]  # save the uid
            username_by_login[line[1]] = line[2]

    ext = '.files.txt'
    if not infile.endswith(ext):
        raise Exception('unexpected file extension: %s'%infile)
    outfile = infile[:-len(ext)] + '.summ.txt'
    outfile_part = outfile + '.part'

    tally_extensions = True


    summarize_disk_usage(infile,outfile_part,login_by_userid,user_id,username_by_login, tally_extensions)
    #cProfile.run('summarize_disk_usage(infile,outfile,login_by_userid,username_by_login)')

    os.rename(outfile_part, outfile)