import csv
import glob
import os


inglob = '/xchip/tcga/cleanup/whitelists2/cga_home/*.txt'
outfile = '/xchip/tcga/cleanup/whitelists3/cga_home.txt'

in_fns = glob.glob(inglob)
with open(outfile,'w') as ofid:
    writer = csv.writer(ofid,dialect='excel-tab',lineterminator='\n')
    for fn in in_fns:
        fn_list = os.path.basename(fn).split('_')
        with open(fn) as ifid:
            reader = csv.reader(ifid, dialect='excel-tab')
            for line in reader:
                if not line:
                    continue
                path = line[0]
                # if path == '':
                #     continue
                path_list = path.split('/')
                if path_list[2] == 'cga_home':
                    path2 = os.path.join('/xchip/cga_home_new','/'.join(path_list[3:-1]))
                else:
                    path2 = os.path.join('/xchip/cga_home_new',fn_list[0],'/'.join(path_list[2:-1]))

                outline = [path,path2]
                writer.writerow(outline)
