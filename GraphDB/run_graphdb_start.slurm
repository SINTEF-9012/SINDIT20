#!/bin/bash
#SBATCH --output /home/anl/SINDIT20/monorepo/projects/sindit/GraphDB/start-graphdb-%j.out
#SBATCH --job-name run-graphdb
#SBATCH --partition sintef
#SBATCH --ntasks 1
#SBATCH --mem=10GB
#SBATCH --cpus-per-task=2
#SBATCH --time 01-00:00:00

time=$(date)
echo "***** Start on $time *****"

cd /home/anl/SINDIT20/monorepo/projects/sindit/GraphDB
export DATE=`date +%F_%H%M`


srun bash graphdb_start.sh

time=$(date)
echo "***** End on $time *****"
