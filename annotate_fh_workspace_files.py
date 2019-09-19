import csv
import os
import sys
import glob
import cga_util

indir = '/sysman/scratch/apsg/fh_to_fc/mongo_export_log/2019_08_14-13-35'
in_glob = os.path.join(indir,'*PCAWG*')

# scan_paths = ['/xchip/tcga/cleanup/all_disks_2019-08-08/scans/cga_fh__2019_08_08__10_16_31.annot.files.txt',
#               '/xchip/tcga/cleanup/all_disks_2019-08-08/scans/cgaext_tcga__2019_08_08__10_16_31.annot.files.txt',
#               '/xchip/tcga/cleanup/all_disks_2019-08-08/subsets/xchip_cga_reference__2019_08_09__11_04_15.annot.files.txt',
#               ]
scan_paths = ['/xchip/tcga/cleanup/all_disks_2019-08-08/scans/cga_fh__2019_08_08__10_16_31.annot.files.txt',
              '/xchip/tcga/cleanup/all_disks_2019-08-08/scans/cgaext_tcga__2019_08_08__10_16_31.annot.files.txt',
              '/xchip/tcga/cleanup/all_disks_2019-08-08/scans/xchip_cga__2019_08_09__11_04_15.annot.files.txt',
              '/xchip/tcga/cleanup/all_disks_2019-08-08/scans/xchip_cga_home__2019_08_09__11_01_53.annot.files.txt',
              '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans5/fh_subscription-Getz-PCAWG__2019_08_28__05_58_21.files.txt',
              ]

out_path = '/xchip/tcga/cleanup/all_disks_2019-08-08/subsets/pcawg_workspace_data4.txt'

def fix_filepath(filepath):
    # Replace problematic characters with their escaped version, so the process is fully reversible
    fixed_filepath = ascii(filepath) # escape most problematic chars, eg \n,\r,\t, foreign chars, except quotes
    # space, &, #, etc that are meaningful to the shell are still there, so result will still need to be quoted if sent to the shell.
    fixed_filepath = fixed_filepath[1:-1] # remove surrounding quotes added by ascii()
    # escape single and double quotes left by ascii() in a consistent way that nothing downstream should complain about.
    fixed_filepath = fixed_filepath.replace(r"\'", r"\x27") # case used for sq if dq also in path
    fixed_filepath = fixed_filepath.replace(r"'",  r"\x27") # case used for sq if dq not in path
    fixed_filepath = fixed_filepath.replace(r'\"', r"\x22") # case should never be used
    fixed_filepath = fixed_filepath.replace(r'"',  r"\x22") # dq case
    # commented out comma sub, as it was not done on the 8/8 scan
    #fixed_filepath = fixed_filepath.replace(r',',  r"\x2c") # comma - won't hurt us, but may mess up other downstream stuff

    if filepath != fixed_filepath:
        filepath_escaped = '1'
    else:
        filepath_escaped = '0'

    return fixed_filepath, filepath_escaped




in_paths = glob.glob(in_glob)

print('reading fh lists')
metadata_by_datapath = {}
for in_path in in_paths:
    print (in_path)
    in_fn = os.path.basename(in_path)
    workspace,ext = os.path.splitext(in_fn)
    with open(in_path) as ifid:
        reader = csv.DictReader(ifid,dialect='excel')
        # File_Status,Upload_Status,File_size,File_Type,Annotation_Type,Annotation_Name,Entity_Name,Canonical_Path,Firehose_Path,Object_Uri
        for i,line in enumerate(reader):
            datapath = line['Canonical_Path']
            (datapath_fixed, datapath_escaped) = fix_filepath(datapath)
            metadata_by_datapath[datapath_fixed] = line
            metadata_by_datapath[datapath_fixed]['Workspace_Name'] = workspace

# bad_paths = []
# for datapath in metadata_by_datapath:
#     if 'File_size' not in metadata_by_datapath[datapath]:
#         print ("%s %s"%(datapath,metadata_by_datapath[datapath]))
#         bad_paths.append(datapath)
#
# for bad_path in bad_paths:
#     del metadata_by_datapath[bad_path]

print('joining with disk scans')
for in_path in scan_paths:
    print (in_path)
    with open(in_path) as ifid:
        reader = csv.DictReader(ifid,dialect='excel-tab')
        #filepath        size    last_access     last_modified   username        groupname       group_readable
        # all_readable    symlink nlink       inode   dupe    filepath_escaped
        # fract   cumfract        cumfractcat     ext     ext2    ext3
        for line in reader:
            filepath = line['filepath']
            if filepath in metadata_by_datapath:
                metadata_by_datapath[filepath].update(line)




print('writing output')
fieldnames = ['filepath',
              'size','last_access','last_modified','username','groupname','group_readable','all_readable','symlink',
              'nlink','inode','dupe','filepath_escaped','fract','cumfract','cumfractcat','ext','ext2','ext3',
              'File_Status', 'Upload_Status', 'File_size', 'File_Type', 'Workspace_Name', 'Annotation_Type',
              'Annotation_Name', 'Entity_Name',
              'Canonical_Path', 'Firehose_Path', 'Object_Uri',
              ]
#cga_util.dump_dict_table(out_path,metadata_by_datapath,fields=fieldnames)

datapaths = list(metadata_by_datapath.keys())
datapaths.sort()

with open(out_path,'w') as ofid:
    writer = csv.DictWriter(ofid,dialect='excel-tab',lineterminator='\n',fieldnames=fieldnames)
    writer.writeheader()
    for datapath in datapaths:
        line = metadata_by_datapath[datapath]
        try:
            writer.writerow(line)
        except:
            print(line)
