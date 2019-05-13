import os
import sys
import csv
import pwd
import stat
import collections

#requires use .genetorrent-3.8.3

scr = sys.argv[0]
scr = os.path.abspath(scr)
scr_list = scr.split('/')
util_path = '/'.join(scr_list[:-4] + ['trunk','Python','util'])
sys.path.append(util_path)

import cga_util

def catalog_disk_usage(rootdir, outpath):
    file_info_list = []
    i = 0
    fieldnames = ['filepath','size','ext','last_access','last_modified','username','nlink','inode','parentdir0','parentdir1','parentdir2','parentdir3']

    for (basedir, dirs, fns) in os.walk(rootdir):
        if i == 0:
            fid = open(outpath,'w')
            outdict = csv.DictWriter(fid,dialect='excel-tab',lineterminator= '\n',fieldnames=fieldnames,quoting=csv.QUOTE_NONE)
            outdict.writerow(dict(zip(fieldnames,fieldnames)))
            fid.close()
        elif i%10000 == 0:
            fid = open(outpath,'a')
            outdict = csv.DictWriter(fid,dialect='excel-tab',lineterminator= '\n',fieldnames=fieldnames,quoting=csv.QUOTE_NONE)
            outdict.writerows(file_info_list)
            fid.close()
            file_info_list = []

        if i>1000:
            pass#break
        for fn in fns:
            filepath = os.path.join(basedir,fn)
            if not os.path.isfile(filepath):
                continue
            if os.path.islink(filepath):
                continue
            try:
                statinfo = os.stat(filepath)
            except:
                continue
            filepath = filepath.replace('\n',r'\n')
            ifmt = stat.S_IFMT(statinfo.st_mode)
            nlink = statinfo.st_nlink
            inode = statinfo.st_ino
            inode_str = '"%d"'%inode
            #if not stat.S_ISREG(statinfo.st_mode):
                #continue
            if i % 1000 == 0:
                print(i)
            i += 1
            atime = statinfo.st_atime
            mtime = statinfo.st_mtime
            uid = statinfo.st_uid
            try:
                uid_struct = pwd.getpwuid(uid)
                login_name = uid_struct[0]
                owner = uid_struct[4]
            except:
                login_name = str(uid)
                owner = str(uid)
            formatted_atime = cga_util.get_timestamp(atime)
            formatted_mtime = cga_util.get_timestamp(mtime)
            #size? link/dir/file?
            size = str(statinfo.st_size)
            '''    
            fn_list = fn.split('.')
            file_ext = fn_list[-1]
            
            dir_list = basedir.split('/')
            dir_list = dir_list
            parentdir0 = '/'.join(dir_list)
            if len(dir_list)>1:
                parentdir1 = '/'.join(dir_list[:-1])
            else:
                parentdir1 = 'NA'
            if len(dir_list)>2:
                parentdir2 = '/'.join(dir_list[:-2])
            else:
                parentdir2 = 'NA'
            if len(dir_list)>3:
                parentdir3 = '/'.join(dir_list[:-3])
            else:
                parentdir3 = 'NA'
            pass
            '''
            file_info = {'filepath':filepath, 'size':size, 'ext':file_ext, 
                         'last_access':formatted_atime, 'last_modified':formatted_mtime, 'username':login_name,'nlink':nlink,'inode':inode_str}
                    #     'parentdir0':parentdir0, 'parentdir1':parentdir1, 
                    #     'parentdir2':parentdir2, 'parentdir3':parentdir3}
        
        
            file_info_list.append(file_info)
    # fieldnames = ['filepath','size','ext','last_access','username','nlink','inode','parentdir0','parentdir1','parentdir2','parentdir3']
    # cga_util.dump_dict_table(outpath,file_info_list,fieldnames)

    fid = open(outpath,'a')
    outdict = csv.DictWriter(fid,dialect='excel-tab',lineterminator= '\n',fieldnames=fieldnames,quoting=csv.QUOTE_NONE)
    outdict.writerows(file_info_list)
    fid.close()


if __name__ == '__main__':
    rootdir = sys.argv[1]
    #outpath = sys.argv[2]
    #rootdir = '/cga/fh/pcawg_pipeline'
    #outpath = '/xchip/cga_home/gsaksena/prj/2014/disk_clearing_2014-11-23/cga_fh_pcawg_pipeline_2015-02-20.txt'
    #rootdir = '/cgaext/tcga'
    #outpath = '/xchip/cga_home/gsaksena/prj/2014/disk_clearing_2014-11-23/cgaext_tcga_2015-04-20.txt'
    #rootdir = '/cga/fh'
    #outpath = '/xchip/cga_home/gsaksena/prj/2014/disk_clearing_2014-11-23/cga_fh_2015-03-30.txt'

    #rootdir='/opt2'
    #outpath = '/opt2/usage.txt'
    
    rootdir_cleaned = rootdir.replace('/','_')
    rootdir_cleaned = rootdir_cleaned[1:]
    outpath = '/xchip/cga_home/gsaksena/prj/2014/disk_clearing_2014-11-23/' + rootdir_cleaned + '_' + cga_util.get_timestamp() + '.txt'
    
    catalog_disk_usage(rootdir, outpath)
