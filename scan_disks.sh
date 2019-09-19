#!/bin/bash

cd /sysman/scratch/apsg/alosada/gsaksena/dev/file-stats
#for d in /cga/fh /xchip/cga_home /cgaext/tcga /cga/fh-new /cga/tcga-gsc /xchip/gdac_data /xchip/tcga_dbgap_data /cga/tcga-gdac /cga/ega_bams /xchip/tcga /xchip/cga1 /cga/nhgri-cip /xchip/tcga_scratch2 /xchip/tcga_gdac_ext /xchip/cga

#for d in /xchip/tcga_old /xchip/gdac_data_old /cga/fh_old /cgaext/tcga_old /cgaext/tcga /cga/fh-new_old /cga/tcga-gsc_old /xchip/tcga_dbgap_data_old /cga/tcga-gdac_old /cga/ega_bams_old /cga/nhgri-cip_old /xchip/tcga_scratch2_old /xchip/tcga_gdac_ext_old /xchip/gcc_data_old /cga/brown_old
#for d in /fh/subscription-Bass_Lab /fh/subscription-Getz-PCAWG /fh/byos-nhgri-tcga /fh/subscription-Meyerson_Lab /fh/subscription-wu_lab
for d in /xchip/cga_home /xchip/tcga /xchip/cga /xchip/gdac_data /xchip/cptac_pgdac_data /xchip/tcga_data /xchip/pcawg_data

do
	sudo ./catalog_disk_usage.py -o /sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans13_new -r $d &
done


# sudo ./catalog_disk_usage.py -o /sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans10 -r    &