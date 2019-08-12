# file-stats
Some tools for attributing filesystem usage


summ.txt files:
user    username   -- login name, _ALL_, zz.fileext1, zz.fileext1.fileext2, zz.fileext1.fileext2.fileext3 -- category that the rest of the line is aggregated over. file is sorted by "user".  Note .gz and .tar.gz files will sort adjacently, as they are represented as zz.gz and zz.gz.tar. 
fileCnt fileSize        TBfileSize      Last access     Last modified   -- aggregate stats for count, size, and dates within the category
Cnt<1M  Cnt<1G  Cnt<10G Cnt<100G   Cnt<1T   Cnt>1T  -- how many files are in each size bin. bins are disjoint, not cumulative
TB<1M   TB<1G   TB<10G  TB<100G TB<1T   TB>1T   -- total size (in TB) taken up by files of a certain size
Cntcsv  Cntbam  Cntgz   Cnttar  TBcsv   TBbam   TBgz    TBtar    -- counts and sizes of certain common extensions
Cnta<1w     Cnta<1m Cnta<1q Cnta<1y Cnta<2y Cnta>2y  -- how many files were accessed this much before the scan date.  bins are disjoint, not cumulative
TBa<1w  TBa<1m  TBa<1q  TBa<1y  TBa<2y  TBa>2y   -- size (in TB) of the files accessed this much before the scan date
Size<1M Size<1G Size<10G        Size<100G   Size<1T Size>1T -- total size (in bytes) of files of a certain size 
Sizecsv Sizebam Sizegz  Sizetar  -- total size (in bytes) of files of certain common extensions
Sizea<1w        Sizea<1m        Sizea<1q        Sizea<1y        Sizea<2y   Sizea>2y -- total size (in bytes) of files accessed this much before the scan date

annot.dirs.txt files:
dir     - directory path
size    files   last_access     last_modified -- stats aggregated over the directory and all of its children.  Size is in bytes.   File is sorted by size.
fract   - fraction of disk that this dir and all of its children consume.  eg if 50%, fract will be 0.5000
fractcat - fraction category, = fract rounded up to the next highest discrete level is 80, 90, 95, 99, 99.9, 100.  eg if you discard all directories labeled 80, you will clear at least 80% of your space.  You will want to focus on the few labeled 80 or 90 and ignore the many labeled 99.9  or 100.

annot.files.txt files:
filepath     - full path to the file.  Unruly characters (eg tab, carriage return, newline, quotes, foreign alphabets) are backslash escaped. Space and comma survive.
size    last_access     last_modified   username        groupname       -- metadata about the file.  File is sorted by size.
group_readable  all_readable    '1' or '0' to indicate whether others could access the file
symlink -- always '0'
nlink       inode   dupe -- fields to help avoid overcounting hard links. When multiple files are hard linked to the same inode (ie nlink>1), then all but one of the dupe fields will be 1 within the same scan.
filepath_escaped  -- 1 if filename contains backslash escapes, otherwise 0      
fract   -- fraction of the size of the total disk scan that this file takes up.  Eg a file consuming 1% of the space will have fract=0.0100
cumfract      --cumulative fraction of disk consumed by this file and all the ones bigger than it. 
cumfractcat    -- cumulative fraction category, = cumfract rounded up to the next highest discrete level is 80, 90, 95, 99, 99.9, 100.  eg if you discard all files labeled 80, you will clear at least 80% of your space.  You will want to focus on the few labeled 80 or 90 and ignore the many labeled 99.9  or 100.
ext     ext2    ext3 -- file extensions, double extensions, etc. foo.tar.gz will have: ext=.gz ext2=.gz.tar ext3=NA
