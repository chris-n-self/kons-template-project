#!/bin/env python
#
# 31/01/16
# Chris Self
"""
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
"""
import os
import sys
import time
import json
import numpy as np
# import Kitaev Honeycomb package
import kithcmb
from kithcmb import ThermalGradient as gradvs
from kithcmb import VortexSectorThermalFermions as nongradvs
# import jsci, CT's enhanced json stream write package
import jsci
from jsci import WriteStream as jsciwrite
from jsci import Coding as jscicoding

if __name__ == '__main__':
    print(sys.argv[0])
    print '---------'
    begin_time = time.time()

    # set output filename
    output_name = 'response-current_NV_L'+sys.argv[3]+'_T'+sys.argv[4]+'_tmax'+sys.argv[5]+'_dt'+sys.argv[6]+'_J'+sys.argv[7]+'_K'+sys.argv[8]+'_dpsi'+sys.argv[9]+'_sample'+sys.argv[10]

    # other system arguments are the code version and the readme string
    version_string = sys.argv[1]
    readme_string = sys.argv[2]

    # set the lattice-factor data we want to load
    L = int(sys.argv[3])
    
    # set the system parameters
    J = float(sys.argv[7])
    K = float(sys.argv[8])

    # set value beta from the system arguments
    #T = np.sqrt( 0.1/10 * float(sys.argv[4]) ) # low-T
    #T = 5./10 * float(sys.argv[4]) # high-T
    T = 10**(-2 + 2./9*(float(sys.argv[4])-1)) # logspace T
    print 'set T : ',T

    # set of times
    times = np.arange(0.,float(sys.argv[5]),float(sys.argv[6]))

    # initialise system
    print('initialising...')
    dpsi = 10**(-2 + 2./9*(float(sys.argv[9])-1)) # logspace dpsi
    non_grad_sys = nongradvs.VortexSectorThermalFermions(L,J,K)
    non_grad_sys.set_sign_disorder_random_vortex_configuration()
    grad_sys = gradvs.ThermalGradient(L,J,K,d_psi=dpsi,kh_to_match=non_grad_sys)

    # compute the coeffs of the eigenvectors of the system with no 
    # thermal gradient in terms of eigenvectors of the system with
    # a thermal gradient
    print 'computing overlaps'
    non_grad_eigvecs = non_grad_sys._get_eigenvectors()
    grad_eigvecs = grad_sys._get_eigenvectors()
    overlaps = np.zeros((2*L**2,2*L**2),dtype='complex128')
    for m in np.arange(2*L**2):
        for n in np.arange(2*L**2):
            overlaps[n,m] = np.sum( np.conj(grad_eigvecs[:,m]) * non_grad_eigvecs[:,n] )

    # compute the density matrix of the non-gradient state in basis of 
    # the thermal gradient eigenstates
    print 'changing basis of density matrix'
    ferm_occs = non_grad_sys.get_fermionic_expectation_values(1./T)
    combined_fermionic_expectation_values = np.empty( 2 * L**2 )
    for m in range(L**2):
        combined_fermionic_expectation_values[m] = np.exp( ferm_occs[2][m] )
        combined_fermionic_expectation_values[2 * L**2 - 1 - m] = np.exp( ferm_occs[1][m] )
    combined_fermionic_expectation_values = np.diag( combined_fermionic_expectation_values )
    dens_mat = np.dot( np.matrix(overlaps).getH(),combined_fermionic_expectation_values )
    dens_mat = np.dot( dens_mat,overlaps )

    # compute the currents with the perturbed A-matrix
    with open( output_name+'.json', 'w' ) as file:
        out = jsciwrite.FileWriteStream(file, indent=2)
        with out.wrap_object():

            # output task details
            out.write_pair('code_versions', { 'main':version_string, 'kithcmb':kithcmb.get_version_string(), 'jsci':jsci.get_version_string() } )
            out.write_pair('readme', readme_string)
            task_spec = non_grad_sys.get_standard_spec()
            task_spec.update({'tmax':sys.argv[5],\
                'dt':sys.argv[6],\
                'sample':sys.argv[10]})
            out.write_pair('specification', task_spec)

            # output vortex profiles
            out.write_pair('non_grad_vort_profile', non_grad_sys.vortices, jscicoding.NumericEncoder)
            out.write_pair('grad_vort_profile', grad_sys.vortices, jscicoding.NumericEncoder)
            out.write_pair('non_grad_vort', non_grad_sys.get_quantity('vortices'), jscicoding.NumericEncoder)
            out.write_pair('grad_vort', grad_sys.get_quantity('vortices'), jscicoding.NumericEncoder)
            out.write_pair('non_grad_energy', non_grad_sys.get_quantity('energy',1./T), jscicoding.NumericEncoder)
            out.write_pair('grad_energy', grad_sys.get_quantity('energy',1./T), jscicoding.NumericEncoder)

            out.write_key('time_series')
            with out.wrap_array():
                # evolve the density matrix in time
                for t in times:
                    start_time = time.time()
                    U = np.diag( np.exp(-1j * grad_sys.spectrum * t) )
                    dens_mat_at_t = np.dot( U, dens_mat )
                    dens_mat_at_t = np.dot( dens_mat_at_t, np.matrix(U).getH() )

                    # multiply the fermionic expectation matrix with the eigenvectors to rotate to the
                    # Majorana basis
                    correl_matrix = np.dot( np.matrix(grad_eigvecs), np.matrix(dens_mat_at_t) )
                    correl_matrix = np.dot( correl_matrix, np.matrix(grad_eigvecs).getH() )

                    # there can be an arbitrary & non-physical real component of correl_matrix, we throw that away here
                    # (the real diagonal does have some meaning so we keep it)
                    diag_correl = np.diag(correl_matrix)
                    correl_matrix = 1j * np.imag(correl_matrix) + np.diag(diag_correl)

                    # cache the correlation matrix
                    # the factor of two corrects for the \hat{a} fermions being prop to 1/2 (sum of c's) rather than 1/sqrt(2)
                    # this is equivalent to the statement that <c_i c_j> = 2 P_ij
                    correl_matrix = 2. * np.array(correl_matrix)

                    # get the currents matrix 
                    currents = grad_sys._compute_thermal_current_matrix(correl_matrix)

                    # get the net currents & output
                    with out.wrap_object():
                        # 'x'
                        net_current = np.real(grad_sys.get_total_current_in_x(currents))
                        out.write_pair('x', net_current, jscicoding.NumericEncoder)
                        # 'z'
                        net_current = np.real(grad_sys.get_total_current_in_y(currents))
                        out.write_pair('z', net_current, jscicoding.NumericEncoder)
                    
                    print 't : ',t,' took ',str(time.time()-start_time),' seconds'

            run_time = time.time() - begin_time
            out.write_pair( 'run_time', run_time )
