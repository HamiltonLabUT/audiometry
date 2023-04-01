# Written 2021 Liberty Hamilton
# University of Texas at Austin
#
# liberty.hamilton@austin.utexas.edu
#

import xml.etree.ElementTree as ET
from copy import copy
import re
import numpy as np
import matplotlib
matplotlib.rcParams['ps.fonttype'] = 42
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
    audiogram = dict()

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
                audiogram[earside] = {}  # initialize the dictionary
                # Find the number of tones that were played to this participant
                nfreqs = len(measured_data[s]['Tone'][0]['TonePoint'])
                # Loop through the tones and find the frequency and measured thresholds,
                # then save these to the audiogram dictionary for the relevant [earside]
                for tone in np.arange(nfreqs):
                    freq = int(measured_data[s]['Tone'][0]['TonePoint'][tone]['Frequency'][0]['_text'])
                    threshold = int(measured_data[s]['Tone'][0]['TonePoint'][tone]['IntensityUT'][0]['_text'])
                    audiogram[earside][freq] = threshold

    return audiogram


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


def plot_classification(fontsize='small'):
    levels = {'Normal': [-10,15,'#9d9bc1'],
            'Slight': [15,25,'#98aed0'],
            'Mild': [25,40,'#a5c3df'],
            'Moderate': [40,55,'#a8d1d9'],
            'Moderately Severe': [55,70,'#88c1cc'],
            'Severe': [70,90,'#7ab9b3'],
            'Profound': [90,120,'#79b7a4']}

    for severity in levels.keys():
        min_db = levels[severity][0]
        max_db = levels[severity][1]
        clr = levels[severity][2]
        plt.fill_between(x=[100,10000], y1=[min_db, min_db], y2=[max_db, max_db], color=clr, alpha=1.0)
        plt.text(100, max_db-5, severity, color='k', fontsize=fontsize)

def plot_audiogram(audiogram, fig=None, banana=None, classification=False):
    '''
    Plot the audiogram given an audiogram dict() from parse_audiometry
    Input:
        audiogram [dict] : generate this from the function parse_audiometry(). Can be a 
                           single dictionary or a list of dictionaries, each from parse_audiometry()
        fig [handle] : figure handle, if you want to plot to the same figure or axis. 
                       If none, creates a new figure.
        banana [str] : Choose from [None, 'Left', 'Right', 'Both']. If None, not shown. 
                       If 'Left', 'Right', or 'Both' the "speech banana" is shown in
                       blue, red, or gray, respectively.
        classification [bool] : True/False, Whether to plot classification of hearing levels
                                e.g. Normal, Slight, Mild, Moderate, Moderately Severe,
                                Severe, and Profound.

    '''
    if fig is None:
        fig=plt.figure()
    if classification:
        plot_classification()
    if banana:
        plot_speechbanana('Both')

    if type(audiogram) == dict:
        plt.plot(audiogram['Left'].keys(), audiogram['Left'].values(), 'x-', color='b', label='Left')
        plt.plot(audiogram['Right'].keys(), audiogram['Right'].values(), 'o-', fillstyle='none', color='r', label='Right')
    
    elif type(audiogram) == list:
        print("Plotting average audiograms")
        x_left=audiogram[0]['Left'].keys()
        x_right=audiogram[0]['Right'].keys()
        y_left, y_right = [], []
        for n in np.arange(len(audiogram)):
            y_left.append(list(audiogram[n]['Left'].values()))
            y_right.append(list(audiogram[n]['Right'].values()))
        y_left = np.array(y_left)
        y_right = np.array(y_right)
        y_left_mean = y_left.mean(0)
        y_right_mean = y_right.mean(0)
        y_left_stderr = y_left.std(0)/np.sqrt(y_left.shape[0])
        y_right_stderr = y_right.std(0)/np.sqrt(y_right.shape[0])

        plt.fill_between(x_left, y_left_mean+y_left_stderr, y_left_mean-y_left_stderr, color='b', alpha=0.5)
        plt.plot(x_left, y_left_mean, 'x-', color='b', label='Left')
        plt.fill_between(x_right, y_right_mean+y_right_stderr, y_right_mean-y_right_stderr, color='r', alpha=0.5)
        plt.plot(x_right, y_right_mean, 'o-', fillstyle='none', color='r', label='Right')
        
    plt.gca().set_xscale('log')
    plt.gca().axis([100, 10000, -10, 120])
    plt.gca().set_xticks([125,250,500,1000,2000,4000,8000])
    plt.gca().set_xticklabels([125,250,500,1000,2000,4000,8000])
    plt.grid()
    plt.ylabel('dB HL')
    plt.xlabel('Frequency (Hz)')
    plt.gca().invert_yaxis()
    plt.legend(loc='lower right')


def main(audiometry_dir, banana='Both', classification=True, average=True, figname=None, title=''):
    '''
    Create a figure with all of the pure tone audiometry results for xml
    files within a directory [audiometry_dir]

    Inputs:
        audiometry_dir [str]: Path to your audiometry xml files
        banana [None,'Left','Right', or 'Both'] : whether to plot speech banana
        classification [bool] : True/False, whether to show hearing classification.
    '''

    files = glob.glob(f'{audiometry_dir}/*.xml')

    nrows = int(np.floor(np.sqrt(len(files))))
    ncols = int(np.ceil(len(files)/nrows))
    audiograms = []
    for fi, file in enumerate(files):
        subject = file.split('/')[-1].split('_')[0]
        print(file)
        audiogram = parse_audiometry(file)
        if average == False:
            fig = plt.subplot(nrows, ncols, fi+1)
            plot_audiogram(audiogram, fig=fig, banana=banana, classification=classification)
            plt.title(subject)
        audiograms.append(audiogram)
    if average:
        fig = plt.figure()
        plot_audiogram(audiograms, fig=fig, banana=banana, classification=classification)
        if title == '':
            title = 'Average audiogram'
        plt.title(title)

    plt.tight_layout()
    if figname:
        plt.savefig(f'{audiometry_dir}/{figname}')
        
    plt.show()
    return audiograms
