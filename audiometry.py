# Written 2021 Liberty Hamilton
# University of Texas at Austin
#
# liberty.hamilton@austin.utexas.edu
#

import xml.etree.ElementTree as ET
from copy import copy
import re
import numpy as np
from matplotlib import pyplot as plt
import glob

def dictify(r,root=True):
    '''
    Create dictionary from root XML object. 
    Input:
        r: root from xml.etree.ElementTree. This is done
           by the parse_audiometry function
    Output:
        d [dict] : dictionary of all the data in the xml file.
    Thanks to Erik Aronesty - see StackOverflow post
    https://stackoverflow.com/questions/2148119/how-to-convert-an-xml-string-to-a-dictionary
    '''
    if root:
        return {re.sub('{.*}', '', r.tag) : dictify(r, False)}
    d=copy(r.attrib)
    if r.text:
        d["_text"]=r.text
    for x in r.findall("./*"):
        x.tag = re.sub('{.*}', '', x.tag)
        if x.tag not in d:
            d[x.tag]=[]
        d[x.tag].append(dictify(x,False))
    return d


def parse_audiometry(xml_file):
    '''
    Parse audiometry xml file. This takes the Otoaccess xml files that have
    been exported and parses out the relevant pure tone data and QuickSIN 
    data. If other data are in the file, they are currently ignored, so if you
    want further functionality you have to write that yourself :)

    Input:
        xml_file [str] : Path to your xml_file for loading. 

    '''
    tree = ET.parse(xml_file)
    r = tree.getroot()

    QuickSIN = dict()  # TBD... in progress
    audiometry = dict()

    d = dictify(r, root=True)

    # Loop through the tests that were done. This is usually a pure tone audiogram ('Tone')
    # followed by the 'QuickSIN' speech in noise task.
    for test in d['SaData']['Session'][0]['Test']:
        # If this is the pure tone task
        if test['TestName'][0]['_text'] == 'Tone':
            measured_data = test['Data'][0]['RecordedData'][0]['Measured']
            # Loop through the measured data. There are usually two measurements, one
            # for the left ear, one for the right ear.
            for s in np.arange(len(measured_data)): 
                earside = measured_data[s]['Tone'][0]['Earside'][0]['_text']
                audiometry[earside] = {}  # initialize the dictionary
                # Find the number of tones that were played to this participant
                nfreqs = len(measured_data[s]['Tone'][0]['TonePoint'])
                # Loop through the tones and find the frequency and measured thresholds,
                # then save these to the audiometry dictionary for the relevant [earside]
                for tone in np.arange(nfreqs):
                    freq = int(measured_data[s]['Tone'][0]['TonePoint'][tone]['Frequency'][0]['_text'])
                    threshold = int(measured_data[s]['Tone'][0]['TonePoint'][tone]['IntensityUT'][0]['_text'])
                    audiometry[earside][freq] = threshold

    return audiometry


def plot_speechbanana(earside):
    '''
    Plot the speech banana for a given ear side ('Left','Right', or 'Both').
    Values for the speech banana are taken from the Interacoustics Otoaccess software.
    (These are also in the xml, but easier to just show here).
    
    Input:
        earside : 'Left', 'Right', or 'Both'. This changes the color of the banana.

    '''
    clrs = {'Left': 'b', 'Right': 'r', 'Both': [0.5, 0.5, 0.5]}
    freqs = np.array([125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000])
    thresh_top = np.array([3, 12, 20, 22, 23, 22, 20, 17, 14, 11, 9])
    thresh_bottom = np.array([30,46,57,62,63,62,60,56,53,48,44])
    plt.fill_between(freqs, thresh_top, y2=thresh_bottom, color=clrs[earside], alpha=0.5, edgecolor=None)

def plot_audiogram(audiometry, fig=None, banana=None):
    '''
    Plot the audiogram given an audiometry dict() from parse_audiometry
    Input:
        audiometry [dict] : generate this from the function parse_audiometry()
        fig [handle] : figure handle, if you want to plot to the same figure or axis. 
                       If none, creates a new figure.
        banana [str] : Choose from [None, 'Left', 'Right', 'Both']. If None, not shown. 
                       If 'Left', 'Right', or 'Both' the "speech banana" is shown in
                       blue, red, or gray, respectively.

    '''
    if fig is None:
        fig=plt.figure()
    if banana:
        plot_speechbanana('Both')
    plt.plot(audiometry['Left'].keys(), audiometry['Left'].values(),'x', color='b')
    plt.plot(audiometry['Right'].keys(), audiometry['Right'].values(), 'o', fillstyle='none', color='r')
    plt.gca().set_xscale('log')
    plt.gca().axis([100, 10000, -10, 120])
    plt.gca().set_xticks([125,250,500,1000,2000,4000,8000])
    plt.gca().set_xticklabels([125,250,500,1000,2000,4000,8000])
    plt.grid()
    plt.ylabel('dB HL')
    plt.xlabel('Frequency (Hz)')
    plt.gca().invert_yaxis()


def main(audiometry_dir):
    '''
    Create a figure with all of the pure tone audiometry results for xml
    files within a directory [audiometry_dir]

    Inputs:
        audiometry_dir [str]: Path to your audiometry xml files
    '''
    #fig = plt.figure(1);
    plt.figure()
    files = glob.glob(f'{audiometry_dir}/*.xml')

    nrows = np.floor(np.sqrt(len(files)))
    ncols = np.ceil(len(files)/nrows)
    for fi, file in enumerate(files):
        subject = file.split('/')[-1].split('_')[0]
        fig = plt.subplot(nrows, ncols, fi+1)
        print(file)
        audiometry = parse_audiometry(file)
        plot_audiogram(audiometry, fig=fig, banana=True)
        plt.title(subject)
    plt.tight_layout()
    #plot_speechbanana('Both')
