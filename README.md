# COMSUITE

A computational materials physics code for simulating strongly correlated
materials using Dynamic Mean Field Theory (DMFT) and its extension.

The repository contains a collection of relevant pieces including the source
code, examples, as well as a number of tools. 

The repository contains the following directories:

- bin -- executable binaries and scripts
- ComCTQMC -- ctqmc solver
- ComCoulomb -- bosonic Weiss Field within constrained random phase approximation
- ComDC -- double counted self-energy within local GW
- ComLowH -- to construct low-energy Hamiltonian and to calculate Delta
- ComWann -- Wannier function constructions
- ComRISB -- gutzwiller solver and interface to ComWann and FlapwMBPT
- tutorials -- tutorials
- gw -- FlapwMBPT(https://www.bnl.gov/cmpmsd/flapwmbpt/)
- wannier90-2.1.0 - the most recent version of Wannier90.

To install this package, modify arch.mk and "make"
# comsuite