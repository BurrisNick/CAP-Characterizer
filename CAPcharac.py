import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from scipy import signal
from scipy.signal import find_peaks
from pathlib import Path

currentCat = '' # used to see if current catergory is changed
prevCat = '' # the previous category after a change is detected
changedCat = False # true if a change is detected
first = True #checks to see if this is the first time the function has ran
individualFig = plt.figure() # figure attribute for the plotter that saves each scope CSV with Peak detection
categoryFig = plt.figure() #combination of all data traces for a specific category


def CAPcharac(dataPath, category):
    """
    calculates the amplitude, latency and half width of each action potential detected. capable of detected switched
    channels IOs and switched bipolar recording leads based on polarity of the CSV data trace
    Args:
        dataPath: name of a CSV in parent folder.
        category: the name of the category of trails

    Returns:
        tuple: A tuple containing:
            - amplitude: The detected peak's maximum magnitude of the first action potential (A-Fiber)
            - latency: when the detected peak's maximum magnitude occurs
            - halfwidth: the half width of the detected peak


    """
    # bring in global variables
    global currentCat
    global individualFig
    global categoryFig
    global prevCat
    global changedCat
    global first

    if first: #determines if this is the first function call - initiates the global currentCat
        currentCat = category
        first = False
    elif currentCat is not category:    # deteremines if the category has changed

        changedCat = True
        currentCat = category
    else: # case for above ifs are not true
        prevCat = category
        changedCat = False

    data = pd.read_csv(dataPath) #get the csv data

    time = data['x-axis']# time axis of the data
    eng = data['1'] #the eng recorded data
    pulse = data['2'] # the data from the pulse cahnnel
    #deletes row of headers
    time.pop(0)
    eng.pop(0)
    pulse.pop(0)

    #converts any strings to number 
    time = pd.to_numeric(time) *1000 #turn time into ms base
    eng = pd.to_numeric(eng)
    pulse = pd.to_numeric(pulse)

    #calculates sampling rate 
    sr = int(len(time) / (abs(np.min(time)) + abs(np.max(time))))

    dist = sr*1000*0.005 #minimum distance between APs based on physiology

    eng -= np.mean(eng[0:30]) #gets rid of DC offset
    pulse -= np.mean(pulse[0:30]) #get rid of DC offset

    pulse1 = pulse
    #applies rolling average to minimize noise 
    eng1 = eng.rolling(window=7, center=True).mean()
    eng1 = eng1.rolling(window=7, center=True).mean()
    eng1 = eng1.rolling(window=7, center=True).mean()

    #get the max data sets for active thresholding
    engMax = np.max(abs(eng1))
    pulseMax = np.max(abs(pulse))

    ENGpeaks, props = find_peaks(eng1, height=(engMax / 3), distance=dist, rel_height=0.5, width=0) #detect the peaks in the dataset

    #check if inverted
    # checks if there were any peaks detected, if not invert the graph and see if there are peaks negative.
    # checks if the first peak is the stimulus artifact by checking its latency, stim artifact is negative polarity compared to CAPs.
    if len(ENGpeaks) == 0 or time[ENGpeaks[0]] < 2.8: #checks if there were any peaks detected, if not invert the graph
        print("inverted electrodes")
        eng = -eng
        eng1 = -eng1
        ENGpeaks, props = find_peaks(eng1, height=(engMax / 3), distance=dist, rel_height=0.5, width=0) #refind peaks

    # check if electrodes were plugged into a different channel
    # if the peaks are significantly less than the stimulus artifact that would tell us the stimulus artifcat is present
    # on the wrong channel and they need to be swapped.
    if ENGpeaks.any() < pulseMax/2:
        #swap the channels
        print("wrong channels")
        eng1 = pulse1
        pulse1 = eng #original unfiltered data
        eng = eng1

        #re-smooth the data
        eng1 = eng1.rolling(window=7, center=True).mean()
        eng1 = eng1.rolling(window=7, center=True).mean()
        eng1 = eng1.rolling(window=7, center=True).mean()

        engMax = np.max(eng1) #recalc the max

        ENGpeaks, props = find_peaks(eng1, height=(engMax / 3), distance=dist, rel_height=0.5, width=0)

        # check if inverted again
        if len(ENGpeaks) == 0 or time[ENGpeaks[0]] < 2.8:
            print("inverted electrodes")
            eng = -eng
            eng1 = -eng1
            ENGpeaks, props = find_peaks(eng1, height=(engMax / 3), distance=dist, rel_height=0.5, width=0)

    if len(ENGpeaks) == 0: #make sure there was a peak detected.
        return None

    hwidth = props['widths'] / sr #calculate the halfwidth in ms

    timeENGPeak = time.iloc[ENGpeaks].values
    magPeak = eng1.iloc[ENGpeaks].values

    amplitude = magPeak[0] #save the first peak for statistical analysis
    latency = timeENGPeak[0]
    halfwidth = hwidth[0]

    ##################################################
    # plotting the pulse and ENG along with the raw data

    plt.figure(individualFig.number) #select the figure to plot on
    plt.clf()
    plt.plot(time, eng, label=f'Raw', color= 'grey', lw=0.5)
    plt.plot(time, eng1, label='eng1', color= 'k', lw=1)
    plt.plot(time, pulse1,label='pulse1', color= 'r',lw=1)
    plt.plot(timeENGPeak[:2], magPeak[:2], 'o', color= 'b')

    if magPeak.shape[0] > 1:
       titleText = f'{category}'\
                   f'AP mag 1: {magPeak[0] * 1000:.1f}mV, mag 2: {magPeak[1] * 1000:.1f}mV' \
                   f'\nLatency 1st: {timeENGPeak[0]:.1f}ms, 2nd {timeENGPeak[1]:.1f}ms' \
                   f'\nhalfwidth 1st: {hwidth[0]:.1f}ms, 2nd: {hwidth[1]:.1f}ms'
    else:
       titleText = f'{category}'\
                   f'AP mag: {magPeak[0] * 1000:.1f}mV' \
                   f'\nLatency: {timeENGPeak[0]:.1f}ms' \
                   f'\nhalfwidth: {hwidth[0]:.1f}ms'

    plt.title(titleText)
    plt.xlabel('time (ms)')
    plt.ylabel('magnitude (V)')
    plt.legend()

    if max(time) > 30:
        plt.xlim(min(time), 30)

    # saves every single figure individually
    plt.savefig(Path(__file__).parent / 'Figures' / f'{dataPath.stem}', dpi=300, bbox_inches='tight')
    plt.close(individualFig)



    # create annd saves figures for the previous category all plotted together, before the new category plots are made

    plt.figure(categoryFig.number)

    if changedCat is True:
        plt.title(f'{prevCat} ')
        plt.xlabel('time (ms)')
        plt.ylabel('magnitude (V)')
        plt.savefig(Path(__file__).parent / 'Figures' / f'{category}', dpi=300, bbox_inches='tight')
        plt.clf()
        plt.close(categoryFig)
        changedCat = False

    plt.plot(time, eng, label=f'Raw', color= 'grey', lw=0.5)
    plt.plot(time, eng1, label='eng1', color= 'k', lw=1)
    plt.plot(time, pulse1,label='pulse1', color= 'r',lw=1)
    plt.plot(timeENGPeak[:2], magPeak[:2], 'o', color= 'b')


    ####filtering data if we wanna mess with that
    # order = 3
    # band = [50, 3000]
    # print(sr)
    # sos = signal.butter(order,band, btype='bandpass', fs=sr, output='sos')
    # filtered_ekg = signal.sosfiltfilt(sos, eng)


    return amplitude, latency, halfwidth
