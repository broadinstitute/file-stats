#!/bin/bash

cd /sysman/scratch/apsg/alosada/gsaksena/dev/file-stats
#for d in abarbera amaro aravi bknisbac bzhitomi bdanysh birger dheiman eleshch francois gadgetz gsaksena jezike jhess kslowik kyizhak malsaleh mleventh mendy mvinyard marniell omordech ppolak qing rsp benhamo sking sanand zhangt twood ygeffen maruvka zlin 
#for d in adunford amartine cgaitools danielr dlivitz igleshch jcha kkubler lelagina lmartin muonweb ospiro sfreeman stewart wroh
for d in /cga/fh /xchip/cga_home /cgaext/tcga /cga/fh-new /cga/tcga-gsc /xchip/gdac_data /xchip/tcga_dbgap_data /cga/tcga-gdac /cga/ega_bams /xchip/tcga /xchip/cga1 /cga/nhgri-cip /xchip/tcga_scratch2 /xchip/tcga_gdac_ext /xchip/cga
do 
	#sudo ./catalog_disk_usage.py -o /sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans2 -r /xchip/cga_home/$d &
	sudo ./catalog_disk_usage.py -o /sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans3 -r $d &
done

