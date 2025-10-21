# -*- coding: utf-8 -*-
"""
© 2025. Triad National Security, LLC. All rights reserved.
This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National 
Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of 
Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad 
National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. 
The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, 
irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute 
copies to the public, perform publicly and display publicly, and to permit others to do so.

Created:  2024-04-03
Modified: 2025-07-19

@author: Aaron Pital (Los Alamos National Lab)

Description: Set of classes for handling SEM, laser profilometry

"""

from SEAM.Core.MetaData import Meta
from SEAM.Dependencies import vk4extract

import cv2
import datetime
import json
import math
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from operator import itemgetter
import os
import pandas as pd
import PIL
from PIL import Image
from PIL.TiffTags import TAGS
  #WARNING: risks decompression bomb susceptibility; only use if you're processing images you trust
Image.MAX_IMAGE_PIXELS = None
from scipy.interpolate import griddata
# import seaborn as sns
#from skimage.feature import blob_dog, blob_log, blob_doh
from skimage.measure import label, regionprops_table
from sklearn.linear_model import LinearRegression
from tqdm.auto import tqdm
from tkinter import Tk, filedialog

    
##################################################################################################
###    Keyence     ###############################################################################
##################################################################################################


class Keyence:

    ''' v1.0.0   created:2024-04-19   modified:2024-08-25
    
    Wrapper class for Keyence file handling and stitching. 
 
    '''
    
    global GOA, GHA
    
    version = '1.0.0'
    version_mod_date = '2024-08-25'
    
    x_exceptions = ['10X', '20X', '50X', '100X', 'XChecker', 'XCheckerHoles', 'TinBalls10X', 'TinBalls20X', 'SPY']
    #TODO: fix this very dumb way of guessing if a coupon image's index is good or not
    index_dict = {
        'images':(15,11),
        'good': [(2,5), (2,6),(2,7),
                 (3,4), (3,5), (3,6), (3,7), (3,8),
                 (4,3), (4,4), (4,5), (4,6), (4,7), (4,8), (4,9),
                 (5,3), (5,4), (5,5), (5,6), (5,7), (5,8), (5,9),
                 (6,2), (6,3), (6,4), (6,5), (6,6), (6,7), (6,8), (6,9), (6,10),
                 (7,2), (7,3), (7,4), (7,5), (7,6), (7,7), (7,8), (7,9), (7,10),
                 (8,2), (8,3), (8,4), (8,5), (8,6), (8,7), (8,8), (8,9), (8,10),
                 (9,2), (9,3), (9,4), (9,5), (9,6), (9,7), (9,8), (9,9), (9,10),
                 (10,2), (10,3), (10,4), (10,5), (10,6), (10,7), (10,8), (10,9), (10,10),
                 (11,3), (11,4), (11,5), (11,6), (11,7), (11,8), (11,9),
                 (12,3), (12,4), (12,5), (12,6), (12,7), (12,8), (12,9),
                 (13,4), (13,5), (13,6), (13,7), (13,8),
                 (14,5), (14,6), (14,7)],
        'marginal_coupon': [(1,4), (1,5), (1,6), (1,7), (1,8), (2,3), (2,9), (3,2), (3,10), (4,2), (4,10), \
                            (5,1), (6,1), (7,1), (8,1), (9,1), (10,1), (11,1),\
                            (5,11), (6,11), (7,11), (8,11), (9,11), (10,11), (11,11), (12,2), (12,10),(13,2), \
                            (13,10), (14,3), (14,9), (15,4), (15,5), (15,6), (15,7), (15,8)],
        'edge': [],
        'marginal_gap': [(1,3), (1,9), (2,2), (2,10), (3,1), (3,11), (4,1), (4,11), (12,1), (12,11), (13,1), \
                         (13,11), (14,2), (14,10), (15,3), (15,9)],
        'bad': [(1,1), (1,2), (2,1), (1,10), (1,11), (2,11), (14,1), (14,11), (15,1), (15,2), (15,10), (15,11)]
        }
    
    
    ##################################################################################################
    ###    Static Methods     ########################################################################
    ##################################################################################################
    
    
    @staticmethod
    def vk4_read(filename, input_dict={}):
        ''' v0.1.0   created:2024-08-05  modified:2024-08-05
        Modified from earlier functions 
        '''
        
        #Check if this file has been processed previously
        #   (look to see if height and optical already exist)
        laser_filename = filename.replace('.vk4','')+'_Laser.png'
        if os.path.isfile(laser_filename):
            laser_flag = False
        else:
            laser_flag = True
        
        optical_filename = filename.replace('.vk4','')+'_Optical.png'
        if os.path.isfile(optical_filename):
            optical_flag = False
        else:
            optical_flag = True
        
        
        #Extract the RGB and height data and save individual files
        with open(filename, 'rb') as in_file:
            offsets = vk4extract.extract_offsets(in_file)
            meas_data_2 = vk4extract.extract_measurement_conditions(offsets, in_file)
            rgb_dict = vk4extract.extract_color_data(offsets, 'peak', in_file)
            height_dict = vk4extract.extract_img_data(offsets, 'height', in_file)
            
        #Pull image height and width from 'height_dict'; should be the same for both images
        img_height = height_dict['height']
        img_width = height_dict['width']
        height_data = height_dict['data']
        rgb_data = rgb_dict['data']
        
        height_matrix = np.reshape(height_data, (img_height, img_width))
        rgb_matrix = np.reshape(rgb_data, (img_height, img_width, 3))
            
        #Initialize an 'output_dict'
        output_dict ={
            'file_metadata': meas_data_2, 
            'image_height': img_height, 
            'image_width': img_width, 
            'height_array': height_matrix,
            'optical_array': rgb_matrix
            }
        
        
        #Laser data is always pulled from .vk4 because otherwise why are you reading it
        if laser_flag:
            height_image = Image.fromarray(height_matrix)
            plt.imsave(laser_filename, height_image, cmap = 'inferno', dpi=600)
        
        #optical data only pulled an processed if 
        if optical_flag:
            rgb_image = PIL.Image.fromarray(rgb_matrix)
            rgb_image = rgb_image.convert("RGB")
            plt.imsave(optical_filename, rgb_image)
                
        return output_dict
    
    
    @staticmethod
    def vk4_group_summary(filenames, input_dict={}):
        ''' v1.0.0   created:2024-04-19  modified:2024-08-06
        Modified from version 0.1; previously 'vk4_laser_prestitch'.
        Includes input/output parsing and streamlines past versions.
        '''
        
        #TODO: no modifiers were used previously, but should consider using them
        if len(input_dict) == 0:
            #Set default keyword argument values
            hist_bins = 100   #Number of histogram bins to consider in height histograms; no real difference >~50
        else:
            #TODO: eventually this should try and parse the 'input_dict' and look for keyword arguments
            hist_bins = 100   #Number of histogram bins to consider in height histograms; no real difference >~50
        
        #Assign class variables to local scope (just easier this way; should change eventually)
        x_exceptions = Keyence.x_exceptions
        index_dict = Keyence.index_dict
        
        #Initialize dict and arrays
        output_dict = {}
        good_surface_mean_heights=[]
        good_fwhms =[]
        
        
        # Initialize global variables
        x_min = 10000
        x_max = 0
        y_min = 10000
        y_max = 0
        adj_dict = {}        #Save the adjacent-image filenames for each side of each filename while we're here
        qual_dict = {}
        fwhm_dict = {}
        surface_height_dict = {}
        
        
        # Run through, get max dimensions of 'X' and 'Y' values, populate 
        for idx, filename in enumerate(filenames):
            # Get the X/Y dimensions of the final assembly
            split_list = os.path.basename(filename).split('_')
            for item in split_list:
                item = item.replace('.vk4', '')
                if ('Y' in item) and (item not in x_exceptions):
                    this_y = int(item.replace('Y',''))  #Get the 'Y' index and turn it into a real number
                    if this_y > y_max:
                        y_max = this_y
                    if this_y < y_min:
                        y_min = this_y
                if ('X' in item) and (item not in x_exceptions):
                    #print(item)
                    this_x = int(item.replace('X',''))  #Get the 'X' index and turn it into a real number
                    if this_x > x_max:
                        x_max = this_x
                    if this_x < x_min:
                        x_min = this_x
            # Write maxes to 'sample_dict'
            output_dict.update({'y_min' : y_min})
            output_dict.update({'x_min' : x_min})
            output_dict.update({'y_max' : y_max})
            output_dict.update({'x_max' : x_max})
            output_dict.update({'indices': (this_y, this_x)})
        
         
        #TODO: fix this garbage; add better support for good/bad flagging
        # Do the exact same thing, but now compare file X/Y indices to get edge filenames
        for idx, filename in enumerate(filenames):
            # Get the X/Y dimensions of the final assembly
            split_list = os.path.basename(filename).split('_')
            for item in split_list:
                item = item.replace('.vk4', '')
                if ('Y' in item) and (item not in x_exceptions):
                    this_y = int(item.replace('Y',''))  #Get the 'Y' index and turn it into a real number
    
                if ('X' in item) and (item not in x_exceptions):
                    #print(item)
                    this_x = int(item.replace('X',''))  #Get the 'X' index and turn it into a real number
    
            # Generate a set of adjacency indices
            adj_dict.update({filename:{'Top_edge Filename': '', \
                                       'Bottom_edge Filename': '', \
                                       'Left_edge Filename': '', \
                                       'Right_edge Filename': ''
                                       }})
            if (this_y, this_x) in index_dict['good']:
                qual_dict.update({filename: 'good'})
            elif (this_y, this_x) in index_dict['marginal_coupon']:
                qual_dict.update({filename: 'marginal_coupon'})
            elif (this_y, this_x) in index_dict['edge']:
                qual_dict.update({filename: 'edge'})
            elif (this_y, this_x) in index_dict['marginal_gap']:
                qual_dict.update({filename: 'marginal_gap'})
            elif (this_y, this_x) in index_dict['bad']:
                qual_dict.update({filename: 'bad'})
            else:
                qual_dict.update({filename: 'UNK'})
    
            # Get filenames for each edge image in the list
            #   Get top
            if (this_y != 1):
                top_y = this_y-1
                y_name = 'Y'+str(this_y)
                adj_name = "Y"+str(top_y)
                top_filename = filename.replace(y_name, adj_name)
                if os.path.isfile(top_filename):
                    adj_dict[filename]['Top_edge Filename'] = top_filename
                else:
                    adj_dict[filename]['Top_edge Filename'] = ''
            else:
                adj_dict[filename]['Top_edge Filename'] = ''
    
            #   Get bottom
            if (this_y != y_max):
    
                bot_y = this_y+1
                y_name = 'Y'+str(this_y)
                adj_name = "Y"+str(bot_y)
                bottom_filename = filename.replace(y_name, adj_name)
                if os.path.isfile(bottom_filename):
                    adj_dict[filename]['Bottom_edge Filename'] = bottom_filename
                else:
                    adj_dict[filename]['Bottom_edge Filename'] = ''
    
            else:
                adj_dict[filename]['Bottom_edge Filename'] = ''
    
            #   Get left
            if (this_x != 1):
                left_x = this_x-1
                x_name = 'X'+str(this_x)
                adj_name = "X"+str(left_x)
                left_filename = filename.replace(x_name, adj_name)
                if os.path.isfile(left_filename):
                    adj_dict[filename]['Left_edge Filename'] = left_filename
                else:
                    adj_dict[filename]['Left_edge Filename'] = ''
            else:
                adj_dict[filename]['Left_edge Filename'] = ''
    
            #   Get right
            if (this_x != x_max):
                right_x = this_x+1
                x_name = 'X'+str(this_x)
                adj_name = "X"+str(right_x)
                right_filename = filename.replace(x_name, adj_name)
                if os.path.isfile(right_filename):
                    adj_dict[filename]['Right_edge Filename'] = right_filename
                else:
                    adj_dict[filename]['Right_edge Filename'] = ''
            else:
                adj_dict[filename]['Right_edge Filename'] = ''
    
            # Open each file and add lorentzian data if image is good
            with open(filename, 'rb') as in_file:
                offsets = vk4extract.extract_offsets(in_file)
                vk4_data = vk4extract.extract_img_data(offsets, 'height', in_file)
            height_data = vk4_data['data']
    
            this_counts, this_bins = np.histogram(height_data, bins=hist_bins)
    
            # Max height and width-at-half-max approach
            this_max = this_counts.max()
            this_max_idx = np.where(this_counts == this_max)[0][0]
            this_max_x = this_bins[this_max_idx+1]
            half_max = this_max/2
    
            diffs = np.abs(this_counts-half_max)
            lower_half_idx = diffs[0:this_max_idx].argmin()+1
            upper_half_idx = diffs[this_max_idx::].argmin() + diffs[0:this_max_idx].shape[0]+1
            full_width_half_max = this_bins[upper_half_idx]-this_bins[lower_half_idx]
    
            surface_height_dict.update({filename: this_max_x})
            fwhm_dict.update({filename: full_width_half_max})
            
            if qual_dict[filename]== 'good':
               good_fwhms.append(full_width_half_max)
               good_surface_mean_heights.append(this_max_x)
    
        #TODO: fix this garbage; there needs to be a better way of handling averages and surface coupon height
        output_dict['adjacenct_filenames'] = adj_dict
        try:
            output_dict['average_good_fwhms'] = sum(good_fwhms)/len(good_fwhms)
        except:
            output_dict['average_good_fwhms']=0
        try:
            output_dict['average_good_heights'] = sum(good_surface_mean_heights)/len(good_surface_mean_heights)
        except:
            output_dict['average_good_heights'] = 0
        output_dict['height_quality']= qual_dict
        output_dict['fwhm']= fwhm_dict
        output_dict['surface_height_mean']= surface_height_dict
    
        return output_dict
    
    
    
    @staticmethod
    def vk4_tilt_correct(filename, input_dict = {}):
        
        ''' v2.0   created:2024-04-19   modified:2024-08-06
        
        Handles two types of images (2D matrices generally) to tilt-correct:
            'height'- some form of height data from profilometry, etc.
            'intensity'- some form of single-array continous intensity values (i.e. grayscale)
        
        INPUT:    filenames' - list of filenames
                 'interpolation' - grid interpolation between avg points; 'linear'  'cubic'  'nearest'
        ACTION:  import each image, make an array, and calculate skewing of average 'zero' level for a range of points
        OUTPUT:  dictionary or updated dictionary with filenames: {'tilt_summary'} added
    
        TODO:   -add support for VK6 import
                -add support for optical 'tilt' corrections (albedo, etc.)
                -tilt correction is currently not great
                -interpolation points on the grid show up in final image because they're being set strangely
        '''
        
        #Initialize default values
        arg_dict = {
            'window_kernel_size' : 51,
            'window_overlap' : 20,
            'average_global_height' : 0,
            'average_fwhm' : 0,
            'tilt_interpolation' :'linear',
            'show_meshgrid_histograms' : False,
            'show_coupon_correction' : False,   #Used for troubleshooting initially; plots histogram of average global height shifted img
            }
        output_dict = {
            'input_arguments':arg_dict
            }
        
        #TODO: if the input array is empty, some checks should be run
        if len(input_dict) == 0:
            pass   #pass for now until checks are added; probably check
        else:
            try:
                potential_arguments = input_dict['function_arguments']
                #TODO: get potential arguments from the list, filter by 
                for key, value in potential_arguments.items():
                    try:
                        arg_dict[key] = value
                    except:
                        pass   #if key isn't in 'arg_dict', ignore it
            except:
                pass   #If there's an error it should be flagged later
                    
        # Flag if filetype is .VK4 or (eventually) .VK6
        #  TODO: add support in function for vk6 parsing
        if '.vk' in filename:
            #Flag Keyence filetype for read handling
            #TODO: 'vk_flag' should trigger SEAM actions for 'meta_dict' logging regardless of which version
            vk_flag = True
            #Flag vk4 
            if '.vk4' in filename:
                vk4_flag = True
            else: 
                vk4_flag = False
            #Flag vk4 
            if '.vk6' in filename:
                vk6_flag = True
            else: 
                vk6_flag = False
        else:
            vk_flag = False
                    
        # Open the image in binary, read-only mode and then in Python Image Library (PIL) as an 'Image' object
        if vk4_flag:
            image_dict = Keyence.vk4_read(filename)
            img = image_dict['height_array']   #mxn array of image heights
         #TODO: see if this is really needed; intention was to use an image file as height data, which makes sense but hasn't been used
        else:
            img = Image.open(filename)
            # Use PIL's tag library to read the TIF metadata
            tag_dict = {}
            for key in img.tag_v2:
                try:
                    tag_dict.update({TAGS[key] : img.tag[key]}) 
                except KeyError:
                    tag_dict.update({key : img.tag[key]})
        
        # Get summary stats and generate evaluation points for image
        height = img.shape[0]
        width = img.shape[1]
        
        offset = (arg_dict['window_kernel_size']-arg_dict['window_overlap'])//2
          #grid point generation
        xlin = np.linspace(offset, width-1-offset, width//(arg_dict['window_kernel_size']-offset))
        ylin = np.linspace(offset, height-1-offset, height//(arg_dict['window_kernel_size']-offset))
        mesh_x, mesh_y = np.meshgrid(xlin, ylin)
          #generate flat arrays
        flat_x = np.round(mesh_x).flatten().astype('int')
        flat_y = np.round(mesh_y).flatten().astype('int')
        
        # Get mu and sigma for entire image distribution
        cnts, bins = np.histogram(img.flatten(), bins = 50)
          #np.ndarray has to be converted to 'int' and 'float' lists to be saved as a JSON
        output_dict.update({'image_histogram_counts': [int(value) for value in cnts]})
        output_dict.update({'image_histogram_bins': [float(value) for value in bins]})
                                  
          #Calculate global max height and width-at-half-max guess
        this_max = cnts.max()
        this_max_idx = np.where(cnts == this_max)[0][0]
        this_max_x = bins[this_max_idx+1]
        image_max_x = this_max_x
        half_max = this_max/2
          
          #Find half-max boundaries
        diffs = np.abs(cnts-half_max)
        lower_half_idx = diffs[0:this_max_idx].argmin() + 1    #+1 to account for bin:cnt length diff
        upper_half_idx = diffs[this_max_idx::].argmin() + diffs[0:this_max_idx].shape[0] + 1   #+1 to account for bin:cnt length diff
        full_width_half_max = bins[upper_half_idx]-bins[lower_half_idx]
    
        # Adjust average to 'global' average
        img_avg_adjustment = image_max_x- arg_dict['average_global_height']  #average deviation to align this image with the global
        img = img[::,::] - (np.ones((height, width)) * img_avg_adjustment)   #make the adjustment
    
        if arg_dict['show_coupon_correction']:
            diff_cnts, diff_bins = np.histogram(img, bins = 50)
            plt.scatter(bins[1::], cnts)
            plt.scatter(diff_bins[1::], diff_cnts)
            plt.title("")
            plt.legend(['Original img','adj img'])
            plt.show()
        
            print()
            print(f"{os.path.basename(filename)}")
            print(f"   Image most common height: {image_max_x:.2e}")
            print(f"   Global tilt offset: {img_avg_adjustment:.2e}")
        
        # Keeping these lists in case they're used later; not used currently
        window_max_diffs = []
        window_maxs =  []
        window_avgs = []
        mesh_diffs = []
        for x_list, y_list in zip(mesh_x, mesh_y):
            these_diffs = []
            for idx, (x, y) in enumerate(zip(x_list, y_list)):
                x = int(x)
                y = int(y)
                this_inset = img[y-offset:y+offset, x-offset:x+offset]
                this_avg = np.average(this_inset)
                window_avgs.append(this_avg)
            
                cnts, bins = np.histogram(this_inset.flatten(), bins = 50)
                this_max = cnts.max()
                this_max_idx = np.where(cnts == this_max)[0][0]
                this_max_x = bins[this_max_idx+1]
                window_maxs.append(this_max_x)
    
                #If an average height is supplied for global sitching, use that; otherwise use the overall image average
                if arg_dict['average_global_height'] != 0:
                    this_diff = this_max_x- arg_dict['average_global_height']
                else:
                    this_diff = this_max_x-image_max_x
                
                #Constrain tilt correction by FWHM of pixel height histogram (equivalent to Guassian 2-sigma in CLT 'limit')
                #  If a FWHM is supplied for global stitching, use that; otherwise default to not clipping tilt
                if arg_dict['average_fwhm'] != 0:
                    # if abs(diff) >2 std. dev. of average height, clip to 2 std. dev. above/below surface
                    if abs(this_diff) > arg_dict['average_fwhm']*2:
                        if this_diff<0:
                            this_diff = -1*arg_dict['average_fwhm'] + arg_dict['average_global_height']
                        else:
                            this_diff = arg_dict['average_fwhm'] + arg_dict['average_global_height']
    
                    # otherwise just keep the 'this_diff' value
                #use this images FWHM if a global average isn't supplied
                else:
                    pass   # pass for now; not sure if I want function to do anything if a global FWHM and average aren't defined
    
                window_max_diffs.append(this_diff)
                these_diffs.append(this_diff) 
    
                
                if arg_dict['show_meshgrid_histograms']:
                    plt.scatter(bins[1::], cnts)
                    plt.plot([this_avg, this_avg],[min(cnts), max(cnts)], color='g')
                    plt.plot([this_max_x, this_max_x],[min(cnts), max(cnts)], color='magenta')
                    plt.show()
            mesh_diffs.append(these_diffs)
        mesh_array = np.array(mesh_diffs)  #make into numpy array for speeds
        flat_mesh = mesh_array.flatten()
        
        # Get averages for each x/y; used for plotting tilt, not used in calculation
        x_avgs = []
        for x_idx in range(len(xlin)):
            x_avgs.append(np.average(mesh_array[::,x_idx]))
        y_avgs = []
        for y_idx in range(len(ylin)):
            y_avgs.append(np.average(mesh_array[y_idx::]))
        
        # Make a new array the size of the input image, assign deviations from above, and interpolate remaining sparse regions
          #Make grid and populate with known data
        grid = np.ones((height, width)) * arg_dict['average_global_height']
        for x, y, data in zip(flat_x, flat_y, flat_mesh):
            grid[y,x] = data
          #Mask off non-zero values, make an mgrid, and interpolate
        points = grid.nonzero()
        values = grid[points]
          #Make new X/Y grid indices
        gridx, gridy = np.mgrid[:grid.shape[0], :grid.shape[1]]
          #populate known points into grid above and interpolate between them
        interp_height_correction = griddata(points, values, (gridx, gridy), \
                                            method= arg_dict['tilt_interpolation']) # 'linear'  'cubic'  'nearest'
        #if average_global_height != 0:
        #    interp_height_correction = interp_height_correction - img_avg_adjustment
    
        #Populate return dictionary with values from all that stuff above, including the 'correction' matrix
        output_dict.update({'coupon_corrected_image': img})
        output_dict.update({'image_tilt_correction_matrix': interp_height_correction})
        output_dict.update({'interpolation_type': arg_dict['tilt_interpolation']})
        output_dict.update({'x_points': flat_x})
        output_dict.update({'y_points': flat_y})
        output_dict.update({'x-y_tilt_corrections': mesh_array})
    
        return output_dict
    
    
    @staticmethod
    def vk4_stitch(filenames, input_dict = {}, update_metadict = True):
        ''' v0.5   created:2024-04-19   modified:2024-08-06
        
        Taken from previous versions; needs work unitl made into v1.0. 
        
        INPUT:   
        ACTION:  
        OUTPUT:
            
        TODO:
            - lo
        '''
        
        global GOA, GHA
        
        arg_dict = {
            'global_height_align' : True, 
            'tilt_constrain' : True,
            'report_height_stats' : False, 
            'optical_only' : False
            }
        x_exceptions = Keyence.x_exceptions
        output_dict = {}
        
        sample_dict = Keyence.vk4_group_summary(filenames)
        
        #TODO: if the input array is empty, some checks should be run
        if len(input_dict) == 0:
            pass   #pass for now until checks are added; probably check
        else:
            try:
                potential_arguments = input_dict['function_arguments']
                #TODO: get potential arguments from the list, filter by 
                for key, value in potential_arguments.items():
                    try:
                        arg_dict[key] = value
                    except:
                        pass   #if key isn't in 'arg_dict', ignore it
            except:
                pass   #If there's an error it should be flagged later
        
        # Pull values from 'sample_dict'
        name_guess = os.path.basename(filenames[0]).split('_Y')[0]
        coupon_fwhm = sample_dict['average_good_fwhms']
        coupon_surface_avg = sample_dict['average_good_heights']
        x_max = sample_dict['x_max']
        y_max = sample_dict['y_max']
        
        # Final image will be number of images * pixels - overlap between them 
        x_dim = 1024 * x_max -(128 * (x_max-1))
        y_dim = 768 * y_max -(128 * (y_max-1))
        print("Final assembly (y_dim, x_dim) will be ", y_dim, ', ', x_dim)
        
        #Initialize the height array to the avg surface height and optical array to all zeros
        if arg_dict['optical_only']:
            GOA = np.zeros((y_dim, x_dim,3))
            
            for filename in tqdm(filenames):
                #Create a filename
                folder_name = os.path.basename(os.path.dirname(filename))
                folder_path = os.path.dirname(os.path.dirname(filename))
                this_datetime = datetime.datetime.now()
                meta_key_name = folder_name+'_Assembly_'+str(y_dim)+ 'X'+str(x_dim) +'_'
                
                #Open the 
                img_dict = Keyence.vk4_read(filename)
                laser_img = img_dict['height_array']
                optical_img = img_dict['optical_array']
                
                if arg_dict['global_height_align']:
                    pass   #may add checks here eventually; for now, just take pass through with global height
                else:
                    coupon_surface_avg = 0   #if not aligning globally, pass default '0' value to tilt_dict; results in image-only tilt correct
                    
                if arg_dict['tilt_constrain']:
                    pass  #may add checks here eventually; for now, just take pass through with global FWHM for constraining tilt magnitude
                else:
                    coupon_fwhm = 0   #if not constraining tilts globally, pass default '0' value to tilt_dict; results in image-only tilt magnitude guesses
                    #TODO: unstable; need a better way to guess if tilt correction is actually a feature or not
            
                # Grab the 'X' and 'Y' index again
                split_list = os.path.basename(filename).split('_')
                for item in split_list:
                    item = item.replace('.vk4', '')
                    if ('Y' in item) and (item not in x_exceptions):
                        this_y = int(item.replace('Y',''))  #Get the 'Y' index and turn it into a real number
                    if ('X' in item) and (item not in x_exceptions):
                        this_x = int(item.replace('X',''))  #Get the 'X' index and turn it into a real number
            
                # Define start and stop indices
                x_start = (1023 * (this_x-1)) - (128 * (this_x-1))
                x_end = x_start + 1024
                y_start = (767 * (this_y-1)) - (128 * (this_y-1))
                y_end = y_start + 768
            
                # Place the pixels in the final assembly and increment that pixel count
                GOA[y_start:y_end, x_start:x_end, ::] = optical_img
                
                if update_metadict:
                    pic_dict = {
                        meta_key_name: {
                            'stitch_x0_idx': x_start,
                            'stitch_y0_idx': y_start
                            }
                        }
                    _,_ = Meta.meta_index_lookup(filename, update_dict=pic_dict)
            
            # Create a useful filename for the GFA and save it to the same folder the images were pulled from
            folder_name = os.path.basename(os.path.dirname(filename))
            folder_path = os.path.dirname(os.path.dirname(filename))
            this_datetime = datetime.datetime.now()
            file_name = folder_name+'_Assembly_'+str(y_dim)+ 'X'+str(x_dim) +'_'+str(this_datetime).split('.')[0].replace(":",'.')
            gha_filename = os.path.join(folder_path, file_name+".png")
            print("Saving file in location: ")
            print(gha_filename)
            print()
            
            # Save the array
            optical_array_name =  os.path.join(folder_path, "OpticalArray_"+file_name)
            with open(optical_array_name, 'wb') as name:
                np.save(name, GOA)
            
            # Optical stitch saving
            file_name = folder_name+'_OpticalAssembly_'+str(y_dim)+ 'X'+str(x_dim) +'_'+str(this_datetime).split('.')[0].replace(":",'.')
            goa_filename = os.path.join(folder_path, file_name+".png")
            goa_image = PIL.Image.fromarray(GOA.astype(np.uint8))
            goa_image.save(goa_filename, format = 'png')
            
            #gfa_image.save(gfa_filename, format= "PNG")
            plt.figure(figsize=(20,20))
            plt.imshow(GOA)
            plt.show()
            
            if update_metadict:
                pic_dict = {
                    'optical_numpy_array_filepath': optical_array_name,
                        }

                _,_ = Meta.meta_index_lookup(goa_filename, update_dict=pic_dict)
        
        #Stitch both laser and optical images
        else:
            GHA = np.ones((y_dim, x_dim)) * coupon_surface_avg
            GOA = np.zeros((y_dim, x_dim,3))
            
            for filename in tqdm(filenames):
                #Open the 
                img_dict = Keyence.vk4_read(filename)
                laser_img = img_dict['height_array']
                optical_img = img_dict['optical_array']
                
                #Create a filename
                folder_name = os.path.basename(os.path.dirname(filename))
                folder_path = os.path.dirname(os.path.dirname(filename))
                this_datetime = datetime.datetime.now()
                meta_key_name = folder_name+'_Assembly_'+str(y_dim)+ 'X'+str(x_dim) +'_'
                
                if arg_dict['global_height_align']:
                    pass   #may add checks here eventually; for now, just take pass through with global height
                else:
                    coupon_surface_avg = 0   #if not aligning globally, pass default '0' value to tilt_dict; results in image-only tilt correct
                    
                if arg_dict['tilt_constrain']:
                    pass  #may add checks here eventually; for now, just take pass through with global FWHM for constraining tilt magnitude
                else:
                    coupon_fwhm = 0   #if not constraining tilts globally, pass default '0' value to tilt_dict; results in image-only tilt magnitude guesses
                    #TODO: unstable; need a better way to guess if tilt correction is actually a feature or not
                
                # tilt_dict keys 'image_tilt_correction_matrix' 'interpolation_type'  'y_points'  'y_tilt_corrections'
                
                tilt_input_dict = {
                    'window_kernel_size' : 101, 
                    'window_overlap' : 20, 
                    'average_global_height' : coupon_surface_avg, 
                    'average_fwhm' : coupon_fwhm,
                    'interpolation' : 'linear',
                    'show_meshgrid_histograms' : False
                    }
                tilt_dict = Keyence.vk4_tilt_correct(filename, tilt_input_dict)
            
                # Grab the 'X' and 'Y' index again
                split_list = os.path.basename(filename).split('_')
                for item in split_list:
                    item = item.replace('.vk4', '')
                    if ('Y' in item) and (item not in x_exceptions):
                        this_y = int(item.replace('Y',''))  #Get the 'Y' index and turn it into a real number
                    if ('X' in item) and (item not in x_exceptions):
                        this_x = int(item.replace('X',''))  #Get the 'X' index and turn it into a real number
            
                # Define start and stop indices
                x_start = (1023 * (this_x-1)) - (128 * (this_x-1))
                x_end = x_start + 1024
                y_start = (767 * (this_y-1)) - (128 * (this_y-1))
                y_end = y_start + 768
            
                # Place the pixels in the final assembly and increment that pixel count
                if arg_dict['tilt_constrain']:
                    GHA[y_start:y_end, x_start:x_end] = tilt_dict['coupon_corrected_image'] + tilt_dict['image_tilt_correction_matrix']
                else:
                    GHA[y_start:y_end, x_start:x_end] = tilt_dict['coupon_corrected_image']
                GOA[y_start:y_end, x_start:x_end, ::] = optical_img
                
                if update_metadict:
                    pic_dict = {
                        meta_key_name: {
                            'stitch_x0_idx': x_start,
                            'stitch_y0_idx': y_start,
                            'tilt_dict': {
                                'input_arguments': tilt_dict['input_arguments'],
                                'image_histogram_counts': list(tilt_dict['image_histogram_counts']),
                                'image_histogram_bins': list(tilt_dict['image_histogram_bins'])
                                }
                            }
                        }
                    _,_ = Meta.meta_index_lookup(filename, update_dict=pic_dict)
            
                # Report stats
                if arg_dict['report_height_stats']:
                    corr_cnts, corr_bins = np.histogram(GHA[y_start:y_end, x_start:x_end], bins = 50)
                    laser_cnts, laser_bins = np.histogram(laser_img[::,::,0], bins = 50)
                
                    plt.plot([coupon_surface_avg, coupon_surface_avg], [min(corr_cnts), max(corr_cnts)], linewidth=5, color='green')
                    plt.scatter(laser_bins[1::], laser_cnts, s=200, alpha=0.7)
                    plt.scatter(corr_bins[1::], corr_cnts, s=200, alpha=0.7)
                    plt.title("'Raw' Laser Heights vs. corrected heights")
                    plt.legend(['Coupon avg.','Raw  heights', 'Corr heights'])
                    plt.show()
        
            # Create a useful filename for the GFA and save it to the same folder the images were pulled from
            folder_name = os.path.basename(os.path.dirname(filename))
            folder_path = os.path.dirname(os.path.dirname(filename))
            this_datetime = datetime.datetime.now()
            file_name = folder_name+'_Assembly_'+str(y_dim)+ 'X'+str(x_dim) +'_'+str(this_datetime).split('.')[0].replace(":",'.')
            gha_filename = os.path.join(folder_path, file_name+".png")
            print("Saving file in location: ")
            print(gha_filename)
            print()
            
            # Save the array
            GHA= np.nan_to_num(GHA, nan=coupon_surface_avg, \
                          posinf=coupon_surface_avg, neginf=coupon_surface_avg) #convert nan and any inf's to 0's
            height_array_name =  os.path.join(folder_path, "HeightArray_"+file_name+".npy")
            with open(height_array_name, 'wb') as name:
                np.save(name, GHA)
            optical_array_name =  os.path.join(folder_path, "OpticalArray_"+file_name+".npy")
            with open(optical_array_name, 'wb') as name:
                np.save(name, GOA)
            
            
            # Height visualization
            median_height = coupon_surface_avg*2
            up_offset = coupon_surface_avg*2
            down_offset = coupon_surface_avg
            offset = mcolors.TwoSlopeNorm(vmin=median_height-down_offset, \
                                          vcenter=median_height, vmax=median_height+up_offset)
            norm_GHA = offset(GHA)
            norm_GHA = np.nan_to_num(norm_GHA, nan=0.5, \
                          posinf=0.5, neginf=0.5)
            #GHA_norm = GHA/np.max(GHA)   # This is generally a bad idea, but useful for optical and similar images
            #gfa_image = PIL.Image.fromarray(np.uint16(cm.Spectral(GFA)*255))   # Previous standalone mapping from image to colormap
            gha_image = PIL.Image.fromarray(np.uint16(norm_GHA))
            
            # Optical stitch saving
            file_name = folder_name+'_OpticalAssembly_'+str(y_dim)+ 'X'+str(x_dim) +'_'+str(this_datetime).split('.')[0].replace(":",'.')
            goa_filename = os.path.join(folder_path, file_name+".png")
            goa_image = PIL.Image.fromarray(GOA.astype(np.uint8))
            goa_image.save(goa_filename, format = 'png')
            
            #Show and save the laser image
            plt.figure(figsize=(20,20))
            plt.imshow(offset(GHA), cmap= 'bwr')
            plt.imsave(gha_filename, norm_GHA, cmap='bwr')
            plt.show()
            
            #Show the optical image
            plt.figure(figsize=(20,20))
            plt.imshow(goa_image)
            plt.show()
            
            if update_metadict:
                pic_dict = {
                    'height_numpy_array_filepath': height_array_name,
                    'optical_numpy_array_filepath': optical_array_name,
                    }
                _,_ = Meta.meta_index_lookup(goa_filename, update_dict=pic_dict)
                _,_ = Meta.meta_index_lookup(gha_filename, update_dict=pic_dict)
        
        #TODO: add a bunch of necessary shit to the 'output_dict' for logging, etc. 
        return output_dict
    
    
        
##################################################################################################
###    Keyence     ###############################################################################
##################################################################################################


class SEM:

    ''' v1.0.0   created:2024-08-06   modified:2025-07-01
    Wrapper class for stitching SEM images from Quanta 200 and JEOL instruments.
    NOT a generic SEM class; very niche and kind of garbage. Needs a lot of work.
    
    TODO:
        - Consider making into an actual object class that's intialized on a set of images to be stitched or handled.
        -
    '''
    
    version = '1.1.0'
    version_mod_date = '2025-07-01'
    
    global GFA, gfa_x_edges, gfa_y_edges, GFA_dict

    homography_match_threshholds = [0.2, 0.4, 0.5, 0.6, 0.8]
    minimum_homography_matches = 5
    
    @staticmethod
    def sort_filenames(these_filenames):
    
        ''' v1.2  modified 2025-07-01
        INPUT:  list of filenames
        ACTION: sort filenames by index unless they have a '_X000_Y000' component (JEOL standard for montage),
                in which case sort them by those X-Y indices.
                Required because the stitching code assumes a left-to-right, top-to-bottom order of images;
                should probably change that in the future (TODO).
        OUTPUT: sorted list of filenames.
        '''
    
        # Initialize new filename list
        sorted_filenames = []
        possible_sorted_names = []
        original_basenames = [os.path.basename(filename) for filename in these_filenames]
        
        test_filename = these_filenames[0]
        under_split_test_filename = test_filename.replace('.tif','').split('_')
    
        # Flag for JEOL naming of montage images
        # NOTE: this whole section will fail if there are >99 rows or columns in the montage
        if '_X0' in test_filename and '_Y0' in test_filename:
            # Run through list once to get maximum 'X' and 'Y' in the list
            max_x = 0
            max_y = 0
            for filename in these_filenames:
                split_list = os.path.basename(filename.replace('.tif', '')).split('_')
                for item in split_list:
                    if 'X' in item:
                        x_int = int(item.replace('X', ''))
                        if x_int > max_x:
                            max_x = x_int
                    if 'Y' in item:
                        y_int = int(item.replace('Y', ''))
                        if y_int > max_y:
                            max_y = y_int
    
            # Create a basename
            split_list = os.path.basename(filename.replace('.tif', '')).split('_')
            basename = split_list[0]
            for item in split_list[1::]:
                if 'X' not in item and 'Y' not in item:
                    basename = basename+'_'+item
            base_path = os.path.dirname(these_filenames[0])
    
            # Re-order and create a possible match list
            for y_idx in range(0,max_y+1):
                for x_idx in range(0,max_x+1):
                    x_zero_len = 3 - len(str(x_idx))
                    y_zero_len = 3 - len(str(y_idx))
                    this_basename = f"_X{'0'*x_zero_len}{x_idx}_Y{'0'*y_zero_len}{y_idx}.tif"
                    possible_sorted_names.append(this_basename)
    
            # Run through the possible, sorted list and add any from the original list that appear
            for basename in possible_sorted_names:
                for original_basename in original_basenames:
                    if basename in original_basename:
                        sorted_filenames.append(os.path.join(base_path, original_basename))
                        
        #For Quanta 200 and generic formats where last part of filename is an imaging index
        elif under_split_test_filename[-1].isnumeric():
            #TODO: do the actual sorting, but it honestly doesn't matter
            sorted_filenames = these_filenames
        
        return sorted_filenames
    
        
    @staticmethod
    def open_without_databar(filename):
    
        ''' v2.0 modified 2024-11-03
        '''
        
        # Make the databar offset value global for edge cases where TIF tag reading fails (1:1000 case)
        global databar_offset
        
        # Open the image in binary, read-only mode and then in Python Image Library (PIL) as an 'Image' object
        im = open(filename, 'rb')
        img = PIL.Image.open(im)
        
    
        # Use PIL's tag library to read the TIF metadata
        tag_dict = {}
        for key in img.tag_v2:
            try:
                tag_dict.update({TAGS[key] : img.tag[key]}) 
            except KeyError:
                tag_dict.update({key : img.tag[key]})
    
        # Parse the tag contents and store them as variables        
        try:
            # Quanta 200, FEI instrument
            # The single non-standard tag contains all the SEM data
            offset = 40  #pixels to skip around edges to get rid of scan errors
            mishmash = tag_dict[34682]
            mishmash= mishmash[0].replace(u'\r', '').split(u'\n')
            for line in mishmash:
                if "Databarheight" in line:
                    databar_offset = int(line.split('=')[1])
    
            # Store the image dimensions provided as standard TIF tag headings
            img_width = int(tag_dict['ImageWidth'][0])
            img_height = int(tag_dict['ImageLength'][0])
    
        except KeyError as ie:
            # JSM-IT510
            offset = 2 #pixels to skip around edges to get rid of scan errors
            databar_offset = 0
            # Store the image dimensions provided as standard TIF tag headings
            img_width = int(tag_dict['ImageWidth'][0])
            img_height = int(tag_dict['ImageLength'][0])
    
            # Find the matching text file for the image
            # Get base filepath (image/text agnostic)
            base_filename = filename.replace('.tif','')
            mishmash = open(base_filename+'.txt', 'r')
            for line in mishmash:
                if "PNU_HEIGHT" in line:
                    databar_offset = int(line.split(' ')[1])
                    tag_dict["DatabarHeight"] = databar_offset

            
        # Reshape the imported image data 
        try:
            np_img = np.array(img.getdata())
        except:
            np_img = np.array(img)
        w, h = img.size
        np_img.shape = (h, w, np_img.size // (w * h))
        np_img = np_img[offset:(img_height-databar_offset-offset), offset:(img_width-offset)]
        clean_img = np_img.astype(np.uint8)
    
        xdim = clean_img.shape[0]
        ydim = clean_img.shape[1]
        try:
            pil_image = PIL.Image.fromarray(clean_img.astype('uint8'))
        except:
            pil_image = PIL.Image.fromarray(clean_img[offset:xdim-offset, offset:ydim-offset, 0].astype('uint8'))
        
        return clean_img

    @staticmethod
    def tiff_tag_getter(filename):
        
        ''' v2.3 modified 2024-11-01
        '''
    
        # Initalize dictionary
        tag_dict = {}
    
        #print("working on ", os.path.basename(filename))
        # Open the image in binary, read-only mode and then in Python Image Library (PIL) as an 'Image' object
        im = open(filename, 'rb')
        img = PIL.Image.open(im)
    
        # Use PIL's tag library to read the TIF metadata
        pic_dict = {}
        for key in img.tag_v2:
            try:
                pic_dict.update({TAGS[key] : img.tag[key]}) 
            except KeyError:
                pic_dict.update({key : img.tag[key]})
    
        # Store the image dimensions provided as standard TIF tag headings
        img_width = int(pic_dict['ImageWidth'][0])
        img_height = int(pic_dict['ImageLength'][0])
    
        # Parse the tag contents and store them as variables        
        try:
            # Quanta 200, FEI instrument
            # The single non-standard tag contains all the SEM data
    
            mishmash = pic_dict[34682]
            mishmash= mishmash[0].replace(u'\r', '').split(u'\n')
            for line in mishmash:
                if "Databarheight" in line:
                    databar_offset = int(line.split('=')[1])
    
        except KeyError:
            # JSM-IT510
            databar_offset = 0
            tag_dict["DatabarHeight"] = databar_offset
    
            # Find the matching text file for the image
            # Get base filepath (image/text agnostic)
            base_filename = filename.replace('.tif','')
            mishmash = open(base_filename+'.txt', 'r')
    
        for line in mishmash:
            #####################################################
            # FEI instrument
            if "HV=" in line:
                hv = int(line.split('=')[1])
                tag_dict["HV"] = hv
    
            elif "PixelHeight"in line:
                pix_h  = float(line.split('=')[1])
                tag_dict["PixelHeight"] = pix_h
    
            elif "PixelWidth"in line:
                pix_w  = float(line.split('=')[1])
                tag_dict["PixelWidth"] = pix_w
    
            elif "Horfieldsize" in line:
                img_hor_dim  = float(line.split('=')[1])
                tag_dict["HorizontalSize"] = img_hor_dim
    
            elif "Verfieldsize" in line:
                img_ver_dim  = float(line.split('=')[1])
                tag_dict["VerticalSize"] = img_ver_dim
    
            elif "StageX=" in line:
                stage_x = float(line.split('=')[1])
                tag_dict["StageX"] = stage_x
    
            elif "StageY=" in line:
                stage_y = float(line.split('=')[1])
                tag_dict["StageY"] = stage_y
    
            elif "Databarheight" in line:
                databar_offset = int(line.split('=')[1])
                tag_dict["DatabarHeight"] = databar_offset
    
            #####################################################
            # JEOL instrument
            elif "GUN_VOLT" in line:
                tag_dict["HV"] = float(line.split(' ')[1]) *1000   #convert from kV to V
    
            elif "FIELD_OF_VIEW" in line:
                hor_string = line.split(' ')[1]
                if 'Â' in hor_string:
                    hor_string = hor_string.replace('Â', '')
                if 'mm' in hor_string:
                    img_hor_dim  = float(hor_string.replace('mm', ''))/1000   #convert from mm to m
                elif 'µm' in hor_string:
                    img_hor_dim  = float(hor_string.replace('µm', ''))/1000000   #convert from mm to m
                ver_string = line.split(' ')[2]
                if 'Â' in ver_string:
                    ver_string = ver_string.replace('Â', '')
                if 'mm' in hor_string:
                    img_ver_dim  = float(hor_string.replace('mm', ''))/1000   #convert from mm to m
                elif 'µm' in hor_string:
                    img_ver_dim  = float(hor_string.replace('µm', ''))/1000000   #convert from mm to m

                tag_dict["HorizontalSize"] = img_hor_dim
                tag_dict["VerticalSize"] = img_ver_dim
                # Divide the field of view by the pixel number to get pixel height and width in real terms
                tag_dict["PixelHeight"] = img_ver_dim/img_height
                tag_dict["PixelWidth"] = img_hor_dim/img_width
    
            elif "STAGE_POSITION" in line:
                positions = line.split(' ')
                stage_x = float(positions[1])
                stage_y = float(positions[2])
                stage_z = float(positions[3])
                # three more datapoints ([4], [5], [6]); R T ?
                tag_dict["StageX"] = stage_x/1000   #convert from mm to m
                tag_dict["StageY"] = stage_y/1000   #convert from mm to m
                
            elif "PNU_HEIGHT" in line:
                databar_offset = int(line.split(' ')[-1])
                tag_dict["DatabarHeight"] = databar_offset
    
        # Store the image dimensions provided as standard TIF tag headings
        img_width = int(pic_dict['ImageWidth'][0])
        tag_dict["ImageWidth"] = img_width
        img_height = int(pic_dict['ImageLength'][0])
        tag_dict["ImageLength"] = img_height
        tag_dict['ImageHeight'] = img_height
        
        return tag_dict
    

    @staticmethod
    def make_GFA_dimensions(filenames, padding = 500, update_metadict = False, process_name = ''):
        
        ''' v2.3.7? modified 2024-01-30
        INPUT: A list of filenames
        ACTION: Addition
        OUTPUT: A list of X-dimension and Y-dimension edges for all the TIFF images in the INPUT list
        '''
    
        #   Initialize some business
        image_x_list = []
        image_y_list = []
        pix_widths = []
        pix_heights = []
        resolution = 1   # This should never change unless you have a very good reason and have rewritten the code
        
        #TODO: need a better way to flag 'jeol' vs. other SEM data
        # Check if the images are probably taken from JEOL SEM
        if '_X0' in filenames[0] and '_Y0' in filenames[0]:
            jeol_data = True
        else:
            jeol_data = False
    
        # Step through each image to populate the location data for the GFA
        for filename in filenames:
            #print("working on ", os.path.basename(filename))
            # Open the image in binary, read-only mode and then in Python Image Library (PIL) as an 'Image' object
            #im = open(filename, 'rb')
            #img = PIL.Image.open(im)
    
            # Load image parameters from either the TIF itself or an image text file
            tag_dict = SEM.tiff_tag_getter(filename)
    
            # Assign tags to variables; assignment just makes the rest of the code easier
            hv = tag_dict["HV"]
            pix_h = tag_dict["PixelHeight"]
            pix_w = tag_dict["PixelWidth"]
            img_hor_dim = tag_dict["HorizontalSize"]
            img_height = tag_dict["VerticalSize"]
            stage_x = tag_dict["StageX"]
            stage_y = tag_dict["StageY"]
            databar_offset = tag_dict["DatabarHeight"]
            img_width = tag_dict['ImageWidth']
            img_height = tag_dict['ImageHeight']
    
            # Add values to list; only useful for systems with manually-collected images (FEI system)
            #   This lets you see if the images change size during the collection.
            #   Needed to guess at X-Y extent calculation with padding.
            pix_widths.append(pix_w)
            pix_heights.append(pix_h)
    
            if jeol_data:
                # Append the left/right and top/bottom coordinates of the image
                image_x_list.append(stage_x)
                image_x_list.append(stage_x-img_hor_dim)
                image_y_list.append(stage_y)
                   #Adjust the y-value for databar
                image_y_list.append(stage_y+(pix_h*(img_height-databar_offset)))
    
            else:
                # Append the left/right and top/bottom coordinates of the image
                image_x_list.append(stage_x)
                image_x_list.append(stage_x+img_hor_dim)
                image_y_list.append(stage_y)
                   #Adjust the y-value for databar
                image_y_list.append(stage_y-(pix_h*(img_height-databar_offset)))
                
            if update_metadict:
                meta_dict_index, status = Meta.meta_index_lookup(filename, update_dict = tag_dict)
                
            
        if jeol_data:
            min_x = min(image_x_list) - (pix_w*padding)
            max_x = max(image_x_list)   
            min_y = min(image_y_list) - (pix_h*padding)
            max_y = max(image_y_list) 
        else:
            min_x = min(image_x_list) - (pix_w*padding)   # Add padding so stitching has room to work
            max_x = max(image_x_list)
            min_y = min(image_y_list) - (pix_h*padding)   # Add padding so stitching has room to work
            max_y = max(image_y_list)
            
        if len(set(pix_widths))==1:
            pix_width = pix_widths[0]/resolution
            x_dim = round(abs(max_x-min_x)/(pix_width))
        else:
            pix_width = max(pix_widths)/resolution
            x_dim = round(abs(max_x-min_x)/(pix_width))
    
        if len(set(pix_heights))==1:
            pix_height = pix_heights[0]/resolution
            y_dim = round(abs(max_y-min_y)/(pix_height))
        else:
            pix_height = max(pix_heights)/resolution
            y_dim = round(abs(max_y-min_y)/(pix_height))
    
        # Double-'padding' is added to dimensions to account for 'padding' on each edge of the total image
        gfa_x_edges = [(min_x+(pix_width*i)) for i in range(x_dim+(padding*2))]    # List of left-edge locations to make an array
        gfa_y_edges = [(min_y+(pix_height*i)) for i in range(y_dim+(padding*2))]    # List of top-edge locations to make an array
    
        # JEOL: x idx 0-X goes high-low; y idx 0-Y goes low-high
        #  FEI: x idx 0-X goes low-high; y idx 0-Y goes high-low
        if jeol_data:
            gfa_x_edges.reverse()
        #TODO: make this 'else' an 'elif' and define each instrument type somehow
        else:
            gfa_y_edges.reverse()
            
        return gfa_x_edges, gfa_y_edges


    def img_GFA_homography(img1_filename, gfa_x_edges, gfa_y_edges, GFA, \
                          show_match_pic= True, algorithm = 'SIFT', threshold = 0.2,\
                          show_match_scatter=False, GFA_comparison_padding = 500, \
                          expected_x_shift =0, expected_y_shift = 0):
        
        ''' v3.0 modified 2024-11-10
        INPUT:    Filenames for two TIFF images to compare.
        ACTION:   Image features are detected with SIFT algorithm.
                  Matches between features is determined by K-Nearest Neighbor.
                  A thresholded average of matching features is used to determine the pixel-shift between them.
        OUTPUT:   X-shift and Y-shift in pixels between the images.
        '''
        
        #Force int for 'GFA_comparison_padding'
        GFA_comparison_padding = int(GFA_comparison_padding)
        
        # Open the images and pull the metadata
        im1 = SEM.open_without_databar(img1_filename)
          #create a frame around the image to match the padding around the 'expected' location in the GFA
        #im1 = np.pad(im1, (GFA_comparison_padding, GFA_comparison_padding), 'constant', constant_values=(0))
        im1_dict = SEM.tiff_tag_getter(img1_filename)
           # Convert images to grayscale (if not already)
        #im1Gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
        
        # Check if the images are probably taken from JEOL SEM
        if '_X0' in img1_filename and '_Y0' in img1_filename:
            jeol_data = True
        else:
            jeol_data = False
        
        # Get img x and y spatial location and relate to GFA indices
        x_start = im1_dict['StageX']
        y_start = im1_dict['StageY']
        if jeol_data:
            x_end = x_start - (im1_dict['PixelWidth']*im1_dict['ImageWidth'])
            y_end = y_start + (im1_dict['PixelHeight']*im1_dict['ImageHeight'])
        else:
            x_end = x_start + (im1_dict['PixelWidth']*im1_dict['ImageWidth'])
            y_end = y_start - (im1_dict['PixelHeight']*im1_dict['ImageHeight'])
        
        # Pull the GFA indices to compare against image
           # For x start and end
        gfa_x_start_list = [abs(x_start-x_edge) for x_edge in gfa_x_edges]
        gfa_x_start_min = min(gfa_x_start_list)
        gfa_x_start_index = gfa_x_start_list.index(gfa_x_start_min) 
        gfa_x_end_list = [abs(x_end-x_edge) for x_edge in gfa_x_edges]
        gfa_x_end_min = min(gfa_x_end_list)
        gfa_x_end_index = gfa_x_end_list.index(gfa_x_end_min) 
           # For y start and end
        gfa_y_start_list = [abs(y_start-y_edge) for y_edge in gfa_y_edges]
        gfa_y_start_min = min(gfa_y_start_list)
        gfa_y_start_index = gfa_y_start_list.index(gfa_y_start_min)
        gfa_y_end_list = [abs(y_end-y_edge) for y_edge in gfa_y_edges]
        gfa_y_end_min = min(gfa_y_end_list)
        gfa_y_end_index = gfa_y_end_list.index(gfa_y_end_min)
        
        #Get indices for GFA inset that correspond to expected image addition location
        gfa_x_list = [gfa_x_start_index + expected_x_shift, gfa_x_end_index + expected_x_shift]
        gfa_y_list = [gfa_y_start_index + expected_y_shift, gfa_y_end_index + expected_y_shift]
          #if indices are outside GFA dimensions, coerce to possible dimensions
          #calculate shift for adjust 'x_shift' by padding coordinate change
            #i.e. if the padding is 500, the ('y_shift', 'x_shift) would be (500, -500) for JEOL and (-500, 500) for Quanta
            #coordinates corresponding to pixel values (pixels always Y(+) down, X(+) right)
            # JEOL: spatial coordinates Y(+) down, (X+) left
            # Quanta: spatial coordinates Y(+) up, (X+) right
        inset_x_min = min(gfa_x_list)- GFA_comparison_padding
        if inset_x_min < 0:
            actual_x_inset_shift = GFA_comparison_padding + inset_x_min
            inset_x_min = 0
        else:
            actual_x_inset_shift = GFA_comparison_padding
            
        inset_y_min = min(gfa_y_list)- GFA_comparison_padding
        if inset_y_min < 0:
            actual_y_inset_shift = GFA_comparison_padding + inset_y_min
            inset_y_min = 0
        else:
            actual_y_inset_shift = GFA_comparison_padding
        
        inset_x_max = (max(gfa_x_list) + GFA_comparison_padding)
        if inset_x_max > (GFA.shape[1]-1):
            inset_x_max = (GFA.shape[1]-1)
            
        inset_y_max = (max(gfa_y_list) + GFA_comparison_padding)
        if inset_y_max > (GFA.shape[0]-1):
            inset_y_max = (GFA.shape[0]-1)
            
        gfa_inset = GFA[inset_y_min: inset_y_max, inset_x_min: inset_x_max].astype(np.uint8)
    
        #TODO: Verify in SURF/ORB documentation that these settings make sense
        if algorithm == 'SIFT' or algorithm =='sift':
            # Applying SIFT detector
            sift = cv2.SIFT_create() 
            kp1, des1 = sift.detectAndCompute(im1, None)
            kp2, des2 = sift.detectAndCompute(gfa_inset, None)
        elif algorithm == 'SURF' or algorithm =='surf':
            surf = cv2.xfeatures2d.SURF_create(400)
            kp1, des1 = surf.detectAndCompute(im1, None)
            kp2, des2 = surf.detectAndCompute(gfa_inset, None)
        elif algorithm == 'ORB' or algorithm =='orb':
            orb = cv2.ORB_create(400)
            kp1, des1 = orb.detectAndCompute(im1, None)
            kp2, des2 = orb.detectAndCompute(gfa_inset, None)
        elif algorithm == 'AKAZE' or algorithm == 'akaze':
            akaze = cv2.AKAZE_create()
            kp1, des1 = akaze.detectAndCompute(im1, None)
            kp2, des2 = akaze.detectAndCompute(gfa_inset, None)
            
        if show_match_pic:
            # Marking the keypoint on the image using circles
            img1=cv2.drawKeypoints(im1 ,
                                  kp1 ,
                                  im1 ,
                                  flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        
            img2=cv2.drawKeypoints(gfa_inset ,
                                  kp2 ,
                                  gfa_inset ,
                                  flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        
        try:    #If no matches, a TypeError will pop, in which case just skip all of the following and set everything to zero
            if len(des1)>0 and len(des2)>0:
                if algorithm == 'ORB' or algorithm == 'AKAZE':
                    # BFMatcher with default params
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING)   #crossCheck=True
                    matches = bf.knnMatch(des1, des2, k=2)
                    #matches = sorted(matches, key = lambda x:x.distance)
                    
                if algorithm =='SURF' or algorithm=='SIFT':
                    #FLANN parameters
                    #FLANN_INDEX_KDTREE = 0
                    #index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
                    #search_params = dict(checks=50)   # or pass empty dictionary
                    #flann = cv2.FlannBasedMatcher(index_params,search_params)
                    #matches = flann.knnMatch(des1,des2,k=2)
                    
                    # BFMatcher with default params
                    bf = cv2.BFMatcher()   #crossCheck=True
                    matches = bf.knnMatch(des1, des2, k=2)
                    #matches = sorted(matches, key = lambda x:x.distance)
                
            else:
                matches = []            
            
            #TODO: alter match checking and following distance shift to be smarter
            # Apply ratio test
            good = []
            run_flag = True
            #Run through increasingly lax match criteria until minimum match number is met    
            for idx, threshold in enumerate(SEM.homography_match_threshholds):
                
                #Flag if this is the last threshold to try
                if idx >= len(SEM.homography_match_threshholds):
                    run_flag = False
                
                if run_flag:
                    #Try to get a good set of matches
                    try:
                        for m,n in matches:
                            if m.distance < threshold * n.distance:   #NOTE: this distance is adjustable. 0.4 is middling strict, 0.7 is lax.
                                good.append([m])
                        print(len(good), ' matches with threshold of ', threshold)
                    except ValueError:
                        print(f"Error in matches: {matches}")
                    
                if (len(good) > SEM.minimum_homography_matches):
                    run_flag = False
                
            # Pull the actual coordinates for the best matches
            list_kp1 = []
            list_kp2 = []
            for match in good:
                # Get the matching keypoints for each of the images
                img1_idx = match[0].queryIdx
                img2_idx = match[0].trainIdx
    
                # x - columns
                # y - rows
                # Get the coordinates
                (x1, y1) = kp1[img1_idx].pt
                (x2, y2) = kp2[img2_idx].pt
    
                # Append to each list
                list_kp1.append((x1, y1))
                list_kp2.append((x2, y2))
    
            # Find the differences between the matched image feature dimensions    
            x_dif = []
            y_dif = []
            for index in range(len(list_kp1)):
                x1, y1 = list_kp1[index]
                x2, y2 = list_kp2[index]
                x_dif.append(x2-x1)
                y_dif.append(y2-y1)
    
            # Make numpy arrays because why not
            x_array = np.array(x_dif)
            y_array = np.array(y_dif)    
            orig_x_len = len(x_array)
            orig_y_len = len(y_array)
            xy_array = [(round(x, 2),round(y,2)) for x,y in zip(x_array,y_array)]
            
            if show_match_pic:
                # cv.drawMatchesKnn expects list of lists as matches.
                img3 = cv2.drawMatchesKnn(im1,kp1,gfa_inset,kp2,good,None,flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
                plt.figure(figsize=(10, 20))
                plt.imshow(img3)
                plt.title(f"Mathpics for {img1_filename}")
                plt.show()
    
            if show_match_scatter:
                plt.title(f"Mathed points for {img1_filename}")
                plt.xlabel(f"X-shifts (subtract {GFA_comparison_padding} for actual pixel shift)")
                plt.ylabel("Y-shifts (subtract padding for real indices)")
                plt.scatter(x_array, y_array)
                plt.show()
            
            match_number = min([len(x_array), len(y_array)])
            
            # Calculate the 'center of mass' of match points based on euclidian distance
               # Some instances of match may produce split array lengths
               
            weighted_x, weighted_y = Utilities.get_weighted_xy_mean(x_array, y_array)
            
            #Assign x-shift and y-shift, and calculate error between found matchpoints and 'final' shift
              #otherwise, shift is relative to a changed 0,0 coordinate
            x_shift = weighted_x
            y_shift = weighted_y
            x_residual_sum = sum([round(abs(x-x_shift),3) for x in x_array])
            y_residual_sum = sum([round(abs(y-y_shift),3) for y in y_array])
              #
            x_shift = weighted_x - actual_x_inset_shift
            y_shift = weighted_y - actual_y_inset_shift
        
        except TypeError as TE:
            print()
            print("Failure in image-to-image homography.")
            print(TE)
            x_shift = 0
            y_shift = 0
            x_residual_sum = 0
            y_residual_sum = 0
            match_number = 0
            
        return x_shift, y_shift, match_number, x_residual_sum, y_residual_sum

    
    @staticmethod
    def homography_stitch(filenames, 
                          guess_and_check = False,
                          show_guess_checking = False,
                          show_matchpics = True,
                          show_match_scatter = True,
                          user_input = False,
                          show_final_GFA = False,
                          save_final_GFA = False,
                          show_final_annotated = False,
                          save_final_annotated = True,
                          overright_GFA = True,
                          algo = 'SIFT',
                          update_metadict = False,
                          save_alternate_location = '',
                          shift_dict = {},
                          global_manual_shift = {
                              'manual_x_shift':0,
                              'manual_y_shift':0
                              },
                          average_error_threshold = 50
                          ):
        
        global GFA, gfa_x_edges, gfa_y_edges, GFA_dict
        
        ''' v3.3  modified 2024-11-10
        INPUT:
        ACTION:
        OUTPUT:
            (Explicit)
        
        '''
    
        # Run through ALL the images to get TIF metadata and populate the X-Y spatial dimensions of the final image
        gfa_x_edges, gfa_y_edges = SEM.make_GFA_dimensions(filenames, padding = 500, update_metadict = update_metadict)
    
        # Initialize the array that stores the final image with padding on each dimension
        GFA = np.zeros((len(gfa_y_edges), len(gfa_x_edges)))
        print("Final GFA shape: ", GFA.shape)
           # Initialize the sister array that stores the number of values added to each index
           # Used to average the pixel sum in the last step of stitching
        gfa_count = np.zeros((len(gfa_y_edges), len(gfa_x_edges)))

        # Initialize some global variables
        x_shift_list =[]
        y_shift_list =[]
        xy_loc_list = []
        GFA_dict = {
            'file_summary':{},
            'jeol_data?':False,
            }
          # Check if the images are probably taken from JEOL SEM
        if '_X0' in filenames[0] and '_Y0' in filenames[0]:
            jeol_data = True
            GFA_dict['jeol_data?'] = True
        else:
            jeol_data = False
        #Intialize filename for meta_dict updates
        folder_name = os.path.basename(os.path.dirname(filenames[0]))
        folder_path = os.path.dirname(os.path.dirname(filenames[0]))
        this_datetime = datetime.datetime.now()
        if jeol_data:        
            detector_name ='UNK'
            for part in os.path.basename(filenames[0]).split('_'):
                print(part)
                if 'BED' in part:
                    detector_name = part
                if 'SED' in part:
                    detector_name = part
            meta_key_name = folder_name+ f"_{detector_name}"+'_HomographyStitch_' + algo +'_'
        else:
            meta_key_name = folder_name+'_HomographyStitch_' + algo +'_'
    
        for file_index, filename in tqdm(enumerate(filenames)):
            print()
            print("Running file ", file_index+1, ' of ', len(filenames))
    
            # For the first file, just drop it into the GFA
            if file_index==0:
                np_img = SEM.open_without_databar(filename)
                img_dict = SEM.tiff_tag_getter(filename)
                #plt.imshow(np_img)
                #plt.show()
    
                # Pull the img shape dimensions and TIF tag metadata
                x_dim = np_img.shape[1]
                y_dim = np_img.shape[0]
                stage_x = img_dict['StageX']
                stage_y = img_dict['StageY']
                pix_w = img_dict['PixelWidth']
                pix_h = img_dict['PixelHeight']
                databar_offset = img_dict['DatabarHeight']
                
    
                # List out the spatial location expected for each pixel index
                if jeol_data:
                    x_edges = [(stage_x-(pix_w*i)) for i in range(x_dim)]
                    y_edges = [(stage_y+(pix_h*i)) for i in range(y_dim)]
                else:
                    x_edges = [(stage_x+(pix_w*i)) for i in range(x_dim)]
                    y_edges = [(stage_y-(pix_h*i)) for i in range(y_dim)]
                    
                
                #Get x_start and y_start indices from edge lists
                   # For x start and end
                gfa_x_start_list = [abs(stage_x-x_edge) for x_edge in gfa_x_edges]
                gfa_x_start_min = min(gfa_x_start_list)
                x_gfa = gfa_x_start_list.index(gfa_x_start_min)
                   # For y start and end
                gfa_y_start_list = [abs(stage_y-y_edge) for y_edge in gfa_y_edges]
                gfa_y_start_min = min(gfa_y_start_list)
                y_gfa = gfa_y_start_list.index(gfa_y_start_min)
                
    
                # Assign the image pixels to their appropriate place in the GFA
                #   Add 1 to the count for that array location whenever a value is added to the sum so an average can be taken later
                if overright_GFA:
                    this_entry = np_img[::, ::, 0]
                else:
                    this_entry = GFA[y_gfa : y_gfa + np_img.shape[0], 
                                     x_gfa : x_gfa + np_img.shape[1]] + np_img[::, ::, 0]
                try:
                    GFA[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] = this_entry
                    gfa_count[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] += 1

                except IndexError:
                    #get array clash difference (amount of padding needed)
                      #if 'IndexError' was raised, either 'y_gfa' or 'x_gfa' must be bigger than that index of GFA
                    pad_size = int(max([
                        (y_gfa + np_img.shape[0]) - (GFA.shape[0]-1),
                        (x_gfa+np_img.shape[1]) - (GFA.shape[1]-1)
                        ]))
                    
                    #pad the GFA
                    GFA = np.pad(GFA, pad_size)
                    gfa_count = np.pad(gfa_count, pad_size)
                    
                #Dummy variables for file summary
                x_shift = 0
                y_shift = 0
                x_residual_sum = 0
                y_residual_sum = 0
    
            # For every file after the first one, pull the metadata, do homography matching
            # If the homography fit is garbage, revert to guess-and-check based on expected shifts
            else:
                np_img = SEM.open_without_databar(filename)
                img_dict = SEM.tiff_tag_getter(filename)
                #plt.imshow(np_img)
                #plt.show()
    
                # Pull the img shape dimensions and TIF tag metadata
                stage_x = img_dict['StageX']
                stage_y = img_dict['StageY']
                pix_w = img_dict['PixelWidth']
                databar_offset = img_dict['DatabarHeight']
                pix_h = img_dict['PixelHeight']
                x_dim = np_img.shape[1]
                y_dim = np_img.shape[0]
    
                # List out the spatial location expected for each pixel index
                if jeol_data:
                    x_edges = [(stage_x-(pix_w*i)) for i in range(x_dim)]  
                    y_edges = [(stage_y+(pix_h*i)) for i in range(y_dim)]
                else:
                    x_edges = [(stage_x+(pix_w*i)) for i in range(x_dim)]  
                    y_edges = [(stage_y-(pix_h*i)) for i in range(y_dim)]
    
                #Get x_start and y_start indices from edge lists
                   # For x start and end
                gfa_x_start_list = [abs(stage_x-x_edge) for x_edge in gfa_x_edges]
                gfa_x_start_min = min(gfa_x_start_list)
                x_gfa = gfa_x_start_list.index(gfa_x_start_min)
                   # For y start and end
                gfa_y_start_list = [abs(stage_y-y_edge) for y_edge in gfa_y_edges]
                gfa_y_start_min = min(gfa_y_start_list)
                y_gfa = gfa_y_start_list.index(gfa_y_start_min)
                
                #Guess at how big a shift there should be and look there in the GFA
                if len(x_shift_list)>0 and len(y_shift_list)>0:
                    x_shift_pred, y_shift_pred = Utilities.get_weighted_xy_mean(x_shift_list, y_shift_list)
                else:
                    x_shift_pred= 0
                    y_shift_pred= 0
    
                # 'SIFT'   'AKAZE'   'ORB'   'SURF'
                algorithm = algo   #'SIFT' works, 'SURF' needs work, and 'ORB' needs to be optimized
                x_shift, y_shift, match_count, x_residual_sum, y_residual_sum = SEM.img_GFA_homography(filename, gfa_x_edges, gfa_y_edges, \
                                                                GFA, \
                                                                show_match_pic=show_matchpics, \
                                                                show_match_scatter= show_match_scatter, \
                                                                algorithm = algorithm, threshold = 0.4,\
                                                                expected_x_shift = x_shift_pred,\
                                                                expected_y_shift = y_shift_pred)
                residual_error = x_residual_sum + y_residual_sum
                    
                print()
                print("Residual error (x&y):  ", residual_error)
                if match_count >1:
                    print("Avg. X-error: ", round(x_residual_sum/(match_count), 2))
                    print("Avg. Y-error: ", round(y_residual_sum/(match_count), 2))
                
                #Apply manual shift 
                #TODO: create the ability for individual filenames to be shifted by specific amounts.
                if len(shift_dict) >0:
                    pass
                else:
                    x_shift = x_shift + global_manual_shift['manual_x_shift'] 
                    y_shift = y_shift + global_manual_shift['manual_y_shift'] 
    
                if guess_and_check:
                    #TODO: add this functionality back in
                    #SEM.guess_and_check(x_shift, y_shift, GFA, )
                    pass
    
                #If no shift is calculated, try and guess based on actual good shifts
                  #save the these shifts to the list if they're 'good' 
                if (x_shift != 0) and (y_shift!=0) and (residual_error !=0):
    
                    #if residual error is 'too high', coerce to average shift or don't apply a shift at all 
                    if (x_residual_sum/match_count) > average_error_threshold:
                        if len(x_shift_list)>0 :
                            x_shift,_ = Utilities.get_weighted_xy_mean(x_shift_list, y_shift_list)
                        #default to just 0's if all else fails; typically just for first few (first 1-3) images where shift doesn't matter yet anyway
                        else:
                            x_shift = 0
                    
                    if (y_residual_sum/match_count) > average_error_threshold:
                        if len(y_shift_list)>0:
                            _,y_shift = Utilities.get_weighted_xy_mean(x_shift_list, y_shift_list)
                        #default to just 0's if all else fails; typically just for first few (first 1-3) images where shift doesn't matter yet anyway
                        else:
                            y_shift = 0
                     
                    #save both x and y locations if below threshold
                      #need to save them together to get euclidian distance function for weightin 
                    if ((y_residual_sum/match_count) < average_error_threshold) and (x_residual_sum/match_count) < average_error_threshold: 
                        x_shift_list.append(x_shift)
                        y_shift_list.append(y_shift)
                    
                  #coerce shift to average 'good' shift if everything is 0 (the homography failed completetly)
                else:
                    if len(x_shift_list)>0 and len(y_shift_list)>0:
                        x_shift, y_shift = Utilities.get_weighted_xy_mean(x_shift_list, y_shift_list)
                    #default to just 0's if all else fails; typically just for first few (first 1-3) images where shift doesn't matter yet anyway
                    else:
                        x_shift = 0
                        y_shift = 0
                        
                #Assign homography shift to raw spatially-assigned pixel location
                x_gfa = int(x_gfa + x_shift)
                y_gfa = int(y_gfa + y_shift)
                
                print("x-shift by homography: ", x_shift)
                print("y-shift by homography: ", y_shift)
       
                
                #Update metadict with info about this image
                if update_metadict:
                    pic_dict = {
                        meta_key_name: {
                            'stitch_x0_idx': x_gfa,
                            'stitch_y0_idx': y_gfa,
                            }
                        }
                    _,_ = Meta.meta_index_lookup(filename, update_dict=pic_dict)
    
                # Assign the image pixels to their appropriate place in the GFA
                #   Add 1 to the count for that array location whenever a value is added to the sum so an average can be taken later
                    # for i_x in range(len(x_gfa_indices)):
                    #    x_gfa = int(x_gfa_indices[i_x] + x_shift)   # Force int; not sure why it is ever not an int
                    #    for i_y in range(len(y_gfa_indices)):
                    #       y_gfa = int(y_gfa_indices[i_y] + y_shift)   # Force int
                
                
                if overright_GFA:
                    this_entry = np_img[::, ::, 0]
                else:
                    this_entry = GFA[y_gfa : y_gfa + np_img.shape[0], 
                                     x_gfa : x_gfa + np_img.shape[1]] + np_img[::, ::, 0]
                try:
                    GFA[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] = this_entry
                    gfa_count[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] += 1
                
                # Flagged if indices fail
                except IndexError:
                    #get array clash difference (amount of padding needed)
                      #if 'IndexError' was raised, either 'y_gfa' or 'x_gfa' must be bigger than that index of GFA
                    pad_size = int(max([
                        (y_gfa + np_img.shape[0]) - (GFA.shape[0]-1),
                        (x_gfa+np_img.shape[1]) - (GFA.shape[1]-1)
                        ]))
                    
                    #pad the GFA and try appending again
                    GFA = np.pad(GFA, pad_size)
                    gfa_count = np.pad(gfa_count, pad_size)
                    
                    GFA[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] = this_entry
                    gfa_count[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] += 1
                    
                #Flagged if array can't be cast into GFA
                #   Identical to error solution above; may leverage different solutions in the future so 
                #     keeping errors split for that reason now.
                except ValueError:
                    #get array clash difference (amount of padding needed)
                      #if 'IndexError' was raised, either 'y_gfa' or 'x_gfa' must be bigger than that index of GFA
                    pad_size = int(max([
                        (y_gfa + np_img.shape[0]) - (GFA.shape[0]-1),
                        (x_gfa+np_img.shape[1]) - (GFA.shape[1]-1)
                        ]))
                    
                    #pad the GFA and try appending again
                    GFA = np.pad(GFA, pad_size)
                    gfa_count = np.pad(gfa_count, pad_size)
                    
                    GFA[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] = this_entry
                    gfa_count[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] += 1
            
            #Append locations to annotation list for plotting on annotation figure
            xy_loc_list.append( (x_gfa, y_gfa) )
            
            #Update dict
            GFA_dict['file_summary'].update (
                {filename: {
                    'stage_x': img_dict['StageX'],
                    'stage_y': img_dict['StageY'],
                    'GFA_x_start': x_gfa,
                    'GFA_y_start': y_gfa,
                    'x_shift': x_shift,
                    'y_shift': y_shift,
                    'x_residual_sum': x_residual_sum,
                    'y_residual_sum': y_residual_sum
                    }
                    }
                )
        
        # Initialize the figure below
        if overright_GFA:
            gfa_count = np.ones((GFA.shape[0], GFA.shape[1]))
        fig, ax = plt.subplots()
        plt.figure(figsize=(20,17))
        plt.title(f"{filename} Stitched Image")        
        if show_final_GFA:
            ax.imshow(GFA)
    
        # Create annotations for GFA location
        for idx, (x, y) in enumerate(xy_loc_list):
            ax.text(x, y, str(idx), va='top', ha='left', color = 'w')
    
        # Create a useful filename for the GFA and save it to the same folder the images were pulled from
        folder_name = os.path.basename(os.path.dirname(filenames[0]))
        folder_path = os.path.dirname(os.path.dirname(filenames[0]))
        this_datetime = datetime.datetime.now()
        if jeol_data:        
            detector_name ='UNK'
            for part in os.path.basename(filenames[0]).split('_'):
                print(part)
                if 'BED' in part:
                    detector_name = part
                if 'SED' in part:
                    detector_name = part
            file_name = folder_name+ f"_{detector_name}"+'_HomographyStitch_' + algorithm +'_'+str(this_datetime).\
                split('.')[0].replace(":",'.')
        else:
            file_name = folder_name+'_HomographyStitch_' + algorithm +'_'+str(this_datetime).split('.')[0].replace(":",'.')
        gfa_filename = os.path.join(folder_path, file_name+".png")
        print("Saving file in location: ")
        print(gfa_filename)
        print()

        #Save the annotated version
        annot_filename = os.path.join(folder_path, 'Annotated_'+file_name+".png")
        if show_final_annotated:
            fig.savefig(annot_filename)
        if len(save_alternate_location)>0:
            try:
                annot_filename = os.path.join(save_alternate_location, 'Annotated_'+file_name+".png")
                fig.savefig(annot_filename)
            except:
                pass
        plt.title(f"{filename} Stitched Image")
        if show_final_annotated:
            plt.show()
        
        #Save file data dict as a json in same folder with images
        json_filepath = os.path.join(folder_path, file_name+".json")
        with open(json_filepath, 'w') as file:
            json.dump(GFA_dict, file, indent=4)
    
        #Save the array
        with open(gfa_filename, 'wb') as name:
            # This is primarily for summed bluring and other effects
            #np.save(name, np.divide(GFA, gfa_count))
            # This just saves the raw array
            np.save(name, GFA, gfa_count)
    
        #   Save the image of the array
        #gfa_image = PIL.Image.fromarray(np.divide(GFA, gfa_count))
        gfa_image = PIL.Image.fromarray(GFA)
        gfa_image = gfa_image.convert("L")
        if save_final_GFA:
            gfa_image.save(gfa_filename, format= "PNG")
        
        if len(save_alternate_location)>0:
            try:
                alt_location = os.path.join(save_alternate_location, file_name+".png")
                gfa_image.save(alt_location, format= "PNG")
            except:
                print('Alternate save location fail:')
                print("\t {save_alternate_location}")

        return GFA, gfa_image

    
    @staticmethod
    def spatial_stitch(filenames, 
                          guess_and_check = False,
                          overright_GFA = True,
                          update_metadict = False,
                          show_final_GFA = False,
                          save_final_GFA = False,
                          show_final_annotated = False,
                          save_final_annotated = True,
                          save_alternate_location = '',
                          shift_dict = {},
                          global_manual_shift = {
                              'manual_x_shift':0,
                              'manual_y_shift':0
                              }
                          ):
        
        global GFA, gfa_x_edges, gfa_y_edges, GFA_dict
        
        ''' v1.0  created:2024-11-11   modified 2024-11-11
        Take a list of filenames (TIFs as of v1.0) and drop them by X-Y location into a single array        
        '''
    
        # Run through ALL the images to get TIF metadata and populate the X-Y spatial dimensions of the final image
        gfa_x_edges, gfa_y_edges = SEM.make_GFA_dimensions(filenames, padding = 500, update_metadict = update_metadict)
    
        # Initialize the array that stores the final image with padding on each dimension
        GFA = np.zeros((len(gfa_y_edges), len(gfa_x_edges)))
        print("Final GFA shape: ", GFA.shape)
           # Initialize the sister array that stores the number of values added to each index
           # Used to average the pixel sum in the last step of stitching
        gfa_count = np.zeros((len(gfa_y_edges), len(gfa_x_edges)))

        # Initialize some global variables
        xy_loc_list = []
        GFA_dict = {
            'file_summary':{},
            'jeol_data?':False,
            'stitch_type': 'dumb-simple spaatial drop'
            }
          # Check if the images are probably taken from JEOL SEM
        if '_X0' in filenames[0] and '_Y0' in filenames[0]:
            jeol_data = True
            GFA_dict['jeol_data?'] = True
        else:
            jeol_data = False
        #Intialize filename for meta_dict updates
        folder_name = os.path.basename(os.path.dirname(filenames[0]))
        folder_path = os.path.dirname(os.path.dirname(filenames[0]))
        this_datetime = datetime.datetime.now()
        if jeol_data:        
            detector_name ='UNK'
            for part in os.path.basename(filenames[0]).split('_'):
                print(part)
                if 'BED' in part:
                    detector_name = part
                if 'SED' in part:
                    detector_name = part
            meta_key_name = folder_name+ f"_{detector_name}"+'_DumbStitch_' + '_'
        else:
            meta_key_name = folder_name+'_DumbStitch_' + '_'
    
        for file_index, filename in tqdm(enumerate(filenames)):
            print()
            print("Running file ", file_index+1, ' of ', len(filenames))
    
            # For the first file, just drop it into the GFA
            if file_index==0:
                np_img = SEM.open_without_databar(filename)
                img_dict = SEM.tiff_tag_getter(filename)
                #plt.imshow(np_img)
                #plt.show()
    
                # Pull the img shape dimensions and TIF tag metadata
                x_dim = np_img.shape[1]
                y_dim = np_img.shape[0]
                stage_x = img_dict['StageX']
                stage_y = img_dict['StageY']
                pix_w = img_dict['PixelWidth']
                pix_h = img_dict['PixelHeight']
                databar_offset = img_dict['DatabarHeight']
                
    
                # List out the spatial location expected for each pixel index
                if jeol_data:
                    x_edges = [(stage_x-(pix_w*i)) for i in range(x_dim)]
                    y_edges = [(stage_y+(pix_h*i)) for i in range(y_dim)]
                else:
                    x_edges = [(stage_x+(pix_w*i)) for i in range(x_dim)]
                    y_edges = [(stage_y-(pix_h*i)) for i in range(y_dim)]
                    
                
                #Get x_start and y_start indices from edge lists
                   # For x start and end
                gfa_x_start_list = [abs(stage_x-x_edge) for x_edge in gfa_x_edges]
                gfa_x_start_min = min(gfa_x_start_list)
                x_gfa = gfa_x_start_list.index(gfa_x_start_min)
                   # For y start and end
                gfa_y_start_list = [abs(stage_y-y_edge) for y_edge in gfa_y_edges]
                gfa_y_start_min = min(gfa_y_start_list)
                y_gfa = gfa_y_start_list.index(gfa_y_start_min)
                
    
                # Assign the image pixels to their appropriate place in the GFA
                #   Add 1 to the count for that array location whenever a value is added to the sum so an average can be taken later
                if overright_GFA:
                    this_entry = np_img[::, ::, 0]
                else:
                    this_entry = GFA[y_gfa : y_gfa + np_img.shape[0], 
                                     x_gfa : x_gfa + np_img.shape[1]] + np_img[::, ::, 0]
                try:
                    GFA[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] = this_entry
                    gfa_count[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] += 1

                except IndexError:
                    #get array clash difference (amount of padding needed)
                      #if 'IndexError' was raised, either 'y_gfa' or 'x_gfa' must be bigger than that index of GFA
                    pad_size = int(max([
                        (y_gfa + np_img.shape[0]) - (GFA.shape[0]-1),
                        (x_gfa+np_img.shape[1]) - (GFA.shape[1]-1)
                        ]))
                    
                    #pad the GFA
                    GFA = np.pad(GFA, pad_size)
                    gfa_count = np.pad(gfa_count, pad_size)
                    
                #Dummy variables for file summary
                x_shift = 0
                y_shift = 0
                x_residual_sum = 0
                y_residual_sum = 0
    
            # For every file after the first one, pull the metadata, do homography matching
            # If the homography fit is garbage, revert to guess-and-check based on expected shifts
            else:
                np_img = SEM.open_without_databar(filename)
                img_dict = SEM.tiff_tag_getter(filename)
                #plt.imshow(np_img)
                #plt.show()
    
                # Pull the img shape dimensions and TIF tag metadata
                stage_x = img_dict['StageX']
                stage_y = img_dict['StageY']
                pix_w = img_dict['PixelWidth']
                databar_offset = img_dict['DatabarHeight']
                pix_h = img_dict['PixelHeight']
                x_dim = np_img.shape[1]
                y_dim = np_img.shape[0]
    
                # List out the spatial location expected for each pixel index
                if jeol_data:
                    x_edges = [(stage_x-(pix_w*i)) for i in range(x_dim)]  
                    y_edges = [(stage_y+(pix_h*i)) for i in range(y_dim)]
                else:
                    x_edges = [(stage_x+(pix_w*i)) for i in range(x_dim)]  
                    y_edges = [(stage_y-(pix_h*i)) for i in range(y_dim)]
    
                #Get x_start and y_start indices from edge lists
                   # For x start and end
                gfa_x_start_list = [abs(stage_x-x_edge) for x_edge in gfa_x_edges]
                gfa_x_start_min = min(gfa_x_start_list)
                x_gfa = gfa_x_start_list.index(gfa_x_start_min)
                   # For y start and end
                gfa_y_start_list = [abs(stage_y-y_edge) for y_edge in gfa_y_edges]
                gfa_y_start_min = min(gfa_y_start_list)
                y_gfa = gfa_y_start_list.index(gfa_y_start_min)
                
                #Apply manual shift 
                #TODO: create the ability for individual filenames to be shifted by specific amounts.
                if len(shift_dict) >0:
                    pass
                else:
                    x_shift = x_shift + global_manual_shift['manual_x_shift'] 
                    y_shift = y_shift + global_manual_shift['manual_y_shift'] 
                        
                #Assign homography shift to raw spatially-assigned pixel location
                x_gfa = int(x_gfa + x_shift)
                y_gfa = int(y_gfa + y_shift)
                
                print("x-shift by assignment: ", x_shift)
                print("y-shift by assignment: ", y_shift)
                
                #Update metadict with info about this image
                if update_metadict:
                    pic_dict = {
                        meta_key_name: {
                            'stitch_x0_idx': x_gfa,
                            'stitch_y0_idx': y_gfa,
                            }
                        }
                    _,_ = Meta.meta_index_lookup(filename, update_dict=pic_dict)

                if overright_GFA:
                    this_entry = np_img[::, ::, 0]
                else:
                    this_entry = GFA[y_gfa : y_gfa + np_img.shape[0], 
                                     x_gfa : x_gfa + np_img.shape[1]] + np_img[::, ::, 0]
                try:
                    GFA[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] = this_entry
                    gfa_count[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] += 1
                
                # Flagged if indices fail
                except IndexError:
                    #get array clash difference (amount of padding needed)
                      #if 'IndexError' was raised, either 'y_gfa' or 'x_gfa' must be bigger than that index of GFA
                    pad_size = int(max([
                        (y_gfa + np_img.shape[0]) - (GFA.shape[0]-1),
                        (x_gfa+np_img.shape[1]) - (GFA.shape[1]-1)
                        ]))
                    
                    #pad the GFA and try appending again
                    GFA = np.pad(GFA, pad_size)
                    gfa_count = np.pad(gfa_count, pad_size)
                    
                    GFA[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] = this_entry
                    gfa_count[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] += 1
                    
                #Flagged if array can't be cast into GFA
                #   Identical to error solution above; may leverage different solutions in the future so 
                #     keeping errors split for that reason now.
                except ValueError:
                    #get array clash difference (amount of padding needed)
                      #if 'IndexError' was raised, either 'y_gfa' or 'x_gfa' must be bigger than that index of GFA
                    pad_size = int(max([
                        (y_gfa + np_img.shape[0]) - (GFA.shape[0]-1),
                        (x_gfa+np_img.shape[1]) - (GFA.shape[1]-1)
                        ]))
                    
                    #pad the GFA and try appending again
                    GFA = np.pad(GFA, pad_size)
                    gfa_count = np.pad(gfa_count, pad_size)
                    
                    GFA[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] = this_entry
                    gfa_count[y_gfa : y_gfa + np_img.shape[0], 
                        x_gfa : x_gfa + np_img.shape[1]] += 1
            
            #Append locations to annotation list for plotting on annotation figure
            xy_loc_list.append( (x_gfa, y_gfa) )
            
            #Update dict
            GFA_dict['file_summary'].update (
                {filename: {
                    'stage_x': img_dict['StageX'],
                    'stage_y': img_dict['StageY'],
                    'GFA_x_start': x_gfa,
                    'GFA_y_start': y_gfa,
                    'x_shift': x_shift,
                    'y_shift': y_shift,
                    'x_residual_sum': x_residual_sum,
                    'y_residual_sum': y_residual_sum
                    }
                    }
                )
        
        # Initialize the figure below
        if overright_GFA:
            gfa_count = np.ones((GFA.shape[0], GFA.shape[1]))
        fig, ax = plt.subplots()
        plt.figure(figsize=(20,17))
        plt.title(f"{filename} Stitched Image")        
        if show_final_GFA:
            ax.imshow(GFA)
    
        # Create annotations for GFA location
        for idx, (x, y) in enumerate(xy_loc_list):
            ax.text(x, y, str(idx), va='top', ha='left', color = 'w')
    
        # Create a useful filename for the GFA and save it to the same folder the images were pulled from
        folder_name = os.path.basename(os.path.dirname(filenames[0]))
        folder_path = os.path.dirname(os.path.dirname(filenames[0]))
        this_datetime = datetime.datetime.now()
        if jeol_data:        
            detector_name ='UNK'
            for part in os.path.basename(filenames[0]).split('_'):
                print(part)
                if 'BED' in part:
                    detector_name = part
                if 'SED' in part:
                    detector_name = part
            file_name = folder_name+ f"_{detector_name}"+'_DumbStitch_' + '_'+str(this_datetime).\
                split('.')[0].replace(":",'.')
        else:
            file_name = folder_name+'_DumbStitch_' + '_'+str(this_datetime).split('.')[0].replace(":",'.')
        gfa_filename = os.path.join(folder_path, file_name+".png")
        print("Saving file in location: ")
        print(gfa_filename)
        print()

        #Save the annotated version
        annot_filename = os.path.join(folder_path, 'Annotated_'+file_name+".png")
        if save_final_annotated:
            fig.savefig(annot_filename)
        if len(save_alternate_location)>0 and save_final_annotated:
            try:
                annot_filename = os.path.join(save_alternate_location, 'Annotated_'+file_name+".png")
                fig.savefig(annot_filename)
            except:
                pass
        plt.title(f"{filename} Stitched Image")
        if show_final_annotated:
            plt.show()
        
        #Save file data dict as a json in same folder with images
        json_filepath = os.path.join(folder_path, file_name+".json")
        with open(json_filepath, 'w') as file:
            json.dump(GFA_dict, file, indent=4)
    
        #Save the array
        with open(gfa_filename, 'wb') as name:
            # This is primarily for summed bluring and other effects
            #np.save(name, np.divide(GFA, gfa_count))
            # This just saves the raw array
            np.save(name, GFA, gfa_count)
    
        #   Save the image of the array
        #gfa_image = PIL.Image.fromarray(np.divide(GFA, gfa_count))
        gfa_image = PIL.Image.fromarray(GFA)
        gfa_image = gfa_image.convert("L")
        if save_final_GFA:
            gfa_image.save(gfa_filename, format= "PNG")
        
        if len(save_alternate_location)>0:
            try:
                alt_location = os.path.join(save_alternate_location, file_name+".png")
                gfa_image.save(alt_location, format= "PNG")
            except:
                print('Alternate save location fail:')
                print("\t {save_alternate_location}")

        return GFA
    
    
    @staticmethod
    def img_GFA_area_finder(img1_filename, gfa_x_edges, gfa_y_edges, GFA, x_shift, y_shift, \
                           window_size = 100, slide_overlap = 0, show_max_inset= False):
        
        '''v1.1  modified 2024-01-11
        INPUT:    Image filename to open
                  A list of X and a list of Y spatial edges for alignment array (GFA)
                  The GFA itself
        ACTION:   Open the image to be compared and pull its metadata
                  Find the portion of the GFA it should theoretically apply to based on metadata
                  Slide a window around both the image and the GFA selection to pick a region with useful data            
        OUTPUT:   GFA x_start, y_start indices based on the 'window_size'
        '''
        
        # Open the images and pull the metadata
        im1 = SEM.open_without_databar(img1_filename)
        im1_dict = SEM.tiff_tag_getter(img1_filename)
           # Convert images to grayscale (if not already)
        #im1Gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
        
          # Check if the images are probably taken from JEOL SEM
        if '_X0' in img1_filename and '_Y0' in img1_filename:
            jeol_data = True
        else:
            jeol_data = False
    
        # Get img x and y spatial location and relate to GFA indices
        if jeol_data:
            x_start = im1_dict['StageX']
            x_end = x_start - (im1_dict['PixelWidth']*im1_dict['ImageWidth'])
            y_start = im1_dict['StageY']
            y_end = y_start + (im1_dict['PixelHeight']*im1_dict['ImageHeight']-\
                               (im1_dict['DatabarHeight']*im1_dict['PixelHeight']))
        else:
            x_start = im1_dict['StageX']
            x_end = x_start + (im1_dict['PixelWidth']*im1_dict['ImageWidth'])
            y_start = im1_dict['StageY']
            y_end = y_start - (im1_dict['PixelHeight']*im1_dict['ImageHeight']-\
                               (im1_dict['DatabarHeight']*im1_dict['PixelHeight']))
        y_dim, x_dim, _ = im1.shape
    
        # Pull the GFA indices to compare against image
           # For x start and end
        gfa_x_start_list = [abs(x_start-x_edge) for x_edge in gfa_x_edges]
        gfa_x_start_min = min(gfa_x_start_list)
        gfa_x_start_index = gfa_x_start_list.index(gfa_x_start_min) + x_shift
        gfa_x_end_list = [abs(x_end-x_edge) for x_edge in gfa_x_edges]
        gfa_x_end_min = min(gfa_x_end_list)
        gfa_x_end_index = gfa_x_end_list.index(gfa_x_end_min) + x_shift
           # For y start and end
        gfa_y_start_list = [abs(y_start-y_edge) for y_edge in gfa_y_edges]
        gfa_y_start_min = min(gfa_y_start_list)
        gfa_y_start_index = gfa_y_start_list.index(gfa_y_start_min) + y_shift
        gfa_y_end_list = [abs(y_end-y_edge) for y_edge in gfa_y_edges]
        gfa_y_end_min = min(gfa_y_end_list)
        gfa_y_end_index = gfa_y_end_list.index(gfa_y_end_min) + y_shift
    
        # In case the indices aren't in order, make a list and take the max() and min()
        gfa_x_list = [int(gfa_x_start_index), int(gfa_x_end_index)]
        gfa_y_list = [int(gfa_y_start_index), int(gfa_y_end_index)]
        try:
            gfa_inset = GFA[min(gfa_y_list):max(gfa_y_list), min(gfa_x_list):max(gfa_x_list)].astype(np.uint8)
        except TypeError:
            print("GFA Y's: ", gfa_y_list)
            print("GFA X's: ", gfa_x_list)
        gfa_x_size = gfa_inset.shape[1]
        gfa_y_size = gfa_inset.shape[0]
    
        # Make a list of start indices, open a window starting at those indices
        x_indices = []
        y_indices = []
        x = 0
        y = 0
        while x <= (gfa_x_size-window_size):
            x_indices.append(x)
            x = x+(window_size-slide_overlap)
    
        while y <= (gfa_y_size-window_size):
            y_indices.append(y)
            y = y +(window_size-slide_overlap)
        # Translate effective indices to actual GFA indices by adding start indices from above
        x_indices = [min(gfa_x_list)+x for x in x_indices]
        y_indices = [min(gfa_y_list)+y for y in y_indices]
    
        # Generate a max_x and max_y index for highest-entropy windows
        min_entropy = 100
        test = []
        for x_idx in x_indices:
            for y_idx in y_indices:
                this_gfa_inset = GFA[y_idx:y_idx+window_size, x_idx:x_idx+window_size]
                n_counts, bins = np.histogram(this_gfa_inset, bins=252)
                count_sum = np.sum(n_counts)
                hist_p = np.nan_to_num(np.divide(n_counts, count_sum), nan=0)
                hist_ln_p = np.nan_to_num(np.log(n_counts), nan=0)
                this_ent = np.nansum(np.multiply(hist_p, hist_ln_p))
                test.append(this_ent)
                if this_ent < min_entropy:
                    min_entropy = this_ent
                    max_x_idx = int(x_idx)
                    max_y_idx = int(y_idx)
                    #print('New minimum: ', this_ent)
                    #plt.imshow(this_gfa_inset)
                    #plt.show()
    
        #Calculate the rough region of overlap for the img
        if jeol_data:
            img_x_list = []
            for x_idx in range(x_dim):
                img_x_list.append(x_start - im1_dict['PixelWidth']*x_idx)
            img_y_list = []
            for y_idx in range(y_dim):
                img_y_list.append(y_start + im1_dict['PixelHeight']*y_idx)
        else:
            img_x_list = []
            for x_idx in range(x_dim):
                img_x_list.append(x_start + im1_dict['PixelWidth']*x_idx)
            img_y_list = []
            for y_idx in range(y_dim):
                img_y_list.append(y_start - im1_dict['PixelHeight']*y_idx)
    
        spatial_gfa_x_start = gfa_x_edges[max_x_idx]
        img_x_diff_list = [abs(x-spatial_gfa_x_start) for x in img_x_list]
        img_x_min = min(img_x_diff_list)
        img_x_inset_start = int(img_x_diff_list.index(img_x_min) - x_shift)
        if img_x_inset_start<0:
            offset = img_x_inset_start
            img_x_inset_start = 0
            max_x_idx = max_x_idx + offset
        if img_x_inset_start+window_size>(x_dim-1):
            offset = img_x_inset_start+window_size-x_dim
            img_x_inset_start = img_x_inset_start-offset
            max_x_idx = max_x_idx - offset
    
        spatial_gfa_y_start = gfa_y_edges[max_y_idx]
        img_y_diff_list = [abs(y-spatial_gfa_y_start) for y in img_y_list]
        img_y_min = min(img_y_diff_list)
        img_y_inset_start = int(img_y_diff_list.index(img_y_min) - y_shift)
        if img_y_inset_start < 0:
            offset = img_y_inset_start
            img_y_inset_start = 0
            max_y_idx = max_y_idx + offset
        if img_y_inset_start+window_size>(y_dim-1):
            offset = img_y_inset_start+window_size-y_dim
            img_y_inset_start = img_y_inset_start-offset
            max_y_idx = max_y_idx - offset
    
        return img_x_inset_start, img_y_inset_start, max_x_idx, max_y_idx
    
    
    @staticmethod
    def guess_and_check(x_shift, y_shift, GFA, ):
        ''' v0.1   created:2024-11-03   modified:2024-11-03
        Pulled out from SEM.homography_stitch() as a separate function because it was getting huge.
        TODO: Code below needs to be completetly revamped as a function; currently just dropped here from SEM.homography_stitch().
        '''
        
        # If all else fails, use the last shifts calculated to get something reasonable
        crazy_shift = False
        if y_shift==0 and x_shift==0 and residual_error==0:
            #x_shift = np.median(np.array(x_shift_list[-10:]))
            #y_shift = np.median(np.array(y_shift_list[-10:]))
            crazy_shift = True
        if abs(x_shift)> 100:
            #x_shift = np.median(np.array(x_shift_list[-10:]))
            crazy_shift = True
        if abs(y_shift>70):
            #y_shift = np.median(np.array(y_shift_list[-10:]))
            crazy_shift = True

        # Even if the shifts aren't zero they may be bad fits. Catch bad fits and do guess-and-check to get improve alignment.
        if (abs(residual_error)/(match_count+1))>2 or crazy_shift:
            window_n = 75
            overlap_n = 50
            guess_window = 100
            guess_step = 5
            #Rough pass for guess-and check
            img_x_start, img_y_start, inset_x_start, inset_y_start = SEM.img_GFA_area_finder(filename, \
                                                                                         gfa_x_edges, \
                                                                                         gfa_y_edges, GFA, \
                                                                                         x_shift, y_shift, \
                                                                                         window_size = window_n, \
                                                                                         slide_overlap = overlap_n, \
                                                                                         show_max_inset= False)
            # Calculate original difference to compare against
            guess_GFA = GFA.copy()
            guess_GFA = np.nan_to_num(np.divide(guess_GFA, gfa_count), nan= 0)
            original_diff = np.subtract(np_img[int(img_y_start):(int(img_y_start)+window_n), \
                                                   int(img_x_start):(int(img_x_start)+window_n), 0],\
                                           guess_GFA[int(inset_y_start):(int(inset_y_start)+window_n), \
                                                   int(inset_x_start):(int(inset_x_start)+window_n)])
            original_sum = np.sum(np.absolute(original_diff))
            print("Original sum: ", round(original_sum, 5))
            running_min = original_sum

            # Calculate the original entropy
            n_counts, bins = np.histogram(np.absolute(original_diff), bins=252)
            count_sum = np.sum(n_counts)
            hist_p = np.nan_to_num(np.divide(n_counts, count_sum), nan=0)
            hist_ln_p = np.nan_to_num(np.log(n_counts), nan=0)
            original_ent = np.nansum(np.multiply(hist_p, hist_ln_p))
            min_ent = original_ent

            if show_guess_checking:
                # Show the original fit
                fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharex=True, sharey=True)
                ax = axes.ravel()
                ax[0].set_title(' Original GFA Inset')
                ax[0].imshow(guess_GFA[inset_y_start:inset_y_start+window_n, \
                                 inset_x_start:inset_x_start+window_n])
                ax[1].set_title('Original Image Inset')
                ax[1].imshow(np_img[img_y_start:img_y_start+window_n, \
                                 img_x_start:img_x_start+window_n])
                plt.tight_layout()
                plt.show()

            # Calculate window extreme indices to step within
            window_x_start = inset_x_start - round(guess_window/2)
            window_x_end = inset_x_start + window_n + round(guess_window/2)
            window_y_start = inset_y_start - round(guess_window/2)
            window_y_end = inset_y_start + window_n + round(guess_window/2)

            # Try different fits
            guess_dif_list = []
            guess_pairs = []
            ent_list = []
            #Build up the list of differences
            for x_step in range(guess_window):
                x_start = window_x_start + x_step
                x_end = window_x_end - (guess_window - x_step)
                for y_step in range(guess_window):
                    y_start = window_y_start + y_step
                    y_end = window_y_end +(guess_window - y_step)
                    this_diff = np.subtract(np_img[(img_y_start):(img_y_start+window_n), \
                                                   img_x_start:(img_x_start+window_n), 0], \
                                            guess_GFA[y_start:y_end, x_start:x_end])
                    this_sum = np.sum(np.absolute(this_diff))
                    n_counts, bins = np.histogram(this_diff, bins=252)
                    count_sum = np.sum(n_counts)
                    hist_p = np.nan_to_num(np.divide(n_counts, count_sum), nan=0)
                    hist_ln_p = np.nan_to_num(np.log(n_counts), nan=0)
                    this_ent = np.nansum(np.multiply(hist_p, hist_ln_p))
                    ent_list.append(this_ent)
                    guess_dif_list.append(this_sum)
                    guess_pairs.append( (x_step, y_step) )

                    if this_ent > min_ent:
                        min_ent = this_ent

            diff_ents = [original_ent-ent for ent in ent_list]
            d_ents = [0]
            for idx in range(len(diff_ents)-1):
                if idx>0:
                    d_ents.append(diff_ents[idx]-diff_ents[idx+1])
            diff_max = max(d_ents)
            sum_diff = [dif-original_sum for dif in guess_dif_list]
            sum_max = max(sum_diff)
            diff_ents = [round(ent/diff_max, 5) for ent in diff_ents]
            ent_sum = [abs(diff_ents[0]-diff_ents[1])]
            sum_diff = [round(dif/sum_max, 5) for dif in guess_dif_list]
            #joined_score =[dif+ent for dif, ent in zip(sum_diff, diff_ents)]
            joined_score =[dif for dif, ent in zip(sum_diff, diff_ents)]
            sort_score = joined_score.copy()
            sort_score.sort()

            guess_image = np.empty(shape=(guess_window, guess_window))
            guess_image.fill(0)
            sum_min = min(sum_diff)-0.001 # subtract a bit to keep math.log domain happy
            for idx,pair in enumerate(guess_pairs):
                this_sum = math.log10(sum_diff[idx]-sum_min)
                guess_image[pair[1], pair[0]] = this_sum

            ent_steps = round((len(sum_diff)-50)//10)
            sum_ent_list = []
            middles = []
            for idx in range(ent_steps):
                start = 0 + 10*idx
                end = 50 + 10*idx
                middles.append(end-25)
                this_array = np.array(sum_diff[start:end])
                n_counts, bins = np.histogram(this_array, bins=50)
                count_sum = np.sum(n_counts)
                hist_p = np.nan_to_num(np.divide(n_counts, count_sum), nan=0)
                hist_ln_p = np.nan_to_num(np.log(n_counts), nan=0)
                this_ent = np.nansum(np.multiply(hist_p, hist_ln_p))
                sum_ent_list.append(this_ent)

            if show_guess_checking:               
                plt.figure(figsize=(30,10))
                plt.scatter(range(len(diff_ents)), diff_ents, color = 'lightslategray')
                plt.plot(diff_ents, color='lightsteelblue', alpha=0.5)
                plt.show()
                plt.figure(figsize=(30,10))
                plt.scatter(range(len(joined_score)), joined_score)
                plt.plot(joined_score)
                plt.show()
                plt.figure(figsize=(30,30))
                plt.imshow(guess_image)
                plt.show()
                #print('_______________________________________________________________________')
                #print("The following are best fit results: ")
                #print()
                #for idx in range(5):
                #    this_pair = guess_pairs[joined_score.index(sort_score[idx])]
                #    print("Y,X shift proposed: ", (this_pair[1] - round(guess_window/2)), ', ', (this_pair[0] - round(guess_window/2)))
                #    print("Score: ", u'\t', sort_score[idx])
                #    print()
                #print('_______________________________________________________________________')


            # Get a trendline for the minimum values and find the global minima
               # Calculate how many steps it will take to span the entire set
            step_number = len(sum_diff)//(guess_window-5)
            min_list = []
            x_list = []
            for step in range(step_number):
                # Subtract stagger offset for first iteration
                if step ==0:
                    offset = 0
                else:
                    offset = 5
                start_index = 0 + (guess_window*step)- offset
                end_index = start_index + guess_window
                # Find minimum in window and pull 'X' value to get a trendline
                if end_index < len(sum_diff):
                    this_min = min(sum_diff[start_index:end_index])
                    min_list.append(this_min)
                    this_x = sum_diff.index(this_min)
                    x_list.append(this_x)  
                # Number of step calculation is wrong, and this is the lazy way of fixing it
                else:
                    pass

               # Re-factor the data
            x_array = np.array(x_list).reshape((-1,1))
            min_diffs = [0]
            for idx in range(len(min_list)-1):
                if idx>0:
                    min_diffs.append(min_list[idx]-min_list[idx+1])
            min_diffs.append(0)
            min_array = np.array(min_list)

               # Do a linear regression
            model = LinearRegression()
            model.fit(x_array, min_array)
            r_squared = model.score(x_array, min_array)
            min_predict = model.predict(x_array)

               # Calculate the differences between the trendline predictions and the actual minima
            min_diffs = [minimum - min_pred for minimum, min_pred in zip(min_list, min_predict)]
            sorted_min_diffs = sorted(min_diffs.copy())
               # Store the index for graphing, and for finding the X-Y coordinates 'guess_pairs' later
               #   'guess_pairs' and 'sum_diff' are the same size and indices are shared (i.e. (X,Y) == 'sum')
            min_indices = []
            graph_min_indices = []
            for idx in range(3):
                this_min_index = min_diffs.index(sorted_min_diffs[idx])
                graph_min_indices.append(this_min_index)
                this_min = min_list[this_min_index]
                this_index = sum_diff.index(this_min)
                min_indices.append(this_index)

               # Use those indices to get the X-Y step from 'guess_pairs'
            xs = []
            ys = []
            for idx in range(3):
                this_x, this_y = guess_pairs[min_indices[idx]]
                print("Minima at ", this_y, ' Y, ', this_x, " X")
                xs.append(this_x)
                ys.append(this_y)
            if show_guess_checking:
                plt.figure(figsize=(10,7))
                plt.scatter(xs, ys)
                plt.show()

               # Show the minimum sums and fit
            plt.figure(figsize=(30,10))
            plt.scatter(range(len(x_list)), min_diffs, s=100)
            plt.plot(min_predict, color='r')
            plt.scatter(range(len(x_list)), min_predict, color = 'r')  
            plt.axvline(graph_min_indices[0], color = 'b', linewidth= 10, alpha= 0.5)
            plt.axvline(graph_min_indices[1], color = 'b', linewidth= 5, alpha= 0.5)
            plt.axvline(graph_min_indices[2], color = 'b', linewidth= 2, alpha= 0.5)
            plt.show()

            eu_dist_array = np.array([])
            for x, y in zip(xs, ys):
                eu_dist_array = np.append(eu_dist_array, math.sqrt(x**2 + y**2))

            # Run through every pair and add a summed weight that scales inversely with distance between points
            weighted_sum = np.zeros(len(eu_dist_array))
            for pt_idx, point in enumerate(eu_dist_array):
                   #Add -1 to avoid 0 div error and peg all values to unity
                this_weight = np.absolute(np.subtract(eu_dist_array, point-1))
                   #Keep in mind that 'this_weight' is actually a distance until the step below
                weighted_sum = np.nan_to_num(np.add(weighted_sum, np.divide(1, this_weight**2)), \
                                             nan = 0.0000001, posinf = 0.0000001, neginf = 0.0000001)

            weighted_x_list = []
            weighted_y_list = []
            for weight, pair in zip(weighted_sum,zip(xs,ys)):
                x = round(pair[0], 1)
                weighted_x_list.append(weight * x)
                y = round(pair[1], 1)
                weighted_y_list.append(weight * y)

            if len(weighted_sum)>0:
                weighted_x = sum(weighted_x_list)/sum(weighted_sum)
                weighted_y = sum(weighted_y_list)/sum(weighted_sum)
                x_diff = round(weighted_x)- round(guess_window/2)
                y_diff = round(weighted_y)- round(guess_window/2)
            else:
                weighted_x = round(guess_window/2)
                weighted_y = round(guess_window/2)
                x_diff = 0
                y_diff = 0

            x_error = round(sum([abs(weighted_x-x) for x in xs]), 1)
            y_error = round(sum([abs(weighted_y-y) for y in ys]), 1)


            print("Best guess for X difference: ", x_diff)
            print(u'\t', x_error)
            print("Best guess for Y difference: ", y_diff)
            print(u'\t', y_error)
            if show_guess_checking:

                fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharex=True, sharey=True)
                ax = axes.ravel()
                ax[0].set_title('GFA Inset')
                ax[0].imshow(guess_GFA[inset_y_start+y_diff:inset_y_start+y_diff+window_n, \
                                 inset_x_start+x_diff:inset_x_start+x_diff+window_n])
                ax[1].set_title('Image Inset')
                ax[1].imshow(np_img[img_y_start:img_y_start+window_n, \
                             img_x_start:img_x_start+window_n])
                plt.tight_layout()
                plt.show()



            if user_input:
                print("Proposed extra shift of ", y_diff, ' Y, ', x_diff,' X?')
                print("Does this fit look better (yes/no/manual)?")
                user_test = input().lower().strip()
                if user_test == 'yes' or user_test=='y':
                    x_shift = x_shift + x_diff
                    y_shift = y_shift + y_diff
                    print("Guess-and-Check shifted (x,y) by: ", x_diff, ', ', \
                          y_diff)
                    print(user_test)
                elif user_test == 'no' or user_test == 'n':
                    print("Ignoring Guess-and-Check.")
                elif user_test == 'manual' or user_test == 'man':
                    print("Manual x-shift(integer)?")
                    x_manual_shift = int(input())
                    print("Manual y-shift(integer)?")
                    y_manual_shift = int(input())
                    x_shift = x_shift + x_manual_shift
                    y_shift = y_shift + y_manual_shift
            else:
                x_shift = x_shift + x_diff
                y_shift = y_shift + y_diff
                print("Guess-and-Check shifted (x,y) by: ", x_diff, ', ', \
                      y_diff)
    

####################################################################################################################################################
####################################################################################################################################################
    

class Stich:
    ''' v0.1.0   created:2024-10-21   modified:2024-10-28
    Wrapper class for stitching homogenous (same pixel size) data into a new array.
    '''
    
    version = '0.1.0'
    version_mod_date = '2024-10-18'
    
    blank_stitch_dict = {
        'filenames_list': [],
        'file_properties':{},
        'array_size': (5000, 5000),
        'array_middle': (2500, 2500),
        'hit_list': [],
        'data_type': ''
        }
    
    ##################################################################################################
    ###    Object functions     ######################################################################
    ##################################################################################################
    
    def __intit__(self, filenames = [], existing_montage_array = np.array([]), stitch_dict = {}):
        ''' v0.1.0   created:2024-10-26   modified:2024-10-26
        '''
        
        #assign 'blank' if no stitch settings dictionary is passed in
        if len(stitch_dict) <1:
            stitch_dict = self.blank_stitch_dict
            self.stitch_dict = stitch_dict
        
        #Define filenames
          #try and pull data from dict and default to 'blank'
        try:
            filenames = stitch_dict['filenames_list']
        except:
            filenames = []
          #if there aren't any filenames, 
        if len(filenames) < 1:
            root = Tk()
            filenames = filedialog.askopenfilenames(title = "Select files to stitch together.")
            root.destroy()
        self.stitch_dict['filenames_list'] = filenames
        
        #Guess at what kind of stitching is being asked for
          #take the first filename and 
            
        #get summary parameters from set of filenames
        #summary_dict = 
            
        #
            
            
        if existing_montage_array.shape[0] < 1:
            montage_array = np.array(stitch_dict['array_size'])
        else:
            montage_array = existing_montage_array
            
            
    def add_files(self):
        ''' v0.1.0   created:2024-10-26   modified:2024-10-26
        '''
        
        #Populate filenames
        root = Tk()
        filenames = filedialog.askopenfilenames(title = "Select files to stitch together.")
        root.destroy()
        
        self.stitch_dict['filenames_list'] = filenames
        
        #Populate object data
         
         

    ##################################################################################################
    ###    Utility functions     #####################################################################
    ##################################################################################################
    
    #TODO: transition this to TypeHash in the future
    @staticmethod
    def guess_stitch_type(filenames_list):
        #Check filetypes and (potentially) metadata
        type_guesses = []
        for filename in filenames_list:
            end_check = filename.split('.')[-1]
            if end_check not in type_guesses:
                type_guesses.append(end_check)
        if len(type_guesses) == 1:
            filetype = type_guesses[0].lower()
        elif len(type_guesses) == 0:
            print()
            print("Unkown filetype:")
            print(f"\t example:{os.path.basename(filenames_list[0])}")
            filetype = 'unk'
        else:
            print()
            print("More than 1 filetype:")
            print(f"\t types:{tyep_guesses}")
            filetype = 'unk'
        
        type_dict = {
            'type_list':type_guesses,
            'type':filetype,
            }
            
        return type_dict
            
        
    @staticmethod
    def get_summary(filenames_list, stitch_dict={}, type_dict={}):
        
        #Pull some data for determining how summary gets made
        if len(stitch_dict) <1:
            stitch_dict = self.blank_stitch_dict
        
        if len(type_dict) <1:
            type_dict = Stitch.guess_stitch_type(filenames_list)
        
        try:
            filetype = type_dict['type']
        except:
            filetype = 'unk'
            
        #TODO: replace this with something from Recipes and TypeHash
        #Pull running instructions from SEM class
        if filetype == 'tif' or (filetype == 'tiff'):
            #Assume this is for SEM
            if ('_X0' in filenames[0]) and ('_Y0' in filenames[0]):
                pass
        
    
        @staticmethod
        def transform(ind_image, stitched_image):
            ''' v0.1.0   created:2024-10-18   modified:2024-10-18
            INPUT:   lorem
            ACTION:  lorem
            OUTPUT:  lorem 
                '''
    
    
class Defects:
    ''' v0.4.2   created:2024-10-18   modified:2025-05-05
    Object class for handling defect identification, blobbing, and counting. 
    '''
    #
    blank_finergprint_names = []
    
    #O x N set of defect types; O= number of types, N= dimension of fingerprint functions
    defect_type_dict = {
        
        }
    
    global_summary_dict_blank = {
        'all_filenames':[],
        'samples':[],
        'sample_filenames':{
            },
        'global_grayscale_histogram':{
            'bins':np.array(256),
            'cnts':np.zeros(256),},
        'global_grayscale_probs':{
            'bins':np.array(256),
            'cnts':np.zeros(256),},
        }

    #Average pixel probabilities from a training set (n=13) of blisters
    # CorrosionShare\Aaron\Blister Training Set\Cropped blisters
    # Processed 2025-04-22, n=13
    blister_avg_prob = np.array([
           2.97932359e-01, 6.35865861e-03, 2.37825716e-03, 3.91643013e-03,
           2.07476827e-03, 4.13995530e-03, 2.25049284e-03, 2.14718928e-03,
           2.21204381e-03, 2.03968436e-03, 2.12293884e-03, 2.16551416e-03,
           2.06058460e-03, 1.99718079e-03, 4.08692136e-03, 2.20958183e-03,
           2.03277778e-03, 2.17472905e-03, 2.18068944e-03, 2.28500338e-03,
           2.62154953e-04, 2.19926636e-03, 2.11385894e-03, 2.49760593e-04,
           2.24346498e-03, 4.05557961e-03, 2.10677150e-03, 2.39141520e-04,
           4.11991513e-03, 2.15941091e-03, 1.87990242e-04, 4.25020364e-03,
           2.38827599e-03, 2.01337621e-04, 4.24034345e-03, 2.10257642e-04,
           0.00000000e+00, 2.24616109e-03, 2.39930530e-03, 2.28984872e-03,
           2.25690187e-03, 2.36479190e-03, 2.11462683e-03, 2.28353391e-03,
           2.36526028e-03, 2.45368394e-03, 2.38681024e-03, 2.43381254e-03,
           2.44093426e-03, 2.60352561e-03, 2.41390253e-03, 2.14385452e-04,
           2.56138071e-03, 4.90215797e-03, 1.89732877e-04, 2.64611359e-03,
           2.62659020e-03, 2.61595228e-03, 2.49655496e-03, 2.77794726e-03,
           2.77926296e-03, 2.53386851e-03, 2.70604620e-03, 2.93726818e-03,
           2.66993951e-03, 2.76214513e-03, 2.87070017e-03, 2.92455006e-03,
           2.85155793e-03, 2.69608052e-03, 2.70403391e-03, 5.40627610e-03,
           2.00912858e-04, 0.00000000e+00, 2.84701599e-03, 5.85723097e-03,
           2.15431033e-04, 2.80841191e-03, 3.14120791e-03, 3.12864083e-03,
           2.92876348e-03, 2.99688384e-03, 2.95569917e-03, 3.19877810e-03,
           5.86903845e-03, 1.97531081e-04, 3.05626638e-03, 5.98850087e-03,
           1.82315852e-04, 2.81633736e-03, 3.35588438e-03, 3.23569346e-03,
           6.36993331e-03, 1.84151049e-04, 3.28114612e-03, 2.87576992e-03,
           3.25852790e-03, 3.14314536e-03, 3.40812645e-03, 3.19517279e-03,
           6.44166089e-03, 3.45815670e-03, 3.47426791e-03, 1.84379757e-04,
           3.32736979e-03, 3.53073445e-03, 3.37078368e-03, 3.42442846e-03,
           3.35036684e-03, 0.00000000e+00, 3.28108508e-03, 3.62812829e-03,
           3.30806918e-03, 3.37062865e-03, 3.53851270e-03, 3.26585113e-03,
           3.35633273e-03, 3.64430531e-03, 3.71532106e-03, 3.18606013e-03,
           1.86868425e-04, 3.28747005e-03, 3.55444695e-03, 3.31101298e-03,
           3.49545926e-03, 6.47264636e-03, 3.50338728e-03, 1.80208364e-04,
           3.59713193e-03, 6.54526792e-03, 3.52729011e-03, 3.45975811e-03,
           3.14659322e-03, 3.47053118e-03, 3.22711819e-03, 3.29175541e-03,
           2.04359940e-04, 6.70058884e-03, 1.98789043e-04, 3.65939791e-03,
           3.49640395e-03, 3.28537159e-03, 6.62788190e-03, 3.22049832e-03,
           3.29392214e-03, 3.09243017e-03, 0.00000000e+00, 3.72544771e-03,
           3.65075988e-03, 3.45187945e-03, 6.47284626e-03, 3.25450335e-03,
           2.43939127e-04, 3.36958591e-03, 6.37512440e-03, 3.17689567e-03,
           2.51083860e-04, 6.01633565e-03, 3.28035432e-03, 3.08809159e-03,
           3.14153464e-03, 3.14036934e-03, 3.33062871e-03, 3.27411881e-03,
           3.14303977e-03, 3.05334555e-03, 3.22286922e-03, 2.87613471e-04,
           2.95209035e-03, 3.12111279e-03, 2.82609530e-03, 3.05267893e-03,
           3.17808391e-03, 3.12630136e-03, 3.31072075e-03, 2.92187528e-03,
           3.12636084e-03, 3.08270156e-03, 3.07503629e-03, 5.43572518e-03,
           2.98613668e-03, 3.02390096e-03, 0.00000000e+00, 3.44885623e-04,
           5.24665194e-03, 2.91297470e-03, 2.69031541e-03, 2.67752690e-03,
           2.56308134e-03, 2.80465829e-03, 2.82167982e-03, 2.89849111e-03,
           2.77008324e-03, 2.74186240e-03, 2.47547092e-03, 2.94650977e-03,
           2.52491226e-03, 2.49235882e-03, 2.67100035e-03, 2.46987334e-03,
           2.37618520e-03, 2.23746016e-03, 2.35677622e-03, 2.35957128e-03,
           2.49972843e-03, 2.25012618e-03, 2.37727213e-03, 2.29547080e-03,
           3.37637397e-04, 2.25569806e-03, 4.33614041e-03, 2.17753702e-03,
           2.23466617e-03, 1.92168664e-03, 2.74794348e-04, 2.19879844e-03,
           3.84742225e-03, 2.56812624e-04, 1.92657691e-03, 0.00000000e+00,
           1.94834683e-03, 1.94841495e-03, 2.04726306e-03, 2.52053206e-04,
           1.78568305e-03, 3.47220332e-03, 1.81463212e-03, 1.78824930e-03,
           1.72237462e-03, 2.23615812e-04, 1.76282152e-03, 1.73256941e-03,
           1.66600841e-03, 1.66576627e-03, 2.30014372e-04, 2.86698320e-03,
           1.57919237e-03, 1.53530044e-03, 2.55336744e-04, 1.89180693e-03,
           2.79085899e-03, 2.61381523e-04, 1.55194197e-03, 1.56237309e-03,
           2.29077820e-04, 1.37971752e-03, 2.35171624e-03, 1.47099598e-03,
           1.37010812e-03, 1.29383508e-03, 2.29110212e-03, 1.24134123e-04,
           1.18930289e-03, 2.26995388e-03, 1.25920342e-04, 4.32983753e-02])
    
    #Average pixel probabilities from a training set (n=10) of non-blister metal
    #NOTE: includes small defects, but large defects (~5um or bigger in diameter) were cropped
    # CorrosionShare\Aaron\Blister Training Set\Cropped metal
    # Processed 2025-04-28, n=10
    metal_avg_prob = np.array([
           4.59121130e-03, 1.34210194e-04, 5.00629097e-05, 9.88657019e-05,
           5.45634719e-05, 1.17889142e-04, 2.74440696e-04, 6.41152730e-05,
           6.85279462e-05, 8.16242900e-05, 7.49546700e-05, 7.82382437e-05,
           8.37710108e-05, 8.75063150e-05, 1.88769382e-04, 9.35580336e-05,
           9.87575081e-05, 1.07039763e-04, 1.13085601e-04, 1.18462585e-04,
           2.61834939e-06, 1.22239888e-04, 1.27720493e-04, 2.61834939e-06,
           1.42358900e-04, 2.93664290e-04, 1.67811326e-04, 8.72783131e-07,
           3.59159778e-04, 1.84989857e-04, 3.49113252e-06, 4.04492601e-04,
           2.19460895e-04, 0.00000000e+00, 4.93669231e-04, 4.36391565e-06,
           0.00000000e+00, 2.66489548e-04, 2.89968550e-04, 2.93567952e-04,
           3.09074678e-04, 3.30977731e-04, 3.58166387e-04, 3.69985575e-04,
           3.91772239e-04, 4.14449686e-04, 4.26158347e-04, 4.74296584e-04,
           4.93935939e-04, 5.25832774e-04, 5.51191590e-04, 1.13461807e-05,
           5.75033956e-04, 1.24578789e-03, 6.10948192e-06, 6.73606194e-04,
           6.95595455e-04, 7.60259530e-04, 8.10760270e-04, 8.09719774e-04,
           8.68080146e-04, 9.29263471e-04, 9.57587192e-04, 1.02631629e-03,
           1.07497966e-03, 1.13159683e-03, 1.13970245e-03, 1.25010940e-03,
           1.30600851e-03, 1.35330935e-03, 1.41114969e-03, 3.01015002e-03,
           1.39645301e-05, 1.13461807e-05, 1.63736418e-03, 3.44506727e-03,
           4.18935903e-05, 1.83161129e-03, 1.95286450e-03, 2.01395607e-03,
           2.12821251e-03, 2.19326942e-03, 2.28382998e-03, 2.40942065e-03,
           5.09310427e-03, 3.92752409e-05, 2.67483160e-03, 5.65671364e-03,
           6.98226505e-05, 2.97049606e-03, 3.10787290e-03, 3.25901857e-03,
           6.63710757e-03, 5.14942047e-05, 3.55863970e-03, 3.75307805e-03,
           3.85527423e-03, 3.85664088e-03, 4.09838462e-03, 4.24584776e-03,
           8.78961834e-03, 4.60217637e-03, 4.71052951e-03, 6.80770842e-05,
           4.95350458e-03, 5.05652915e-03, 5.19359898e-03, 5.15150383e-03,
           5.42010540e-03, 1.00370060e-04, 5.64625977e-03, 5.67892389e-03,
           5.77634994e-03, 5.95737527e-03, 6.03336135e-03, 6.20351704e-03,
           6.33284975e-03, 6.51790310e-03, 6.57992652e-03, 6.69816189e-03,
           1.67574361e-04, 6.92810699e-03, 7.01398823e-03, 6.94824435e-03,
           7.16524509e-03, 1.45648459e-02, 7.56703983e-03, 2.25543964e-04,
           7.89738401e-03, 1.54756809e-02, 7.71425480e-03, 8.09427275e-03,
           8.39382957e-03, 8.18183249e-03, 8.39742581e-03, 8.34203948e-03,
           3.12953299e-04, 1.67730538e-02, 3.33536239e-04, 8.26567753e-03,
           9.04475903e-03, 8.39145274e-03, 1.71589849e-02, 8.84461556e-03,
           8.93076639e-03, 9.27995142e-03, 4.32900433e-04, 9.06312078e-03,
           8.92799267e-03, 8.94739154e-03, 1.75149751e-02, 9.02697729e-03,
           1.03704975e-03, 9.03724499e-03, 1.69524073e-02, 8.95575260e-03,
           1.14228478e-03, 1.71991004e-02, 8.38097616e-03, 9.35211562e-03,
           8.78497873e-03, 8.74749149e-03, 8.66313069e-03, 8.59993045e-03,
           8.47560231e-03, 8.51423658e-03, 8.32999043e-03, 7.19762980e-04,
           8.28317946e-03, 7.48354810e-03, 8.13332278e-03, 8.11264850e-03,
           7.93203982e-03, 7.85452488e-03, 7.79223921e-03, 7.83032474e-03,
           7.52855082e-03, 7.48520937e-03, 7.45812885e-03, 1.36806923e-02,
           7.05454078e-03, 7.78579569e-03, 8.84129312e-04, 9.44170056e-04,
           1.18703077e-02, 7.56471240e-03, 6.54342249e-03, 6.33668444e-03,
           6.22364649e-03, 6.12827598e-03, 6.06034631e-03, 5.93598207e-03,
           5.81085252e-03, 5.69866434e-03, 5.59124649e-03, 5.46241011e-03,
           5.32079275e-03, 5.30244173e-03, 5.08540757e-03, 5.01471042e-03,
           4.88315927e-03, 4.79397952e-03, 4.67141245e-03, 4.55878712e-03,
           4.40784376e-03, 4.34389689e-03, 4.34241652e-03, 4.11873006e-03,
           9.49591658e-04, 3.08249046e-03, 6.87286519e-03, 4.70417246e-03,
           3.60318725e-03, 3.53729983e-03, 8.90994691e-04, 2.56752538e-03,
           5.70823124e-03, 1.73870244e-03, 2.35320472e-03, 8.43108504e-04,
           3.10489153e-03, 2.99474807e-03, 2.89752412e-03, 3.15397832e-06,
           2.86191333e-03, 5.36445889e-03, 2.62013378e-03, 2.54095702e-03,
           2.43558928e-03, 9.10897374e-06, 2.41637017e-03, 2.25467397e-03,
           2.25247018e-03, 2.20791292e-03, 1.00642247e-05, 4.11385043e-03,
           1.95110930e-03, 1.91250577e-03, 1.02685819e-05, 1.86825312e-03,
           3.45639660e-03, 6.13209082e-06, 1.66321953e-03, 1.62444274e-03,
           4.51036401e-06, 1.58316577e-03, 3.04210012e-03, 1.42153043e-03,
           1.36771876e-03, 1.39253297e-03, 2.55172539e-03, 3.67720720e-06,
           1.17289189e-03, 2.34327863e-03, 2.88863719e-06, 3.41382417e-02])
    
    
    @staticmethod
    def fingerprint_match(filename):
        pass
    
    
    @staticmethod
    def preprocess_image(filename= '', background_color = '', 
                         grayscale= True, show_image = True, clip_border =0):
        
        ''' v3.0.1   created:2024-11-14   modified:2025-05-05
        INPUT:
            'filename'-     filepath to image; should be able to open most image types, but PNG or TIF is preferred
            (optional)
            'background_color'
        '''
        
        if filename == '':
            root = Tk()
            filename = filedialog.askopenfilename(title="Select an image file",
                                                  filetypes=[("Image Files", ".png .tif .tiff .jpeg .jpg")])
            root.destroy()
        
        name_check = False
        
        # get usable filepath variables from 'filename'
        file_dir = os.path.dirname(filename)
        name = os.path.basename(filename).split('.')[0]
        if name_check:
            #TODO make a 'name_check' function to verify the name works
            name = ''
            name = [name+part for part in name]
        
        #Open the filepath and pre-process it
        # img = Defects.preprocess_image(filename= filename)
        if grayscale:
            orig_img = Image.open(filename).convert('L')
        else:
            orig_img = Image.open(filename)
        
        plt.imshow(orig_img)
        plt.title(f"{name} (Raw PIL Image)")
        plt.show()
        
        if background_color == '':
            img_array = np.array(orig_img, dtype = 'uint8')
        elif background_color == 'black':
            #Create a background and apply to image (this gets rid)
            background = Image.new('L', orig_img.size, 0)
            background.paste(orig_img, (0, 0), orig_img)
            img_array = np.array(background, dtype = 'uint8')
        
        if show_image:
            #Plot the new background image
            greys = plt.cm.Greys.reversed()
            plt.imshow(img_array, cmap = greys)
            plt.title(f"{name} (w/ bkgrd)")
            plt.show()
        
        #Clip the border if called for
        if clip_border >=1:
            if len(img_array.shape) == 2:
                img_array = img_array[clip_border:(img_array.shape[0]-clip_border-1), 
                                      clip_border:(img_array.shape[1]-clip_border-1)]
            else:
                img_array = img_array[clip_border:(img_array.shape[0]-clip_border-1), 
                                      clip_border:(img_array.shape[1]-clip_border-1),
                                      ::]
        
        return img_array


    @staticmethod
    def grayscale_blob_prob(img,  group_dict = global_summary_dict_blank):
        ''' v0.1.0   created:2024-11-14   modified:2024-11-14
        Description.
        '''
        
        pass
    
    
    @staticmethod
    def image_blobber(filename, kernel_size = 7, threshhold_kernel_size = 11, bin_array = np.linspace(0,255,1),\
                    show_original_pic = True, show_blob_pic = True, \
                    show_area_plot = True, save_results = False):
        ''' v1.0   created:2024-03-25   modified:2025-03-31
        SEM-specific blobber (JEOL currently). Will merge & deprecate in future
        Not the best solution; implements a couple out-of-the box solutions that require fine tuning to work.
        Updates:
            2025-03-31- Altered to save regionprops as a pickle
        
        '''
        # get file properties
        folder_name = os.path.dirname(filename)
        name_parts = os.path.basename(filename).split('.')[0:-2]  #remove filetype
        name = ''
        name = [name+part for part in name_parts]
        
        # open image and convert to np.array
        gray_img = Defects.preprocess_image(filename= filename, img_array= np.array([]), grayscale= True, blob_mode= None)
        input_img_array = np.array(gray_img)
        
        # do adaptive threshold on gray image
        thresh_too = cv2.adaptiveThreshold(input_img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, threshhold_kernel_size, 1)
        
        # MORPH_ELLIPSE    MORPH_RECT   MORPH_CROSS
        # apply morphology close,open,close to get good blobs
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size,kernel_size))
        blob = cv2.morphologyEx(thresh_too, cv2.MORPH_CLOSE, kernel)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size,kernel_size))
        blob = cv2.morphologyEx(blob, cv2.MORPH_OPEN, kernel)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size,kernel_size))
        blob = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel)   
        
        # Get contours
        cnts = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        contours, hierarchy = cv2.findContours(blob, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        c_img = cv2.drawContours(input_img_array, cnts, -1, (0), 10)  #draw contours on image
        
        # Get contour areas
        area_list = []
        for this_contour in contours:
            this_area = cv2.contourArea(this_contour)
            area_list.append(this_area)
        area_array = np.array(area_list)
        
        # write results to disk if desired
        if show_original_pic:
            plt.figure(figsize=(5,5))
            plt.imshow(thresh_too)
            plt.title(f"Threshold Image (threshold kernel size = {threshhold_kernel_size})")
            plt.show()    
        
        if show_blob_pic:
            plt.figure(figsize=(5,5))
            plt.imshow(blob)
            plt.title(f"Blob Pic (kernel size = {kernel_size})")
            plt.show()
        
            #plt.figure(figsize=(5,5))
            #plt.imshow(thresh_too)
            #plt.title("'Blob' binary image")
            #plt.show()
        
        #alternative 'blob' counting and property method
        # Define blobs and get some properties
        label_img = label(thresh_too)
        properties = ('label', 'coords', 'area', 'centroid', 'eccentricity', 'perimeter_crofton')
        props = regionprops_table(label_img, properties= properties)
        table = pd.DataFrame(props)
        if save_results:
            pd.to_pickle(table, os.path.join(folder_name, name+"_RegionProps.pickle"))
        
        # Save or plot the results
        folder_name = os.path.dirname(filename)
        name = str(os.path.basename(filename).replace('.png', ''))
        if show_area_plot:
            sns.set(rc={'figure.figsize':(7,5)})
            sns.set(font_scale = 1)
            
            '''
            # Do the actual graphing
            this_graph = sns.histplot(area_array, bins =30, \
                                     log_scale=False, palette = 'rocket', \
                                     kde =True, label = name, \
                                     stat='probability', legend=False, \
                                     common_bins=True)
            this_graph.set(xlabel ="Area of particles (pixels, log scale)", ylabel= "Fraction of total particles")
            #leg = this_graph.legend(loc='upper right')
            if save_results:
                plt.savefig(os.path.join(folder_name, name+"_ParticleAreas.png"))
            plt.show()'''
        
            # Refactor areas as effective diameters
            eff_diams = np.sqrt(area_array/math.pi)*2  #assume circular area; convert radius to diameter
            #   #microns = 1.5105*pixels - 1.2727   #101.3x mag
            # eff_diams = eff_diams*1.5105
            # eff_diams = eff_diams-1.2727
            #   # adjust for hand-measured vs. blob-measured microns trendline
            #   # hand_measured = 1.1079*blob_measured+4.0688
            # eff_diams = eff_diams*1.1079
            # eff_diams = eff_diams+4.0688
              
              # adjust areas for JEOL resolution
            JEOL_pix_height = .76927   #pixel height in microns
            JEOL_pix_width = .76927   #pixel height in microns
            eff_diams = eff_diams*(JEOL_pix_height*JEOL_pix_width)   # pixels^2 * (um/pix-height) * (um/pix-width) = um^2
            
            # Do the actual graphing
            this_graph = sns.histplot(eff_diams[eff_diams>1], bins =30, \
                                     log_scale=False, palette = 'rocket', \
                                     kde =True, label = name, \
                                     stat='probability', legend=False, \
                                     common_bins=True)
            this_graph.set(xlabel ="Diameter of particles (microns, log scale)", ylabel= "Fraction of total particles")
            #leg = this_graph.legend(loc='upper right')
            if save_results:
                plt.savefig(os.path.join(folder_name, name+"_ParticleDiameters.png"))
            plt.show()
        
        if save_results:
            cv2.imwrite(os.path.join(folder_name, name + "_threshold.png"), thresh_too)
            cv2.imwrite(os.path.join(folder_name, name + "_blob.png"), blob)
        
        
        print(f"For {name.replace('.jpg','')}:    avg diameter: {np.average(eff_diams):.2f} +/- {np.std(eff_diams):.2f}")
        cnts, bins = np.histogram(eff_diams, bin_array)
    
        return cnts, eff_diams
    
    
    @staticmethod
    def grayscale_binarize(img_array, prob_dict={}, kernel_size = 4, \
                           selection_mode = 'gaussian-1', show_output_scatter= True):
        ''' v1.1   created:2024-11-14   modified:2024-11-15
        Default to looking for dark blobs in a bright field. 
        'kernel_size'- defines square kernel n+1 x n+1; default is a 9x9 kernel; minimum is a 0 1x1 pixel-by-pixel kernel
                    4 is a good value typically (25x25)
        'selection_mode' -
            'gaussion-<sigma value>'- assume gaussian dist., get standard error and assume minimum threshold of 'sigma value' below median
        '''
        
        # 
        if len(prob_dict)>0:
            bins = prob_dict['bins']
            cnts = prob_dict['cnts']
            bin_n = len(bins)
            try:
                filter_array = prob_dict['filter_array']
            finally:
                filter_array = Defects.make_filter_array(bins, cnts, static_threshold = 70)
        else:
            cnts, bins = np.histogram(img_array, bins = 256)
            probs = cnts/sum(cnts)
            filter_array = Defects.make_filter_array(bins, cnts, static_threshold = 70)
            
        #Define 'global' probabillities
        full_probs = cnts/sum(cnts)

        #
        if type(img_array) == PIL.Image.Image:
            img_array = np.array(img_array)
            
        #
        if 'gaussian' in selection_mode:
            sigma_guess = selection_mode.split('-')[1]
            try:
                sigma = float(sigma_guess)
            finally:
                sigma = 1
        else:
            sigma = 1

        #Get a binarized image
        img_height = img_array.shape[0]
        img_width = img_array.shape[1]

        #TODO: get rid of FOR loops, index better for speed up
        return_array = np.zeros( (img_height, img_width) )
        kernel_output_values = []
        for y_idx in tqdm(range(kernel_size, (img_height-kernel_size))):
            for x_idx in range(kernel_size, (img_width-kernel_size)):
                try:
                    this_array = img_array[y_idx-kernel_size:y_idx+kernel_size, x_idx-kernel_size:x_idx+kernel_size]
                    these_cnts, _ = np.histogram(this_array, bins= 256)
                    #these_cnts = these_cnts * filter_array
                    these_probs = these_cnts/sum(these_cnts)
                    
                    these_probs = these_probs * filter_array
                    
                    #plt.plot(these_probs)
            
                    prob_diff = these_probs/(these_probs + full_probs)
                    prob_diff = prob_diff[~np.isnan(prob_diff)]
                    
                    this_value = np.ones( (prob_diff.shape))/prob_diff
                    this_value = np.nan_to_num(this_value, nan=0.0, posinf=0.0, neginf=0.0)
                    this_value = this_value/this_value.max()
                    this_value = np.sum(this_value)
                    #this_value = np.sum(this_value)/(kernel_size+1)**2
                    
                    # prior calculation method from Jupyter Notebook days
                    #
                    #diff_row.append(prob_diff.sum())
                    #bayes_row.append(np.prod(prob_diff[prob_diff>0]))   #joint prob of pixels occuring (ignore 0 probabilites obviously)
                    
                    return_array[y_idx, x_idx] = this_value
                    kernel_output_values.append(this_value)
                
                except ValueError:
                    return_array[y_idx, x_idx] = 0
                    kernel_output_values.append(0)
                    
        #%#%

        #Select for location values by mode
          #clean up nan and inf values
        kernel_output_values = np.nan_to_num(kernel_output_values, nan=0.0, posinf=0.0, neginf=0.0)
        return_array = np.nan_to_num(return_array, nan=0.0, posinf=0.0, neginf=0.0)
          #get kernel-value histogram
        kernel_cnts, kernel_bins = np.histogram(kernel_output_values, bins =100)
          #get a 'clean' maximum point to threshold values to
          #  if the distribution is a gaussian, this is typically close to the mean
          #  otherwise, this value is 
        mean = np.mean(np.array(kernel_output_values))   #real mean
        #comb_list = [(this_cnt, this_bin) for this_cnt, this_bin in zip(kernel_cnts, kernel_bins[1::])]
        #comb_list = sorted(comb_list, key=itemgetter(0), reverse = True)[0:3]
        #mean = np.mean(np.array([tup[1] for tup in comb_list]))  #pseudo-'peak' mean
          #get stndrd values; not currently used
        std_dev = np.std(np.array(kernel_output_values))
        this_max = max(kernel_output_values)

        #test_thresh = mean + (std_dev*sigma)
        thresh = mean + std_dev

        #
        output_array = np.copy(return_array)
        output_array[output_array < thresh] = 0
        output_array[output_array > thresh] = 1
        
        #
        if show_output_scatter:
            plt.scatter(kernel_bins[1::], kernel_cnts)
            plt.plot([mean, mean], [0, max(cnts)], color='m')
            plt.plot([thresh, thresh], [0, max(cnts)], color='teal')
            plt.show()

        return output_array
            
    
    def sliding_window_threshold(img_array, thresh_dict, mask=None,
                                 cnt_mask = None, cnt_mask_type = 'calc_based',
                                 pixel_value_transform = 'trained_blister_metal_prob',
                                 step = 1, stride = 1, window_max = 13, 
                                 window_min = 13, window_step_number = 0
                                 ):
        
        ''' v1.0.2  created:2025-04-15  modified:2025-05-06
        Description:
            Uses a sliding window
            
        Inputs:
            'img_array'-            numpy array or array-like object (i.e. PIL.Image) that can be converted to a numpy array
            'thresh_dict'-          output from ImageAnalysis.Utilities.dynamic_threshold()
            'cnt_mask'-             mask array for 'image_cnts' from dictionary; i.e. mask all above a threshold value and only take lower values
            'cnt_mask_type'-        use same calc method in 'thresh_dict' to get local entropy; 
                            'calc_based'- based on the calculation method in 'thresh_dict'
            'probability_calc'-     type of calculation
                            'trained_blister_metal_prob'- Bayesian weighting of pixels for blister/not-blister probability
                            'threshold_weighted_entropy'
            'stride'-               stride-size of moving window
            'window_max'-           max size of window to run
            'window_min'-           min size of window to run
            'window_step_number'-   decrement from 'max' to 'min' window size run on each kernel 
        '''

        #Condition window and kernel sizes
        if (window_min != window_max):
            #if window max and min are specified but number of steps isn't, take a guess
            if (window_step_number == 0) and (window_min > 0):
                maxmin_diff = window_max-window_min
                window_step_number = 5      #default to 5
                window_step_number = 5      #default to 5
                
                kernel_sizes = np.round(np.linspace(window_min, window_max, window_step_number))
                kernel_sizes = np.unique(kernel_sizes).astype(int)
                
            elif (window_min == 0):
                window_min = window_max
                window_step_number = 1
                
                kernel_sizes = np.array([max([window_max, window_min])])
        
        else:
            kernel_sizes = np.array([max([window_max, window_min])])

        #Genearate metrics and summary variables
           # extract dictionary values
        name = thresh_dict['name']
        image_cnts = np.round(thresh_dict['cnts'])
        image_bins = np.round(thresh_dict['bins'])
        upper_FWHM_pixel_value = round(thresh_dict['upper_FWHM_pix_value'])
        peak_pixel_value = round(thresh_dict['peak_pix_value'] )
        lower_FWHM_pixel_value = round(thresh_dict['lower_FWHM_pix_value'])
        upper_guassian_pixel_threshold = round(thresh_dict['max_threshold_pix_value'])
        lower_guassian_pixel_threshold = round(thresh_dict['min_threshold_pix_value'])
        calculation = thresh_dict['calculation']
           # generate variables
        global_cnt_probs = image_cnts/sum(image_cnts)

        #Generate a trivial (no masking) image mask if none is provided
        #  convert to 'int' and use products for masking (i.e. be careful when 0's are ignored as masking vs. when they're real data)
        if mask == None:
            mask_array = np.ones((img_array.shape[0], img_array.shape[1]))
            mask_array = mask_array > 0
            mask_array = mask_array.astype(int)
        else:
            if (mask_array.shape == img_array.shape):
                pass
            else:
                if mask_array.shape[0]<img_array.shape[0]:
                    img_array = img_array[0:mask_array.shape[0]-1, ::]
                if mask_array.shape[0]>img_array.shape[0]:
                    mask_array = mask_array[0:img_array.shape[0]-1, ::]
                if mask_array.shape[1]<img_array.shape[1]:
                    img_array = img_array[::, 0:mask_array.shape[1]-1]
                if mask_array.shape[1]>img_array.shape[1]:
                    mask_array = mask_array[::, 0:img_array.shape[1]-1]
            mask_array = mask_array.astype(int)
            
        #Generate the count mask if none is provided
        if cnt_mask == None:
            weights = np.ones(len(image_bins))
            if (cnt_mask_type == 'calc_based'):
                calc_str_parts = calculation.split(';')
                calc_type = calc_str_parts[0]
                calc_region = calc_str_parts[1]
                
                if (calc_type == 'outside_CLT'):
                    if calc_region == 'below':
                        threshold = lower_guassian_pixel_threshold
                        weights[image_bins>threshold] = 0
                    if calc_region == 'above':
                        threshold = lower_guassian_pixel_threshold
                        weights[image_bins>threshold] = 0
            #if all else fails, just make a trivial mask (no masking)
            else:
                weights = np.ones(len(image_bins))
                

        #Modify arrays and preprocess
        print(f"\t Applying pixel transform: ({pixel_value_transform})")
        print()
          # convert pixel intensities into probabilities
        if pixel_value_transform == 'trained_blister_metal_prob':
            metal_probs = Utilities.metal_avg_prob
            blister_probs = Utilities.blister_avg_prob
              #multiply by 'weights' to zero out pixels not considered
              #  i.e. only consider 'dark' pixels
            metal_probs = np.multiply(metal_probs, weights)
            blister_probs = np.multiply(blister_probs, weights)
              #Replace each pixel intensity with the probability of that intensity
            metal_prob_img = Utilities.multiple_array_replace(img_array, range(0,256), metal_probs).astype(np.float16)
            blister_prob_img = Utilities.multiple_array_replace(img_array, range(0,256), blister_probs).astype(np.float16)
              #mask images; FROM HERE ON, 0's should be ignored in calculations
            metal_prob_img = np.multiply(metal_prob_img, mask_array).astype(np.float16)
            blister_prob_img = np.multiply(blister_prob_img, mask_array).astype(np.float16)
            
            #Generate sliding windows
            print("\t Making sliding windows")
            print()
            max_kernel = max(kernel_sizes)
            metal_prob_windows = sliding_window_view(metal_prob_img, (max_kernel, max_kernel))
            del metal_prob_img
            blister_prob_windows = sliding_window_view(blister_prob_img, (max_kernel, max_kernel))
            del blister_prob_img
            # mask_array_windows = sliding_window_view(mask_array, (max_kernel, max_kernel))
            
              # reshape sliding windows from MxNxkxk to MxNxk**2
              #  i.o.w flatten the last dimension
            print("\t Reshaping windows")
            print()
            metal_prob_windows = metal_prob_windows.reshape((metal_prob_windows.shape[0], metal_prob_windows.shape[1], metal_prob_windows.shape[2]**2))
            blister_prob_windows = blister_prob_windows.reshape((blister_prob_windows.shape[0], blister_prob_windows.shape[1], blister_prob_windows.shape[2]**2))
            # mask_array_windows = mask_array_windows.reshape((mask_array_windows.shape[0], mask_array_windows.shape[1], mask_array_windows.shape[2]**2))

            #   # multiply to create masked regions (masked entries are 0's)
            # print("Masking windows")
            # print()
            # metal_prob_windows = np.multiply(metal_prob_windows, mask_array_windows)
            # blister_prob_windows = np.multiply(blister_prob_windows, mask_array_windows)
            #       # delete 'mask_array_windows' to save RAM
            # del mask_array_windows
              #process windows
              #NOTE: Bayesian formulation is 'blister_prob_windows' = numerator, 'sum_prob_windows'=denominator
            print("\t Processing windows")
            print()
              #Currently using the sum of pixel probabilities rather than joint product (i.e. CUMULATIVE prob., not JOINT prob.)
              # NOTE: IF USING PRODUCT: drop zeros to avoid zero products; very large memory reservation for product operation
            blister_prob_windows = np.sum(blister_prob_windows, axis=2)
            metal_prob_windows = np.sum(metal_prob_windows, axis=2)
            sum_prob_windows = (metal_prob_windows + blister_prob_windows).reshape(blister_prob_windows.shape[0], blister_prob_windows.shape[1])
            del metal_prob_windows
            
            #Generate the 'final' image
            blob_array = np.divide(blister_prob_windows, sum_prob_windows)

        if pixel_value_transform == 'threshold_weighted_entropy':

            #Generate sliding windows
            print("\t Making sliding windows")
            print()
            max_kernel = max(kernel_sizes)
            img_array_windows = sliding_window_view(img_array, (max_kernel, max_kernel))
            mask_array_windows = sliding_window_view(mask_array, (max_kernel, max_kernel))
            
              # reshape sliding windows from MxNxkxk to MxNxk**2
              #  i.o.w flatten the last dimension
            print("\t Reshaping windows")
            print()
            img_array_windows = img_array_windows.reshape((img_array_windows.shape[0], img_array_windows.shape[1], img_array_windows.shape[2]**2))
            mask_array_windows = mask_array_windows.reshape((mask_array_windows.shape[0], mask_array_windows.shape[1], mask_array_windows.shape[2]**2))
              # multiply to 
            print("\t Masking windows")
            print()
            img_array_windows = np.multiply(img_array_windows, mask_array_windows)
                 # delete 'mask_array_windows' to save RAM
            del mask_array_windows
            
            #Generate a grid of pixels
              # get clean boundaries and stride information
            y_remainder = img_array_windows.shape[0] % stride
            y_num = img_array_windows.shape[0] // stride
            if y_remainder != 0:
                y_start = y_remainder//2
                y_end = img_array_windows.shape[0] - (1+(y_remainder-y_start))
            else:
                y_start = 0
                y_end = img_array_windows.shape[0]-1
              # get clean boundaries and stride information
            x_remainder = img_array_windows.shape[1] % stride
            x_num = img_array_windows.shape[1] // stride
            if x_remainder != 0:
                x_start = x_remainder//2
                x_end = img_array_windows.shape[1] - (1+(x_remainder-x_start))
            else:
                x_start = 0
                x_end = img_array_windows.shape[1]-1
              # make an evenly-spaced value range based on the values calculated above
            ys = np.linspace(y_start, y_end, y_num)
            xs = np.linspace(x_start, x_end, x_num)
              # generate the actual meshed values (i.e. mxn sized area from m- and n-length arrays)
            mesh_x, mesh_y = np.meshgrid(xs, ys)
              # flatten arrays for easier 
            mesh_x = mesh_x.flatten().astype(int)
            mesh_y = mesh_y.flatten().astype(int)
            image_coordinates = np.stack((mesh_x, mesh_y), axis=1)

            #Do the actual calculations
            if len(kernel_sizes) == 1:
                kernel_size = kernel_sizes[0]
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size,kernel_size))
                kernel = (kernel-1)+kernel
                
                #Run through the indices and populate with local entropy results
                pbar = tqdm(total= mesh_x.shape[0])   #progress bar initialize
                for idx, (this_x, this_y) in enumerate(zip(mesh_x, mesh_y)):
                    pbar.update(1)   #progress bar update
                    this_patch = img_array_windows[this_y, this_x, ::, ::] * kernel
                    these_values = this_patch[mask_array_windows[this_y, this_x, ::, ::]]
                    these_cnts, _ = np.histogram(these_values, image_bins)
                    #mask cnts by entropy 
                    this_sum = np.sum(np.multiply(these_cnts, weights))
                    blob_array[this_y, this_x] = this_sum
                pbar.close()

        # #Start a new entry for kernel_based entropy counting
        # thresh_dict.update( {'kernel_estimate_threshold':{
        #     'pixel_'
        #     }})

        # 'metal_prob_img'  'blister_prob_img'  'blob_array'

        plt.figure(figsize=(20,20))
        plt.imshow(blob_array)
        plt.title(f"{name} Probability Image")
        plt.colorbar()
        plt.show()
        
        return thresh_dict, blob_array
    
    
    @staticmethod
    def make_filter_array(bins, cnts, mode = 'static-lower', static_threshold=0):
        '''
        
        'static-lower' - select values below the static threshold
        'static-upper' - select values above the static threshold
        
        TODO: make this a real function
        '''
        
        bin_n = len(bins)
        cnts_n = len(cnts)
        
        if bin_n == cnts_n:
            pass
        elif (bin_n-1) == cnts_n:
            bins = bins[1::]  #clip the bottom histogram edge if a raw histogram edge set is passed as input
            bin_n = len(bins)
        else:
            #TODO: fix this to take into account different array sizes
            pass
        
        #
        if ('static' in mode) and (static_threshold ==0):
            #TODO make this adaptive 
            pass
            
        #
        if mode == 'static-lower':
            filter_array = np.zeros(bin_n)
            filter_array[bins < static_threshold] = 1
        
        if mode == 'static-upper':
            filter_array = np.zeros(bin_n)
            filter_array[bins > static_threshold] = 1
            
        return filter_array
    
    @staticmethod
    def cv2_blobber(filename, show_orig_pic = True, show_threshold_pic = False, \
                    show_blob_pic = True, show_area_plot = False, \
                    save_summary = True, save_results = False,\
                    clip_border = 0, kernel_size = 5, grayscale_threshold = 111,\
                    close_operation_modifier = 0, open_close_iterations = 1):
        
        ''' v4.0.1   created:2022   modified:2025-04-02
        Default to looking for dark blobs in a bright field. 
        Takes adaptive threshold and returns a binary image.
        NOTES
            - need to convert all numpy arrays to Python lists for JSON serializing to work
        
        Updates:
            2025-04-01- changed to v4; 
                - updated output to dictionary to accomodate variable output modes (i.e. w/countours, w/out, etc.)
                - Allows for updated functionality options in the future as well
                - Added default dictionary output and default 'save_summary' boolean
            2025-04-02-v4.0.1
                - Minor debugging and cleaning
        '''
        
        #Define some initial parameters and variables
          # define histogram bins
        perimeter_bins = [0, 10, 25, 50, 100, 200, 300, 400, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 10000]
        area_bins = [0, 10, 25, 50, 100, 200, 300, 400, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 10000]
        eccen_bins = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 
                      0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]
          # get usable filepath variables from 'filename'
        file_dir = os.path.dirname(filename)
        name_parts = os.path.basename(filename).split('.')
        name = ''
        name = [name+part for part in name_parts]
        
        #Open the filepath and pre-process it
        # img = Defects.preprocess_image(filename= filename)
        img = Image.open(filename)
        img = np.array(img)
        img = img[clip_border:(img.shape[0]-clip_border-1), clip_border:(img.shape[1]-clip_border-1)]
        
        #Pull some summary specs from the opened image and start a return dictionary
        cnts, bins = np.histogram(img, bins= 256)
        default_image_dict = {
            'summary': {
                'filename': filename,
                'hori_dimension': img.shape[1],
                'vert_dimension': img.shape[0],
                'color-dimension': 1,
                'grayscale_histogram': cnts.tolist(),
                },
            'cv2_blob_summary': {
                'area_bins': area_bins,
                'area_cnts': [],
                'perimeter_bins': perimeter_bins,
                'perimeter_cnts': [],
                'eccentricity_bins':eccen_bins,
                'eccentricity_cnts': [],
                }
            }

        if show_orig_pic:
            print()
            print("Raw grayscale image")
            plt.figure(figsize=(10,10))
            plt.imshow(img)
            plt.show()
            print()

        # do adaptive threshold on gray image
        thresh_too = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, grayscale_threshold, 3)

        # apply morphology open then close
        for idx in range(open_close_iterations):
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size,kernel_size))
            blob = cv2.morphologyEx(thresh_too, cv2.MORPH_OPEN, kernel)
            close_kernel_size = kernel_size + close_operation_modifier
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_kernel_size, close_kernel_size))
            blob = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel)
            if close_operation_modifier != 0:
                # open_kernel_size = kernel_size + close_operation_modifier
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size,kernel_size))
                blob = cv2.morphologyEx(thresh_too, cv2.MORPH_OPEN, kernel)

        # invert blob
        #blob = (255 - blob)

        # Get contours
        cnts = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        big_contour = max(cnts, key=cv2.contourArea)

        contours, hierarchy = cv2.findContours(blob, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        blank_img = np.multiply(np.ones((img.shape[0], img.shape[1])), 255)
        cv2.drawContours(blank_img, cnts, -1, (0), 10)

        #plt.figure(figsize=(10,10))
        #plt.imshow(blank_img)
        #plt.show()

        # test blob size
        blob_area_thresh = 1
        blob_area = cv2.contourArea(big_contour)
        if blob_area < blob_area_thresh:
            print("Blob Is Too Small")

        # draw contour
        contour = img.copy()
        contour = cv2.drawContours(contour, [big_contour], -1, (0,0,255), 1)

        # write results to disk if desired
        if show_threshold_pic:
            plt.figure(figsize=(10,10))
            plt.imshow(thresh_too)
            plt.show()    

        if show_blob_pic:
            plt.figure(figsize=(10,10))
            plt.imshow(blob)
            plt.show()

        # Define blobs and get some properties
        label_img = label(thresh_too)
        properties = ('label', 'coords', 'area', 'centroid', 'eccentricity', 'perimeter_crofton')
        props = regionprops_table(label_img, properties= properties)
        table = pd.DataFrame(props)
        
          #NOTE: need to convert all numpy arrays to Python lists for JSON serializing to work
        cnts, bins = np.histogram(table['area'], bins = area_bins)
        default_image_dict['cv2_blob_summary']['area_cnts'] = list(cnts.tolist())
        default_image_dict['cv2_blob_summary']['area_bins'] = list(bins.tolist())
        
        cnts, bins = np.histogram(table['perimeter_crofton'], bins = perimeter_bins)
        default_image_dict['cv2_blob_summary']['perimeter_cnts'] = list(cnts.tolist())
        default_image_dict['cv2_blob_summary']['perimeter_bins'] = list(bins.tolist())
        
        cnts, bins = np.histogram(table['eccentricity'], bins = eccen_bins)
        default_image_dict['cv2_blob_summary']['eccentricity_cnts'] = list(cnts.tolist())
        default_image_dict['cv2_blob_summary']['eccentricity_bins'] = list(bins.tolist())
        
            
        # Save or plot the results
        folder_name = os.path.dirname(filename)
        name = str(os.path.basename(filename).replace('.png', ''))
        if show_area_plot:
            sns.set(rc={'figure.figsize':(15,10)})
            sns.set(font_scale = 2)
            
            # Refactor the pixel areas as a rough um^2 estimate based on total surface
            # TODO: Make the reference value better and validate
            #reference_area = math.pi*((12700/2)**2)  # um^2
            #    Subtract padding (usually 200 pixels total) from each dimention to get approximate image surface area
            # total_area = round(math.pi * ((src.shape[0]-200)/2 * (src.shape[1]-200)/2), 3)  # Approx. area in pixels
            # pix_to_um_conv = round(reference_area/total_area, 6)  #um^2 / pixel
            # array = table[table['area']<500000]['area']*pix_to_um_conv
            
            # # Do the actual graphing
            # this_graph = sns.histplot(array, bins =30, \
            #                          log_scale=True, palette = 'rocket', \
            #                          kde =True, label = sample, \
            #                          stat='probability', legend=False, \
            #                          common_bins=True)
            # this_graph.set(xlabel ="Area of defects (pixels, log scale)", ylabel= "Fraction of total defects")
            # #leg = this_graph.legend(loc='upper right')
            # if save_results:
            #     plt.savefig(os.path.join(folder_name, name+"_DefectAreas.png"))
            # plt.show()

        if save_results:
            cv2.imwrite(os.path.join(folder_name, name + "_threshold.png"), thresh_too)
            cv2.imwrite(os.path.join(folder_name, name + "_blob.png"), blob)
            table.to_csv(os.path.join(folder_name, name + "Blob_prop_table.csv"))
            
        if save_summary:
            try:
                json_filepath = os.path.join(file_dir, str(name)+"_summary.json")
                with open(json_filepath, 'w') as file:
                    json.dump(default_image_dict, file, indent=4)
                    # json.dump(default_image_dict, file, indent=4, cls= NpEncoder)   #untested solution for encoding
            except:
                return default_image_dict
            
        return default_image_dict
    
    
    def defect_JSON_parser(filename):
        pass
        
    

####################################################################################################################################################
####################################################################################################################################################


class Utilities:
    ''' v0.2.6   created:2024-10-21   modified:2025-05-28
    Wrapper class for utility functions and variables that aren't unique to 'ImageAnalysis' classes and could be used elsewhere.
    '''
    
    @staticmethod 
    def create_circular_mask(height, width, center=None, radius=None):
        
        ''' v1.0.0     created:2025-04-14    modified:2025-04-14
        Take in info and return a numpy boolean array        
        Taken entirely from link below and modified for clarity.
        '''
        
        if center is None: # use the middle of the image
            center = (int(width/2), int(height/2))
        if radius is None: # use the smallest distance between the center and image walls
            radius = min(center[0], center[1], width-center[0], height-center[1])
    
        Y, X = np.ogrid[:height, :width]
        dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2)
    
        mask = dist_from_center <= radius
        
        return mask
    
    @staticmethod 
    def multiple_array_replace(target_array, target_values, replacement_values):
        ''' v0.2.0     created:2025-04-28    modified:2025-04-29
        Take a (usually large) array and replace values sequentially.
        '''
        
        if type(target_array) != np.ndarray:
            target_array = np.array(target_array)
        
        dup_array = np.zeros(target_array.shape)
        
        for value, replacement in zip(target_values, replacement_values):
            dup_array[target_array==value] = replacement
            
        return dup_array
    

    @staticmethod    
    def get_slope_param(x_array, y_array):
        
        global return_dict
        
        ''' v0.1.0     created:2024-10-20    modified:2024-10-21
        Takes a (usually) log-log data series and tries to find at least 3 values that linear within a threshold.
        Returns a dictionary with data about whether or not that's possble and how rigid/ at what values linearity occurs.
        '''
        
        #Initialize blank return_dict
        threshold_multipliers = [0.01, 0.05, 0.1]
        y_diffs = [y_array[idx]-y_array[idx-1] for idx in range(1, len(y_array))]
        y_avg_diff = sum(y_diffs)/len(y_diffs)
        return_dict = {
            'thresholds': [str((t*100))+'%' for t in threshold_multipliers],
            'x_array': x_array,
            'y_array': y_array,
            'y_diffs': y_diffs,
            'diff_avg': y_avg_diff,
            'linear_region_exists': False,
            'linearity_bool_at_thresholds': [],
            'slopes': [],
            'linearity_start_idx':[],
            'linearity_end_idx':[]
            }
        
        #Flag if length of arrays won't work for these operations
        if len(y_array) != len(x_array):
            print("X and Y arrays don't have the same length; check inputs")
            return return_dict
        elif len(y_array) <3:
            print("Y-array does not have at least 3 values; check inputs")
            return return_dict

        #For each threshold value, if point-to-point slope is less than threshold, call that a slope
        for multiplier in threshold_multipliers:
            this_threshold = abs(y_avg_diff * multiplier)
            linearity_bool = [False for i in range(len(y_diffs))]
            linearity = False
            first_linear_idx = -1
            last_linear_idx = -1
            slope_list = []
            
            for idx in range(1,len(y_diffs)):
                if abs(y_diffs[idx]-y_diffs[idx-1])<this_threshold:
                    if linearity == False:
                        first_linear_idx = idx-1
                    slope_list.append(y_diffs[idx]-y_diffs[idx-1])
                    linearity_bool[idx] = True
                    linearity_bool[idx-1] = True
                    linearity = True
                    last_linear_idx = idx+1
            
            try:
                slopes = return_dict['slopes']
                bool_list = return_dict['linearity_bool_at_thresholds']
                start_list = return_dict['linearity_start_idx']
                end_list = return_dict['linearity_end_idx']
                
                if linearity == True:
                    return_dict['linear_region_exists'] = True
                    slopes.append(sum(slope_list)/len(slope_list))
                else:
                    slopes.append(0)
                    
                return_dict['slopes'] = slopes
                return_dict['linearity_bool_at_thresholds'] = bool_list.append(linearity_bool)
                return_dict['linearity_start_idx'] = start_list.append(first_linear_idx)
                return_dict['linearity_end_idx'] = end_list.append(last_linear_idx)
            except:
                print(return_dict)
        
        return return_dict
    
    
    @staticmethod
    def get_weighted_xy_mean(x_array, y_array):
        ''' v1.0    created:2022    modified:2024-11-10
        Read in two arrays (cartesian x/y values), and return a distance-weighted mean value.
        '''
        
        if len(x_array) == len(y_array):
            eu_dist_array = np.array([])
            for x, y in zip(x_array, y_array):
                eu_dist_array = np.append(eu_dist_array, math.sqrt(x**2 + y**2))
        else:
            min_length = min([len(x_array), len(y_array)])
            x_array = x_array[0:(min_length-1)]
            y_array = y_array[0:(min_length-1)]
            eu_dist_array = np.array([])
            for x, y in zip(x_array, y_array):
                eu_dist_array = np.append(eu_dist_array, math.sqrt(x**2 + y**2))
           # Run through every pair and add a summed weight that scales inversely with distance between points
        weighted_sum = np.zeros(len(eu_dist_array))
        for pt_idx, point in enumerate(eu_dist_array):
               #Add -1 do avoid 0 div error and peg all values to unity
            this_weight = np.absolute(np.subtract(eu_dist_array, point-1))
               #Keep in mind that 'this_weight' is actually a distance until the step below
            weighted_sum = np.add(weighted_sum, np.divide(1, this_weight**2))
        
        idx = 0
        weighted_x_list = []
        weighted_y_list = []
        for weight, pair in zip(weighted_sum,zip(x_array,y_array)):
            x = round(pair[0], 1)
            weighted_x_list.append(weight * x)
            y = round(pair[1], 1)
            weighted_y_list.append(weight * y)
            idx += 1

        if len(weighted_sum)>0:
            # If NaN's are thrown, default to zero
            try:
                weighted_x = round(sum(weighted_x_list)/sum(weighted_sum))
            except:
                weighted_x = 0
            try:
                weighted_y = round(sum(weighted_y_list)/sum(weighted_sum))
            except:
                weighted_y = 0
        else:
            weighted_x = 0
            weighted_y = 0
            
        return weighted_x, weighted_y
    
    
    @staticmethod
    def dynamic_threshold(array, num_bins = 100,
                          show_threshold_graph = True,
                          name = '', threshold = True,
                          calculation_range = 'below',
                          calculation_type = 'outside_CLT',
                          fix_bins = False):
        
        ''' v1.1.4    created:2025-04-08    modified:2025-07-19
        
        Description: General-purpose function for taking a bin::cnts histogram, assuming central limit theorem, and 
            and returning associated values. If thresholding and calculation values are set, do those and return.
            Returns a dictionary.
        
        Notes:
            - Rolling up code for laser profilometry crater isolation (2024-12-03) into a general purpose function.
            - Changed 'name' to include handling for filepaths
        '''

        #Define and initialize variables
          # define pixel integers if 256 is given (strong assumption)
        if num_bins == 256:
            cnts, bins = np.histogram(array, bins= list(range(0,256)))
        else:    
            cnts, bins = np.histogram(array, bins = num_bins)
          
          #check to see if 100 bins is overkill; only applicable in small systems (vignettes from images, for example)
        zero_count = 0
        for cnt in cnts:
            #flag negative values as well for future normalization
            if cnt <= 0:
                zero_count += 1
          #reduce the number of bins by the number of zero_counts
          #NOTE: hard-coded 10% below can be adjusted
        if (zero_count >= (0.1*num_bins)) and (not fix_bins):
            zero_int = int(num_bins-zero_count)  #force 'int' in case 'num_bins' isn't
            print(f"Too many zero-cnts with {num_bins}.")
            print(f"\t Reducting to {zero_int} histogram bins.")
            num_bins = zero_int
            cnts, bins = np.histogram(array, bins = num_bins)
            
        
          #get summary variables
        bin_middle_idx = num_bins//2
        bin_size = bins[bin_middle_idx+1]-bins[bin_middle_idx]   #Pick the middle bins to accomodate any edge-bin wierdness; should be consistent bin sizes
        global_max_cnt = max(cnts)
        cnt_max = max(cnts[2:bins.shape[-0]-3])   #skip first and last 2 bins to avoid edge effects (i.e. lots of zeros or )
        
        # check if 'name' is a filename and pull basename if so
        if name != '':
            if os.path.isfile(name):
                name = os.path.basename(name)
        else:
            name = "GenericName"
        
        #ASSUME CLT and get FWHM
        max_idx = np.where(cnts== cnt_max)[0] +1
        if type(max_idx)!=int:
            max_idx = max_idx[0]
        half_max = cnt_max//2
        diff_array = np.array([abs(value-half_max) for value in cnts])
        sorted_diff_array = np.sort(diff_array)
          #TODO: verify CLT by checking Gaussian shape; if not CLT, do something

        #Look at the first 10 values closest to the half-max value and try to pull the indices
        upper_halfmax_idx = num_bins-2   #start at the top end of the histogram
        upper_diff = abs(upper_halfmax_idx-max_idx)  #measure idx distance to upper end of array
        lower_halfmax_idx = -1   #start at bottom end of the histogram; offset by 1 to account for bin indexing
        lower_diff = abs(lower_halfmax_idx-max_idx)  #measure idx distance to lower end of array
        
        #Step through closest values to FWHM expectations and save them
        for value in sorted_diff_array[0:10]:
            #if np.where() returns more than one value, only take the first
            this_idx = np.where(diff_array==value)[0]
              #make sure 'this_idx' isn't an array
            if type(this_idx)!=int:
                this_idx = this_idx[0]
            this_diff = abs(this_idx-max_idx)
            
            #Check if closer upper bound
            if (this_idx > max_idx):
                if this_diff < upper_diff:
                    upper_diff = this_diff
                    upper_halfmax_idx = this_idx
                    
            #Check if closer lower bound
            if (this_idx < max_idx):
                if this_diff < lower_diff:
                    lower_diff = this_diff
                    lower_halfmax_idx = this_idx
                    
        #Make sure bounds are in range
        if lower_halfmax_idx < 0:
            lower_halfmax_idx = 0 
        if upper_halfmax_idx > (len(cnts)-2):
            upper_halfmax_idx = len(cnts)-2
        
        #Clean up and generate some summary variables
        upper_halfmax_idx +=1
        lower_halfmax_idx +=1
          #assume FWHM ~= to 2.4 std. devs. and try to find the upper and lower points 
        bin_2stddev_idx_diff = 2* max( abs(max_idx- lower_halfmax_idx), abs(upper_halfmax_idx-max_idx))
        lower_threshold_idx = int(max_idx-bin_2stddev_idx_diff)
        if lower_threshold_idx < 0:
            lower_threshold_idx = 0
        lower_threshold = bins[lower_threshold_idx]
        upper_threshold_idx = int(max_idx+bin_2stddev_idx_diff)
        if upper_threshold_idx > (len(cnts)-1):
            upper_threshold_idx = len(cnts)-1
        upper_threshold = bins[upper_threshold_idx]
        intial_lower_threshold = lower_threshold
        
        # print(f"lower_halfmax_idx: {lower_halfmax_idx}")
        # print(f"upper_halfmax_idx: {upper_halfmax_idx}")
        
        cnts_FWHM = max(cnts[lower_halfmax_idx], cnts[upper_halfmax_idx])- \
            abs(cnts[lower_halfmax_idx] - cnts[upper_halfmax_idx])
        bin_FWHM = max(bins[lower_halfmax_idx], bins[upper_halfmax_idx])- \
            abs(bins[lower_halfmax_idx] - bins[upper_halfmax_idx])
            
          #get variance of 'cnts' values, assume Gaussian, and set 5 std. dev. threshold
        if calculation_type == 'outside_CLT':
              #set minimum threshold as 1/8 of the FWHM; 
              #TODO: make this less weird and hard-coded; pick a more rational minimum
            max_cnt_threshold = round(cnt_max/16)
        
            if calculation_range == 'below':
                
                #Make sure the threshold is below about 1000 cnts
                if cnts[lower_threshold_idx] > max_cnt_threshold:
                    iteration_cnt = 0
                    max_iterations = 10
                    while (iteration_cnt < max_iterations) and (cnts[lower_threshold_idx] > max_cnt_threshold):
                        lower_threshold_idx -= 1
                        lower_threshold = bins[lower_threshold_idx]
                #Count the thresholds      
                calc_sum = 0
                for this_bin, this_cnt in zip(bins[1:lower_threshold_idx], cnts[0:lower_threshold_idx]):
                    if this_cnt <= max_cnt_threshold:
                        calc_sum += this_cnt
            
            if calculation_range == 'above':
                #Make sure the threshold is below about 1000 cnts
                if cnts[upper_threshold_idx] > max_cnt_threshold:
                    iteration_cnt = 0
                    max_iterations = 10
                    while (iteration_cnt < max_iterations) and (cnts[upper_threshold_idx] > max_cnt_threshold):
                        upper_threshold_idx += 1
                        upper_threshold = bins[upper_threshold_idx]
                #Count the thresholds      
                calc_sum = 0
                for this_bin, this_cnt in zip(bins[upper_threshold_idx:-1], cnts[(upper_threshold_idx-1):-1]):
                    if this_cnt <= max_cnt_threshold:
                        calc_sum += this_cnt 
        
        #Plot everything if called for
        if show_threshold_graph:
              #plot the peak max and pseudo FWHM
            plt.plot([bins[lower_halfmax_idx], bins[upper_halfmax_idx]],[half_max, half_max], color = 'm', linewidth = 4)
            plt.plot([bins[max_idx], bins[max_idx]], [0, cnt_max], color = 'm', linewidth = 1)
              #show the actual closest-bin level to the FWHM that the psuedo is calculated
            plt.plot([bins[lower_halfmax_idx], bins[upper_halfmax_idx]],[cnts_FWHM, cnts_FWHM], color = 'purple', linewidth = 5)
              #plot the upper and lower 5-sigma threshholds
            plt.plot([intial_lower_threshold, intial_lower_threshold], [0, half_max], color = 'lime', linewidth = 2)
            plt.plot([upper_threshold, upper_threshold], [0, half_max], color = 'lime', linewidth = 2)
            plt.plot([lower_threshold, lower_threshold], [0, half_max], color = 'red', linewidth = 2)
              #finish plotting the histogram values
            plt.scatter(bins[1::], cnts)
            plt.title(f"Height hist- {name}")
            plt.show()
            
        return_dict = {
            'name': name,
            'cnts': cnts.tolist(),
            'bins': bins.tolist(),
            'max_middle_cnt': cnt_max,
            'bin_size': bin_size,
            'lower_FWHM_bin_idx': lower_halfmax_idx,
            'upper_FWHM_bin_idx': upper_halfmax_idx,
            'FWHM': cnts_FWHM,
            'calculation': calculation_type + ';' + calculation_range,
            'calculation_cnt_sum': calc_sum,
            'upper_FWHM_pix_value': bins[upper_halfmax_idx],
            'peak_pix_value': min(bins[lower_halfmax_idx], bins[upper_halfmax_idx]) + abs(bins[upper_halfmax_idx]-bins[lower_halfmax_idx]),
            'lower_FWHM_pix_value': bins[lower_halfmax_idx],
            'max_threshold_pix_value': upper_threshold,
            'min_threshold_pix_value': lower_threshold
            }
        
        return return_dict
    
    
    def sliding_window_threshold(img_array, thresh_dict, mask=None,
                                 cnt_mask = None, cnt_mask_type = 'calc_based',
                                 pixel_value_transform = 'trained_blister_metal_prob',
                                 step = 1, stride = 1, window_max = 13, 
                                 window_min = 13, window_step_number = 0
                                 ):
        
        ''' v1.0.1  created:2025-04-15  modified:2025-05-28
        Description:
            Uses a sliding window and reference data to build a probability map of local
              pixel intensities in an SEM montage.
            
        Inputs:
            'img_array'-            numpy array or array-like object (i.e. PIL.Image) that can be converted to a numpy array
            'thresh_dict'-          output from ImageAnalysis.Utilities.dynamic_threshold()
            'cnt_mask'-             mask array for 'image_cnts' from dictionary; i.e. mask all above a threshold value and only take lower values
            'cnt_mask_type'-        use same calc method in 'thresh_dict' to get local entropy; 
                            'calc_based'- based on the calculation method in 'thresh_dict'
            'probability_calc'-     type of calculation
                            'trained_blister_metal_prob'- Bayesian weighting of pixels for blister/not-blister probability
                            'threshold_weighted_entropy'
            'stride'-               stride-size of moving window
            'window_max'-           max size of window to run
            'window_min'-           min size of window to run
            'window_step_number'-   decrement from 'max' to 'min' window size run on each kernel 
        '''

        name = thresh_dict['name']
        
        #Condition window size 
        if (window_min != window_max):
            #if window max and min are specified but number of steps isn't, take a guess
            if (window_step_number == 0) and (window_min > 0):
                maxmin_diff = window_max-window_min
                window_step_number = 5      #default to 5
                window_step_number = 5      #default to 5
            elif (window_min == 0):
                window_min = window_max
                window_step_number = 1
            #generate kernel sizes array
            kernel_sizes = np.round(np.linspace(window_min, window_max, window_step_number))
            kernel_sizes = np.unique(kernel_sizes).astype(int)
          #if 'max' and 'min' are the same, just use that number as a len=1 array
        else:
            kernel_sizes = np.array([window_max])

        #Genearate metrics and summary variables
           # extract dictionary values
        image_cnts = np.round(thresh_dict['cnts'])
        image_bins = np.round(thresh_dict['bins'])
        upper_FWHM_pixel_value = round(thresh_dict['upper_FWHM_pix_value'])
        peak_pixel_value = round(thresh_dict['peak_pix_value'] )
        lower_FWHM_pixel_value = round(thresh_dict['lower_FWHM_pix_value'])
        upper_guassian_pixel_threshold = round(thresh_dict['max_threshold_pix_value'])
        lower_guassian_pixel_threshold = round(thresh_dict['min_threshold_pix_value'])
        calculation = thresh_dict['calculation']
           # generate variables
        global_cnt_probs = image_cnts/sum(image_cnts)

        #Generate a trivial (no masking) image mask if none is provided
        #  convert to 'int' and use products for masking (i.e. be careful when 0's are ignored as masking vs. when they're real data)
        if mask == None:
            mask_array = np.ones((img_array.shape[0], img_array.shape[1]))
            mask_array = mask_array > 0
            mask_array = mask_array.astype(int)
        else:
            if (mask_array.shape == img_array.shape):
                pass
            else:
                if mask_array.shape[0]<img_array.shape[0]:
                    img_array = img_array[0:mask_array.shape[0]-1, ::]
                if mask_array.shape[0]>img_array.shape[0]:
                    mask_array = mask_array[0:img_array.shape[0]-1, ::]
                if mask_array.shape[1]<img_array.shape[1]:
                    img_array = img_array[::, 0:mask_array.shape[1]-1]
                if mask_array.shape[1]>img_array.shape[1]:
                    mask_array = mask_array[::, 0:img_array.shape[1]-1]
            mask_array = mask_array.astype(int)
            
        #Generate the count mask if none is provided
        if cnt_mask == None:
            weights = np.ones(len(image_cnts))
            if (cnt_mask_type == 'calc_based'):
                calc_str_parts = calculation.split(';')
                calc_type = calc_str_parts[0]
                calc_region = calc_str_parts[1]
                
                if (calc_type == 'outside_CLT'):
                    if calc_region == 'below':
                        threshold = lower_guassian_pixel_threshold
                        weights[image_bins[1::]>threshold] = 0
                    if calc_region == 'above':
                        threshold = lower_guassian_pixel_threshold
                        weights[image_bins[1::]>threshold] = 0
                
        #Modify arrays and preprocess
        print(f"\t Applying pixel transform: ({pixel_value_transform})")
        print()
          # convert pixel intensities into probabilities
        if pixel_value_transform == 'trained_blister_metal_prob':
            metal_probs = Utilities.metal_avg_prob
            blister_probs = Utilities.blister_avg_prob
            metal_prob_img = Utilities.multiple_array_replace(img_array, range(0,256), metal_probs).astype(np.float16)
            blister_prob_img = Utilities.multiple_array_replace(img_array, range(0,256), blister_probs).astype(np.float16)
              #mask images; FROM HERE ON, 0's should be ignored in calculations
            metal_prob_img = np.multiply(metal_prob_img, mask_array).astype(np.float16)
            blister_prob_img = np.multiply(blister_prob_img, mask_array).astype(np.float16)
            
            #Generate sliding windows
            print("\t Making sliding windows")
            print()
            max_kernel = max(kernel_sizes)
            metal_prob_windows = sliding_window_view(metal_prob_img, (max_kernel, max_kernel))
            del metal_prob_img
            blister_prob_windows = sliding_window_view(blister_prob_img, (max_kernel, max_kernel))
            del blister_prob_img
            # mask_array_windows = sliding_window_view(mask_array, (max_kernel, max_kernel))
            
              # reshape sliding windows from MxNxkxk to MxNxk**2
              #  i.o.w flatten the last dimension
            print("\t Reshaping windows")
            print()
            metal_prob_windows = metal_prob_windows.reshape((metal_prob_windows.shape[0], metal_prob_windows.shape[1], metal_prob_windows.shape[2]**2))
            blister_prob_windows = blister_prob_windows.reshape((blister_prob_windows.shape[0], blister_prob_windows.shape[1], blister_prob_windows.shape[2]**2))
            # mask_array_windows = mask_array_windows.reshape((mask_array_windows.shape[0], mask_array_windows.shape[1], mask_array_windows.shape[2]**2))

            #   # multiply to create masked regions (masked entries are 0's)
            # print("Masking windows")
            # print()
            # metal_prob_windows = np.multiply(metal_prob_windows, mask_array_windows)
            # blister_prob_windows = np.multiply(blister_prob_windows, mask_array_windows)
            #       # delete 'mask_array_windows' to save RAM
            # del mask_array_windows
              #process windows
              #NOTE: Bayesian formulation is 'blister_prob_windows' = numerator, 'sum_prob_windows'=denominator
            print("\t Processing windows")
            print()
              #Currently using the sum of pixel probabilities rather than joint product (i.e. CUMULATIVE prob., not JOINT prob.)
              # NOTE: IF USING PRODUCT: drop zeros to avoid zero products; very large memory reservation for product operation
            blister_prob_windows = np.sum(blister_prob_windows, axis=2)
            metal_prob_windows = np.sum(metal_prob_windows, axis=2)
            sum_prob_windows = (metal_prob_windows + blister_prob_windows).reshape(blister_prob_windows.shape[0], blister_prob_windows.shape[1])
            del metal_prob_windows
            
            #Generate the 'final' image
            blob_array = np.divide(blister_prob_windows, sum_prob_windows)

        if pixel_value_transform == 'threshold_weighted_entropy':

            #Generate sliding windows
            print("\t Making sliding windows")
            print()
            max_kernel = max(kernel_sizes)
            img_array_windows = sliding_window_view(img_array, (max_kernel, max_kernel))
            mask_array_windows = sliding_window_view(mask_array, (max_kernel, max_kernel))
            
              # reshape sliding windows from MxNxkxk to MxNxk**2
              #  i.o.w flatten the last dimension
            print("\t Reshaping windows")
            print()
            img_array_windows = img_array_windows.reshape((img_array_windows.shape[0], img_array_windows.shape[1], img_array_windows.shape[2]**2))
            mask_array_windows = mask_array_windows.reshape((mask_array_windows.shape[0], mask_array_windows.shape[1], mask_array_windows.shape[2]**2))
              # multiply to 
            print("\t Masking windows")
            print()
            img_array_windows = np.multiply(img_array_windows, mask_array_windows)
                 # delete 'mask_array_windows' to save RAM
            del mask_array_windows
            
            #Generate a grid of pixels
              # get clean boundaries and stride information
            y_remainder = img_array_windows.shape[0] % stride
            y_num = img_array_windows.shape[0] // stride
            if y_remainder != 0:
                y_start = y_remainder//2
                y_end = img_array_windows.shape[0] - (1+(y_remainder-y_start))
            else:
                y_start = 0
                y_end = img_array_windows.shape[0]-1
              # get clean boundaries and stride information
            x_remainder = img_array_windows.shape[1] % stride
            x_num = img_array_windows.shape[1] // stride
            if x_remainder != 0:
                x_start = x_remainder//2
                x_end = img_array_windows.shape[1] - (1+(x_remainder-x_start))
            else:
                x_start = 0
                x_end = img_array_windows.shape[1]-1
              # make an evenly-spaced value range based on the values calculated above
            ys = np.linspace(y_start, y_end, y_num)
            xs = np.linspace(x_start, x_end, x_num)
              # generate the actual meshed values (i.e. mxn sized area from m- and n-length arrays)
            mesh_x, mesh_y = np.meshgrid(xs, ys)
              # flatten arrays for easier 
            mesh_x = mesh_x.flatten().astype(int)
            mesh_y = mesh_y.flatten().astype(int)
            image_coordinates = np.stack((mesh_x, mesh_y), axis=1)

            #Do the actual calculations
            if len(kernel_sizes) == 1:
                kernel_size = kernel_sizes[0]
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size,kernel_size))
                kernel = (kernel-1)+kernel
                
                #Run through the indices and populate with local entropy results
                pbar = tqdm(total= mesh_x.shape[0])   #progress bar initialize
                for idx, (this_x, this_y) in enumerate(zip(mesh_x, mesh_y)):
                    pbar.update(1)   #progress bar update
                    this_patch = img_array_windows[this_y, this_x, ::, ::] * kernel
                    these_values = this_patch[mask_array_windows[this_y, this_x, ::, ::]]
                    these_cnts, _ = np.histogram(these_values, image_bins)
                    #mask cnts by entropy 
                    this_sum = np.sum(np.multiply(these_cnts, weights))
                    blob_array[this_y, this_x] = this_sum
                pbar.close()

        # #Start a new entry for kernel_based entropy counting
        # thresh_dict.update( {'kernel_estimate_threshold':{
        #     'pixel_'
        #     }})

        # 'metal_prob_img'  'blister_prob_img'  'blob_array'

        plt.figure(figsize=(20,20))
        plt.imshow(blob_array)
        plt.title(f"{name} Probability Image")
        plt.colorbar()
        plt.show()
        
        return thresh_dict, blob_array
    
    
 


