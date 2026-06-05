# -*- coding: utf-8 -*-
"""
Copyright 2026. Triad National Security, LLC. All rights reserved. FCI reference number (O#): O4928.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National 
Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of 
Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad 
National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. 
The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, 
irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute 
copies to the public, perform publicly and display publicly, and to permit others to do so.

@author: Aaron Pital (Los Alamos National Lab)
Created:  2026-06-05
Description: Library for handling, analyzing, and reporting regions of data within datastreams. For images, this is a literal 2D region.
    For spectra or other psudo-2D data, this is a local subset of data. MESA scale-dependencies define borders and border properties.

Notes on MESA assumptions:
- MESA treats all data scale-dependent and is reduced in efficacy as the data becomes lower resolution.
    - i.e. a 10x10 pixel region in a 1000x1000 image is much easier to analyze than a 10x10 pixel region in a 20x20 image.
        - there will be less statistical power in the smaller image
- 

"""
