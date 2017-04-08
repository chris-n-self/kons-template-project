#! /bin/bash
#
#  Created by Chris Self on 22/02/2016.
#  Copyright (c) 2015 Chris Self. All rights reserved.
#
#  This script takes as an argument a comment that will be recorded in the run record and used to log what
#  the purpose of the run was.
#
script_name_=$0
script_name_=${script_name_#'./'}
script_name_=${script_name_%'.sh'}
version_string_=$(git describe --always)
comment_=$1

echo $script_name_
echo "-----------------------"
echo $comment_

# create file to store run information
run_record_=$(date +"%Y-%m-%d_%H%M")'_'"$script_name_"

# make directory in the runs directory (symlinked into /nobackup/)
mkdir "$HOME/runs/"$run_record_
curr_dir_="$HOME/runs/"$run_record_

# get the path of code directory
code_dir_="$PWD"

# copy the code into a run folder
cp -r "$code_dir_/code/." $curr_dir_"/"
# move into the run folder
cd $curr_dir_

# get the right run script depending on where the cluster is
if [ $USER == "pycse" ]; then
    cp leeds_scripts/run_TaskArray.sh .
else
    echo "ERROR could not identify which cluster script is running on"
    exit 1
fi

# set the fields and input values
####################################################
fields=( 'L' 'max_t' 'dt' 'T' 'J' 'K' 'dpsi' 'samples' )
L=( 7 )
max_t=('3000.0')
dt=('0.1')
T=($(seq 1 10))
J=('1.0')
K=('0.1')
dpsi=($(seq 1 10))
samples=($(seq 1 20))
####################################################

# get the number of required tasks using the sizes of the arrays
num_tasks=1
for var in ${fields[@]}; do
    num_parts_of_var=$(eval echo \${#${var}[@]})
    num_tasks=$(( num_tasks * num_parts_of_var ))
done
echo "job will be broken into "$num_tasks" tasks"

# set the comment string in the qsub file to the argument passed to this script
sed -i 's/_VERSION_STRING_/'"$version_string_"'/' "run_TaskArray.sh"
sed -i 's/_README_STRING_/'"$comment_"'/' "run_TaskArray.sh"
# set number of jobs
sed -i 's/_NUM_TASKS_/'$num_tasks'/' "run_TaskArray.sh"

# generate the input file which will contain all the task specifications
# pack-up fields
for L_val in ${L[@]}; do
    for max_t_val in ${max_t[@]}; do
        for dt_val in ${dt[@]}; do
            for T_val in ${T[@]}; do
                for J_val in ${J[@]}; do
                    for K_val in ${K[@]}; do
                        for dpsi_val in ${dpsi[@]}; do
                            for samples_val in ${samples[@]}; do
                                echo $L_val $T_val $max_t_val $dt_val $J_val $K_val $dpsi_val $samples_val >> inputs
                            done
                        done
                    done
                done
            done
        done
    done
done

# submit job and print job id
job_name_="$script_name_"'-'$(date +"%H%M_%d-%m-%Y")
rename run_TaskArray $job_name_ run_TaskArray.sh
job_id_=$(qsub $job_name_.sh)
echo $job_id_

cd $HOME
