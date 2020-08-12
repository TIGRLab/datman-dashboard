#!/bin/bash -l
#
#SBATCH --job-name=download_session
#SBATCH --ntasks=1
#SBATCH --cores=1
#SBATCH --time=01:00:00

module load lab-code
module load minc-toolkit/1.0.01

study=$1
subject=$2

dm_xnat_extract.py ${study} ${subject}
