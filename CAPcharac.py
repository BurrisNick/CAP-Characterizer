import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from scipy import signal
from scipy.signal import find_peaks
from pathlib import Path

currentCat = ''
individualFig = plt.figure()
categoryFig = plt.figure()

def CAPcharac(dataPath, category):
    global currentCat
    global individualFig
    global categoryFig

    # deteremines if the category has changed
    if currentCat is not category:
        changedCat = True
        currentCat = category
    else:
        changedCat = False

    data = pd.read_csv(dataPath)

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
        plt.title(f'{category} ')
        plt.xlabel('time (ms)')
        plt.ylabel('magnitude (V)')
        plt.savefig(Path(__file__).parent / 'Figures' / f'{category}', dpi=300, bbox_inches='tight')
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
