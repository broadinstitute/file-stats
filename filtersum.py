#!/bin/env python

import csv

fid = open('/sysman/scratch/apsg/cgahomemeta/Scans/xchip_cga_home___2019_06_14__21_14_52.txt')
indict = csv.DictReader(fid,dialect='excel-tab')
total_size = 0
subdirs = (
'aarong',
'adunford',
'amaro',
'amartine',
'aravi',
'bknisbac',
'cgaitools',
'chanc',
'danielr',
'dheiman',
'dlivitz',
'eleshch',
'esther',
'gadgetz',
'hallei',
'igleshch',
'jaegil',
'jcha',
'jhess',
'kkubler',
'kyizhak',
'lelegina',
'lmartin',
'marniell',
'maruvka',
'mhanna',
'mleventh',
'mleventhal',
'mnoble',
'ospiro',
'ozm',
'sfreeman',
'stewart',
'timdef',
'twood',
'wroh',
'zlin')
for i,line in enumerate(indict):
	path = line['filepath']
	size = line['size']
	dupe = line['dupe']
	path_list = path.split('/')
	if len(path_list)>4 and path_list[4] in subdirs and dupe != 'True':
		total_size += int(size)
	if i%1000000 == 0:
		print (i/1e6)
print ('%d  %7.3f'%(total_size,total_size/1.1e12))


