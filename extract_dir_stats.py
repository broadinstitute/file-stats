#!/bin/env python

import csv
import os
import sys
import subprocess
import cga_util
import math
import datetime
import cProfile

def annot_file_scan(infile, tmpdir):
    infile_ext = '.files.txt'
    if not infile.endswith(infile_ext):
        raise Exception('bad file extension %s'%infile)

    fn_base_base = os.path.basename(infile)
    while '.' in fn_base_base:
        (fn_base_base, ext) = os.path.splitext(fn_base_base)
    scan_datestamp = fn_base_base[-20:]

    infile_fn = os.path.basename(infile)[:-len(infile_ext)]
    infile_dir = os.path.dirname(infile)
    tmppath1 = os.path.join(tmpdir, infile_fn + '.sorted.files.txt')
    tmppath2 = os.path.join(tmpdir, infile_fn + '.unsorted.dirs.txt')

    outpath = os.path.join(infile_dir, infile_fn + '.dirs2.txt')
    outpath_part = outpath + '.part.txt'

    # forward ascii sort based on 1st column, starting after header line
    # this puts tree in top-down order
    # cmdline sort tolerates huge files
    print ('sorting files')
    sort_column = 1
    sort_tsv_file(infile, tmppath1, tmpdir, sort_column)


    print('building/walking dir tree')
    dirinfo_by_dirlevel_by_dir = []
    total_size = 0

    with open(tmppath1) as ifid:
        with open(tmppath2,'w') as ofid:
            reader = csv.DictReader(ifid, dialect='excel-tab')
            fieldnames_infile = reader.fieldnames
            fieldnames_outfile = get_output_header()
            writer = csv.DictWriter(ofid,dialect='excel-tab',lineterminator='\n',fieldnames=fieldnames_outfile)
            writer.writeheader()
            linenum = 0
            for fileinfo in reader:
                if linenum%10000 == 0:
                    print('%dk'%(linenum/1000))
                linenum += 1

                filepath = fileinfo['filepath']
                filepath_list = filepath.split('/')

                #find dirs that are done
                for i in range(len(dirinfo_by_dirlevel_by_dir)):
                    if i > len(filepath_list) - 1:
                        break
                    dir_path = '/'.join(filepath_list[:i + 1])
                    if dir_path not in dirinfo_by_dirlevel_by_dir[i]:
                        break
                else:
                    i=len(dirinfo_by_dirlevel_by_dir)
                prune_level = i+1 # +1 because the subdir's parent needs to be done before we process the subdir

                process_finished_dirs(writer, dirinfo_by_dirlevel_by_dir, prune_level)

                #populate new dirs
                for i in range(len(filepath_list)-1):
                    if len(dirinfo_by_dirlevel_by_dir) <= i:
                        dirinfo_by_dirlevel_by_dir.append({})
                    process_new_file(filepath_list, i, fileinfo, dirinfo_by_dirlevel_by_dir, scan_datestamp)

            # flush remaining directories
            process_finished_dirs(writer, dirinfo_by_dirlevel_by_dir, 1)
    # tree was written in bottom-up order, resort to make it top-down again
    print('sorting dirs')
    sort_tsv_file(tmppath2,outpath_part,tmpdir,sort_column)
    os.rename(outpath_part, outpath)


def sort_tsv_file(infile, outfile, tmpdir, sort_column):
    cmdstr = r"export LC_ALL=C && head -1 %s > %s && cat %s | tail -n +2 | sort -k%d,%d -t$'\t' -T%s >> %s" % (
        infile, outfile, infile, sort_column, sort_column, tmpdir, outfile)
    subprocess.check_call(cmdstr, shell=True)


def process_finished_dirs(writer, dirinfo_by_dirlevel_by_dir, prune_level):
    # process dirs that are done
    prune_levels = range(prune_level, len(dirinfo_by_dirlevel_by_dir))

    for level in reversed(prune_levels):
        dirs = list(dirinfo_by_dirlevel_by_dir[level].keys())
        dirs.sort()
        for dir in dirs:
            # get struct for this dir
            dirinfo = dirinfo_by_dirlevel_by_dir[level][dir]
            if dirinfo['done']:
                continue

            # get list of structs of its immediate child dirs
            if len(dirinfo_by_dirlevel_by_dir) > level + 1:
                potential_child_dirinfos = dirinfo_by_dirlevel_by_dir[level + 1]
            else:
                potential_child_dirinfos = []
            child_dirinfos = []
            child_dirs = []
            for potential_child_dir in potential_child_dirinfos:
                if potential_child_dirinfos[potential_child_dir]['parent_dir'] == dir:
                    child_dirs.append(potential_child_dir)
                    child_dirinfos.append(potential_child_dirinfos[potential_child_dir])

            # get struct for parent of this dir
            parent_dir = dirinfo['parent_dir']
            parent_dirinfo = dirinfo_by_dirlevel_by_dir[level - 1][parent_dir]

            # compute final dir stats
            line = process_finished_dir(dirinfo, child_dirinfos, parent_dirinfo, level)
            writer.writerow(line)

            # delete immediate children right after dir is processed, to save RAM; leave dir itself for its own parent.
            # mark it done so it doesn't get processed/printed again
            for child_dir in child_dirs:
                del dirinfo_by_dirlevel_by_dir[level + 1][child_dir]
            dirinfo['done'] = True


def process_new_file(filepath_list, dirlevel, fileinfo, dirinfo_by_dirlevel_by_dir, scan_datestamp):
    dir_path = '/'.join(filepath_list[:dirlevel + 1])
    if dir_path not in dirinfo_by_dirlevel_by_dir[dirlevel]:
        # first time encountering this directory, so need to create a new record for it.
        parent_dir = '/'.join(filepath_list[:dirlevel])
        dirinfo_by_dirlevel_by_dir[dirlevel][dir_path] = get_initial_dirinfo(dir_path, parent_dir)
    # extract just the stuff tally_new_file() needs to know
    dirinfo = dirinfo_by_dirlevel_by_dir[dirlevel][dir_path]
    file_level = len(filepath_list)-2
    is_terminal_node = dirlevel == file_level
    tally_new_file(fileinfo, is_terminal_node, dirinfo, scan_datestamp, file_level)



def get_age_old(this_time, ref_time):
    # return age, as integer representing number of days since ref_time
    # TBD tweak alg such that files with same date have same age regardless of the time component.
    sec_per_day = 60.0 * 60 * 24
    age_secs_float = cga_util.get_timestamp_delta(this_time, ref_time)
    age_days_int = int(min(1, math.floor(age_secs_float / sec_per_day)))
    return age_days_int

age_cache = {}
def get_age(this_time, ref_time):
    # intentionally ignore time, to make files from the same day have an identical age
    # return as an integer number of days
    age_key = this_time + ref_time
    # use cache - this code seems to be unexpectedly time consuming
    age_days = age_cache.get(age_key)
    if age_days is None:

        (this_year, this_month, this_day, junk, this_hour, this_minute, this_second) = this_time.split('_')
        (ref_year, ref_month, ref_day, junk, ref_hour, ref_minute, ref_second) = ref_time.split('_')

        # presume midnight
        this_dt = datetime.datetime(int(this_year), int(this_month), int(this_day), 0, 0, 0)
        # presume 11:59pm
        ref_dt = datetime.datetime(int(ref_year), int(ref_month), int(ref_day), 0, 0, 0)

        this_days = this_dt.toordinal()
        this_ref = ref_dt.toordinal()
        age_days = this_ref - this_days

        age_cache[age_key] = age_days
    return age_days


#####################
#####################
def get_initial_dirinfo(dir_path, parent_dir):
    return {'parent_dir': parent_dir, 'dir_path': dir_path,
            'total_filecount': 0, 'total_size': 0,
            'total_lastaccess': '', 'total_lastmodified': '',
            'total_age_lastaccess':1234567, 'total_age_lastmodified':1234567, #set initial min age very large
            'this_filecount': 0, 'this_size': 0,
            'sum_age_lastaccess':0, 'sum_age_lastmodified':0,'sum_age_lastaccess_squared':0, 'sum_age_lastmodified_squared':0,
            'max_level':0,
            'done': False}

def get_output_header():
    # gives field names and their ordering used in the output file.
    fieldnames_outfile = ['dir', 'size', 'sizeTB', 'numfiles', 'dir_level','max_dir_level', 'tc2mc_size','tc2mc_numfiles',
                          'last_access', 'last_modified',
                          'age_access', 'age_modified',
                         'own_numfiles', 'own_size', 'own_numdirs',
                          'age_access_mean', 'age_access_stdev', 'age_modified_mean', 'age_modified_stdev',
                          'access_mean_age_vs_parent','modified_mean_age_vs_parent','access_min_age_vs_parent','modified_min_age_vs_parent',
                          'children_size','max_child_size',
                          'children_numfiles','max_child_numfiles']
    return fieldnames_outfile



def tally_new_file(fileinfo, is_terminal_node, dirinfo, scan_datestamp, file_level):
    # add current file's info to its dirs
    # fileinfo fields are those found in the .files.txt input file
    # dirinfo fields need to be understood by process_finished_dir(), and are initialized by get_initial_dirinfo()
    dirinfo['total_filecount'] += 1
    dirinfo['total_size'] += int(fileinfo['size'])
    last_access = fileinfo['last_access']
    last_modified = fileinfo['last_modified']
    dirinfo['total_lastaccess'] = max(dirinfo['total_lastaccess'], last_access)
    dirinfo['total_lastmodified'] = max(dirinfo['total_lastmodified'], last_modified)
    dirinfo['max_level'] = max(dirinfo['max_level'],file_level)

    days_access = get_age(last_access, scan_datestamp)
    days_modified = get_age(last_modified, scan_datestamp)
    dirinfo['total_age_lastaccess'] = min(dirinfo['total_age_lastaccess'],days_access)
    dirinfo['total_age_lastmodified'] = min(dirinfo['total_age_lastmodified'],days_modified)
    # collect stats to compute mean and stdev on age
    dirinfo['sum_age_lastaccess'] += days_access
    dirinfo['sum_age_lastmodified'] += days_modified
    dirinfo['sum_age_lastaccess_squared'] += days_access * days_access
    dirinfo['sum_age_lastmodified_squared'] += days_modified * days_modified


    if is_terminal_node:
        dirinfo['this_filecount'] += 1
        dirinfo['this_size'] += int(fileinfo['size'])





def process_finished_dir(dirinfo, child_dirinfos, parent_dirinfo, level):
    # dirinfo fields written by tally_new_file()
    # line fields need to mesh with get_output_header()

    # compute ratio of all children to biggest child
    max_child_size = 0
    total_child_size = 0
    max_child_numfiles = 0
    total_child_numfiles = 0
    for child_dirinfo in child_dirinfos:
        child_size = child_dirinfo['total_size']
        total_child_size += child_size
        max_child_size = max(max_child_size, child_size)

        child_numfiles = child_dirinfo['total_filecount']
        total_child_numfiles += child_numfiles
        max_child_numfiles = max(max_child_numfiles, child_numfiles)
    if max_child_size > 0:
        tc2mc_size_float = float(total_child_size) / max_child_size
        tc2mc_size = '%7.3f'%tc2mc_size_float
        tc2mc_count_float = float(total_child_numfiles) / max_child_numfiles
        tc2mc_count = '%7.3f'%tc2mc_count_float
    else:
        tc2mc_size = 'NA'
        tc2mc_count = 'NA'

    owndirs = len(child_dirinfos)

    total_filecount = dirinfo['total_filecount']
    if total_filecount > 0:
        # calc mean stats on dir
        sum_age_lastaccess = dirinfo['sum_age_lastaccess']
        sum_age_lastmodified = dirinfo['sum_age_lastmodified']
        age_access_mean_float =  float(sum_age_lastaccess) / total_filecount
        age_modified_mean_float = float(sum_age_lastmodified) / total_filecount
        age_access_mean = '%4.1f'%age_access_mean_float
        age_modified_mean = '%4.1f'%age_modified_mean_float

        # calc mean stats on parent, which will be complete by now
        parent_sum_age_lastaccess = parent_dirinfo['sum_age_lastaccess']
        parent_sum_age_lastmodified = parent_dirinfo['sum_age_lastmodified']
        parent_total_filecount = parent_dirinfo['total_filecount']
        #parent_age_access_mean_float =  float(parent_sum_age_lastaccess) / parent_total_filecount
        #parent_age_modified_mean_float = float(parent_sum_age_lastmodified) / parent_total_filecount
        # calc avg of parent ages while excluding current dir
        if parent_total_filecount > total_filecount:
            parent_age_access_mean_float =  (float(parent_sum_age_lastaccess) - sum_age_lastaccess) / (parent_total_filecount - total_filecount)
            parent_age_modified_mean_float = (float(parent_sum_age_lastmodified) - sum_age_lastmodified) / (parent_total_filecount - total_filecount)
        else:
            parent_age_access_mean_float = age_access_mean_float
            parent_age_modified_mean_float = age_modified_mean_float

        access_mean_age_vs_parent_float = age_access_mean_float - parent_age_access_mean_float
        modified_mean_age_vs_parent_float = age_modified_mean_float - parent_age_modified_mean_float
        access_mean_age_vs_parent = '%4.1f'%access_mean_age_vs_parent_float
        modified_mean_age_vs_parent = '%4.1f'%modified_mean_age_vs_parent_float
    else:
        raise Exception('expected to have at least one descendent file somewhere')
        # age_access_mean = 'NA'
        # age_modified_mean = 'NA'


    access_min_age_vs_parent = dirinfo['total_age_lastaccess'] - parent_dirinfo['total_age_lastaccess']
    modified_min_age_vs_parent = dirinfo['total_age_lastmodified'] - parent_dirinfo['total_age_lastmodified']

    if total_filecount > 1:
        # calc std stats on dir
        sum_age_lastaccess_squared = dirinfo['sum_age_lastaccess_squared']
        sum_age_lastmodified_squared = dirinfo['sum_age_lastmodified_squared']
        age_access_stdev_float = math.sqrt((float(total_filecount) * sum_age_lastaccess_squared - sum_age_lastaccess * sum_age_lastaccess) / (total_filecount * (total_filecount-1)))
        age_modified_stdev_float = math.sqrt((float(total_filecount) * sum_age_lastmodified_squared - sum_age_lastmodified * sum_age_lastmodified) / (total_filecount * (total_filecount-1)))
        age_access_stdev = '%4.1f'%age_access_stdev_float
        age_modified_stdev = '%4.1f'%age_modified_stdev_float
    else:
        age_access_stdev = 'NA'
        age_modified_stdev = 'NA'

    line = {'dir': dirinfo['dir_path'],
            'numfiles': dirinfo['total_filecount'],
            'size':dirinfo['total_size'],
            'sizeTB':'%7.3f'%(float(dirinfo['total_size']) / 1.1e12),
            'last_access':dirinfo['total_lastaccess'],
            'last_modified':dirinfo['total_lastmodified'],
            'own_numfiles':dirinfo['this_filecount'],
            'own_size':dirinfo['this_size'],
            'children_size': total_child_size,
            'max_child_size': max_child_size,
            'tc2mc_size': tc2mc_size,
            'dir_level':level,
            'own_numdirs':owndirs,
            'children_numfiles': total_child_numfiles,
            'max_child_numfiles': max_child_numfiles,
            'tc2mc_numfiles': tc2mc_count,
            'age_access':dirinfo['total_age_lastaccess'],
            'age_modified':dirinfo['total_age_lastmodified'],
            'age_access_mean':age_access_mean,
            'age_access_stdev':age_access_stdev,
            'age_modified_mean':age_modified_mean,
            'age_modified_stdev':age_modified_stdev,
            'access_mean_age_vs_parent':access_mean_age_vs_parent,
            'modified_mean_age_vs_parent':modified_mean_age_vs_parent,
            'access_min_age_vs_parent':access_min_age_vs_parent,
            'modified_min_age_vs_parent':modified_min_age_vs_parent,
            'max_dir_level':dirinfo['max_level']

            }
    return line

####################
####################

def main():
    infile = sys.argv[1]

    username = os.getenv('USER')
    tmpdir = '/broad/hptmp/' + username
    os.makedirs(tmpdir,exist_ok = True)

    #infile = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/dirscan/xchip_cga_home_marniell__2019_08_07__11_21_14.files.txt'
    # infile = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/dirscan/xchip_pandora__2019_08_28__10_19_55.files.txt'
    # infile = '/sysman/scratch/apsg/meyerson-stats/old/cga_meyerson__2019_08_20__13_48_36.files.txt'
    # tmpdir = '/broad/hptmp/gsaksena'
    annot_file_scan(infile, tmpdir)

if __name__ == '__main__':
    main()

    #cProfile.run('main()')