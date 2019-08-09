#!/bin/env python
import os
import sys
import csv

writers_by_key = {}
global fieldnames


def log(key, line, outprefix, datestamp):
    if key is None:
        return
    if key not in writers_by_key:
        path = outprefix + '__' + key + "__" + datestamp + '.txt'
        ofid = open(path, 'w')
        writer = csv.DictWriter(ofid,fieldnames,dialect='excel-tab',lineterminator='\n')
        writer.writeheader()
        writers_by_key[key] = writer
    else:
        writer = writers_by_key[key]

    writer.writerow(line)

def split_scanfile(infile, outprefix, login_by_userid):
    global fieldnames
    # output_test/bams_of_cga_brown__2019_06_11__02_54_43.txt
    datestamp = infile[-24:-4]
    if datestamp[0] != "2":
        raise Exception('Datestamp not found in filename: %s'%infile)

    ifid = open(infile, 'r', encoding='ascii', errors='backslashreplace')
    reader = csv.DictReader(ifid, dialect='excel-tab')
    fieldnames = reader.fieldnames
    #print (fieldnames)
    for i,line in enumerate(reader):
        if i%1000000 == 0:
             print(i)
        username = line['username']
        # fix numeric usernames
        if username in login_by_userid:
            username = login_by_userid[username]
            line['username'] = username
        userkey = 'user_' + username

        filepath = line['filepath']
        filepath_norm = os.path.normpath(filepath)
        filepath_list = filepath_norm.split('/')
        pdir = '/' + '/'.join(filepath_list[:4])
        if os.path.isdir(pdir):
            dirkey = 'dir_' + filepath_list[3]
        else:
            dirkey = None

        log(userkey, line, outprefix, datestamp)
        log(dirkey, line, outprefix, datestamp)

if __name__ == "__main__":
    infile = "/sysman/scratch/apsg/alosada/gsaksena/dev/file-stats/inputs2/xchip_projects02__2019_06_11__02_57_07.txt"
    infile = '/sysman/scratch/apsg/cgahomemeta/Scans/xchip_cga_home___2019_06_14__21_14_52.txt'
    outprefix = '/sysman/scratch/apsg/alosada/gsaksena/dev/file-stats/output_split_cga_home/xchip_cga_home'

    login_by_userid = {}
    username_by_login = {}
    userdb_path = '/sysman/scratch/apsg/alosada/gsaksena/dev/users.csv' #'../users.csv'
    with open(userdb_path) as fid:
        reader = csv.reader(fid,dialect='excel')
        for line in reader:
            login_by_userid[line[0]] = line[1]
            username_by_login[line[1]] = line[2]

    split_scanfile(infile, outprefix, login_by_userid)

