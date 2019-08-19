import csv
import os
import sys
import glob

inglob = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans3/*.files.txt'
#inglob = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans3/cga_fh__2019_08_08__10_16_31.files.txt'
outdir = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/old_but_popular'

inpaths = glob.glob(inglob)
for inpath in inpaths:
    if '.annot.' in inpath:
        continue
    fn = os.path.basename(inpath)
    print(fn)
    outpath = os.path.join(outdir,fn)
    with open(inpath) as ifid:
        with open(outpath,'w') as ofid:
            reader = csv.DictReader(ifid,dialect='excel-tab')
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(ofid,dialect='excel-tab',lineterminator='\n',fieldnames=fieldnames)
            writer.writeheader()
            for line in reader:
                last_access = line['last_access']
                last_modified = line['last_modified']
                last_access_year = last_access[:4]
                last_modified_year = last_modified[:4]
                if last_access_year == '2019' and last_modified_year <= '2017':
                    writer.writerow(line)

