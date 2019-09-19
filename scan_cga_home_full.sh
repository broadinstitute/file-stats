#!/usr/bin/env bash

cd /xchip/cga_home

ls -1 | xargs -P 30 -L 1 -I '{}' sudo /sysman/scratch/apsg/alosada/gsaksena/dev/file-stats/catalog_disk_usage.py -o /sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans9_cga_home -r /xchip/cga_home_old/{}

# combine the parts
cd /sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans8_cga_home
tail -n +2 *.files.txt > cga_home_full.txt.part
head -1 xchip_cga_home_AF_temp735789.6257__2019_09_06__06_13_55.files.txt > header.txt
cat header.txt cga_home_full.txt.part > cga_home_full__2019_09_06__06_13_55.files.txt
