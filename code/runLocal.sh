: '
	System arguments main takes:
	----------------------------
	[1] - github version string for this repo
	[2] - readme string that will be included in the output
	[3] - system size
	[4] - temperature 10**-2 to 10**1 on a log-scale in 20 steps logspace(-2,1,20)
	[5] - max time
	[6] - time step
	[7] - coupling J
	[8] - coupling K
	[9] - dpsi
	[10] - sample number
'
# run profiler
python main.py $(git describe --always) 'local test of new code' 8 1 3000.0 0.1 1.0 0.1 0.01 1