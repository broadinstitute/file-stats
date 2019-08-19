#!/bin/bash

cd /sysman/scratch/apsg/alosada/gsaksena/dev/file-stats
#for d in abarbera amaro aravi bzhitomi bdanysh birger dheiman eleshch francois gadgetz gsaksena jezike kslowik kyizhak malsaleh mleventh mendy mvinyard marniell omordech ppolak qing rsp benhamo sking sanand zhangt twood ygeffen maruvka
#for d in adunford amartine bknisbac cgaitools danielr dheiman dlivitz eleshch gadgetz igleshch jcha kkubler kyizhak lelagina lmartin muonweb njharlen jhess ospiro sfreeman stewart wroh zlin
for d in adunford amartine bknisbac cgaitools danielr dheiman dlivitz eleshch gadgetz igleshch jcha kkubler kyizhak lelagina lmartin muonweb njharlen jhess ospiro sfreeman stewart wroh zlin abarbera amaro aravi bzhitomi bdanysh birger dheiman eleshch francois gadgetz gsaksena jezike kslowik kyizhak malsaleh mleventh mendy mvinyard marniell omordech ppolak qing rsp benhamo sking sanand zhangt twood ygeffen maruvka
#for d in /cga/fh /xchip/cga_home /cgaext/tcga /cga/fh-new /cga/tcga-gsc /xchip/gdac_data /xchip/tcga_dbgap_data /cga/tcga-gdac /cga/ega_bams /xchip/tcga /xchip/cga1 /cga/nhgri-cip /xchip/tcga_scratch2 /xchip/tcga_gdac_ext /xchip/cga
do
	sudo ./catalog_disk_usage.py -o /sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans7_cga_home -r /xchip/cga_home/$d &
	#sudo ./catalog_disk_usage.py -o /sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans4_cga_home -r $d &
done

