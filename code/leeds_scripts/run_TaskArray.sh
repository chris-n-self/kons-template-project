#!/bin/bash

# Set current working directory
#$ -cwd

# Use current environment variables/ modules
#$ -V

# Set runtime
#$ -l h_rt=0:05:00

# Set memory
#$-l h_vmem=2000M

# Request run on 1 cores
#$ -pe smp 1

# Email at the beginning and end of the job
#$ -m be

# run a task array
#$ -t 1-_NUM_TASKS_
#$ -tc 100

# read the line from the inputs file for this job
task_spec=$(sed "${SGE_TASK_ID}q;d" inputs)

#Run with the task specification taken from the inputs file
python ./main.py _VERSION_STRING_ '_README_STRING_' $task_spec
