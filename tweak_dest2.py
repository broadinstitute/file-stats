import csv
import glob
import os


inglob = '/xchip/tcga/cleanup/whitelists2/*/*.txt'
outfile = '/xchip/tcga/cleanup/whitelists3/cga_home.txt'



in_fns = glob.glob(inglob)
for fn in in_fns:

    fn_list = fn.split('/')
    list_name = fn_list[-2]
    if list_name == 'cga_home':
        continue
    outfile = '/xchip/tcga/cleanup/whitelists3/' + list_name + '.txt'


    with open(outfile,'w') as ofid:
        writer = csv.writer(ofid,dialect='excel-tab',lineterminator='\n')
        with open(fn) as ifid:
            reader = csv.reader(ifid, dialect='excel-tab')
            for line in reader:
                if not line:
                    continue
                path = line[0]
                # if path == '':
                #     continue
                path_list = path.split('/')
                path2 = '/' + '/'.join([path_list[1],   path_list[2] + "_new"] + path_list[3:-1])


                outline = [path,path2]
                writer.writerow(outline)


