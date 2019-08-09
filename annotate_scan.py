#!/bin/env python

import csv
import os
import sys
import subprocess







def annot_file_scan(infile, tmpdir):
    infile_ext = '.files.txt'
    if not infile.endswith(infile_ext):
        raise Exception('bad file extension %s'%infile)

    infile_fn = os.path.basename(infile)[:-len(infile_ext)]
    infile_dir = os.path.dirname(infile)
    tmppath1 = os.path.join(tmpdir, infile_fn + '.sorted.files.txt')
    outpath = os.path.join(infile_dir, infile_fn + '.annot.files.txt')
    outpath_part = outpath + '.part'

    # reverse numeric sort tsv file by 2nd column, starting after header line
    # cmdline sort tolerates huge files
    cmdstr = r"head -1 %s > %s && cat %s | tail -n +2 | sort -k2nr,2nr -t$'\t' -T%s >> %s"%(infile, tmppath1, infile,tmpdir,tmppath1)
    subprocess.check_call(cmdstr,shell=True)

    total_size = 0

    with open(tmppath1) as ifid:
        reader = csv.DictReader(ifid, dialect='excel-tab')
        fieldnames_infile = reader.fieldnames
        for line in reader:
            sz_str = line['size']
            sz = int(sz_str)
            total_size += sz

    fieldnames_outfile = fieldnames_infile + ['fract', 'cumfract', 'cumfractcat', 'ext', 'ext2', 'ext3']
    cumsize = 0
    cats = [99.9, 99, 95, 90, 80, 0] #sorted by how common each category is
    cat_str_by_cat = {99.9: '100', 99:'99.9', 95:'99', 90:'95', 80:'90', 0:'80'} #note offset bins
    with open(tmppath1) as ifid:
        with open(outpath_part, 'w') as ofid:
            reader = csv.DictReader(ifid, dialect='excel-tab')
            writer = csv.DictWriter(ofid, dialect='excel-tab', lineterminator='\n', fieldnames = fieldnames_outfile)
            writer.writeheader()
            for line in reader:
                sz = float(line['size'])
                cumsize += sz
                fract = sz/total_size
                cumfract = cumsize/total_size
                cumfract_percent = cumfract * 100
                fract_str = "%7.4f"%fract
                cumfract_str = "%7.4f"%cumfract

                if cumfract_percent >= 99.9: #common case
                    cumfractcat = 99.9
                else:
                    for c in cats:
                        if c < cumfract_percent:
                            cumfractcat = c
                            break
                cumfractcat_str = cat_str_by_cat[cumfractcat]

                base_name = os.path.basename(line['filepath'])
                (root,extension) = os.path.splitext(base_name)
                (root_2,extension_2) = os.path.splitext(root)
                (root_3,extension_3) = os.path.splitext(root_2)
                if extension:
                    ext_str = extension.lower()
                else:
                    ext_str = 'NA'
                if extension_2:
                    ext2_str = ext_str + extension_2.lower()
                else:
                    ext2_str = 'NA'
                if extension_3:
                    ext3_str = ext2_str + extension_3.lower()
                else:
                    ext3_str = 'NA'

                line.update(fract=fract_str, cumfract=cumfract_str, cumfractcat = cumfractcat_str, ext=ext_str, ext2=ext2_str, ext3=ext3_str)
                writer.writerow(line)


    os.rename(outpath_part, outpath)


def annot_dir_scan(infile, tmpdir):
    infile_ext = '.dirs.txt'
    if not infile.endswith(infile_ext):
        raise Exception('bad file extension %s' % infile)

    infile_fn = os.path.basename(infile)[:-len(infile_ext)]
    infile_dir = os.path.dirname(infile)
    tmppath1 = os.path.join(tmpdir, infile_fn + '.sorted.dirs.txt')
    outpath = os.path.join(infile_dir, infile_fn + '.annot.dirs.txt')
    outpath_part = outpath + '.part'

    # reverse numeric sort tsv file by 2nd column, starting after header line
    # cmdline sort tolerates huge files
    cmdstr = r"head -1 %s > %s && cat %s | tail -n +2 | sort -k2nr,2nr -t$'\t' -T%s >> %s" % (
    infile, tmppath1, infile, tmpdir, tmppath1)
    subprocess.check_call(cmdstr, shell=True)

    total_size = 0

    with open(tmppath1) as ifid:
        reader = csv.DictReader(ifid, dialect='excel-tab')
        fieldnames_infile = reader.fieldnames
        for line in reader:
            sz_str = line['size']
            sz = int(sz_str)
            total_size += sz
            break # top item is total, since sizes are all cumulative

    fieldnames_outfile = fieldnames_infile + ['fract', 'fractcat']
    cumsize = 0
    cats = [99.9, 99, 95, 90, 80, 0]  # sorted by how common each category is
    cat_str_by_cat = {99.9: '100', 99: '99.9', 95: '99', 90: '95', 80: '90', 0: '80'}  # note offset bins
    with open(tmppath1) as ifid:
        with open(outpath_part, 'w') as ofid:
            reader = csv.DictReader(ifid, dialect='excel-tab')
            writer = csv.DictWriter(ofid, dialect='excel-tab', lineterminator='\n', fieldnames=fieldnames_outfile)
            writer.writeheader()
            for line in reader:
                sz = float(line['size'])
                fract = sz / total_size
                fract_percent = 100 - fract * 100
                fract_str = "%7.4f" % fract

                if fract_percent >= 99.9:  # common case
                    fractcat = 99.9
                else:
                    for c in cats:
                        if c <= fract_percent:
                            fractcat = c
                            break
                fractcat_str = cat_str_by_cat[fractcat]


                line.update(fract=fract_str, fractcat=fractcat_str)
                writer.writerow(line)

    os.rename(outpath_part, outpath)



# infile = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans2/xchip_cga_home_gadgetz__2019_08_07__11_21_13.dirs.txt'

infile = sys.argv[1]

username = os.getenv('USER')
tmpdir = '/broad/hptmp/' + username
os.makedirs(tmpdir,exist_ok = True)

if infile.endswith('.files.txt'):
    annot_file_scan(infile, tmpdir)
elif infile.endswith('.dirs.txt'):
    annot_dir_scan(infile, tmpdir)