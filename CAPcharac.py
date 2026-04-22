import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from scipy import signal
from scipy.signal import find_peaks

def CAPcharac(dataPath, category):
    data = pd.read_csv(dataPath)

    time = data['x-axis']
    eng = data['1']
    pulse = data['2']
    #deletes row of headers
    time.pop(0)
    eng.pop(0)
    pulse.pop(0)

    #converts any strings to number 
    time = pd.to_numeric(time) *1000
    eng = pd.to_numeric(eng)
    pulse = pd.to_numeric(pulse)

    #calculates sampling rate 
    sr = int(len(time) / (abs(np.min(time)) + abs(np.max(time))))


    dist = sr*1000*0.005 #minimum distance between APs

    eng -= np.mean(eng[0:30])
    pulse -= np.mean(pulse[0:30])

    pulse1 = pulse
    #applies rolling average to minimize noise 
    eng1 = eng.rolling(window=7, center=True).mean()
    eng1 = eng1.rolling(window=7, center=True).mean()
    eng1 = eng1.rolling(window=7, center=True).mean()
    dataMax = np.max(abs(eng1))

    ENGpeaks, props = find_peaks(eng1, height=(dataMax / 3), distance=dist, rel_height=0.5, width=0)

    #check if inverted
    if ENGpeaks is None:
        ENGpeaks, props = find_peaks(-eng1, height=(dataMax / 3), distance=dist, rel_height=0.5, width=0)

    if ENGpeaks.any() < 0.05:
        #swap the channels
        print("ahhhhhhhhhhhhhhhh")
        eng1 = pulse1
        pulse1 = eng

        eng1 = eng1.rolling(window=7, center=True).mean()
        eng1 = eng1.rolling(window=7, center=True).mean()
        eng1 = eng1.rolling(window=7, center=True).mean()
        dataMax = np.max(eng1)

        ENGpeaks, props = find_peaks(eng1, height=(dataMax / 3), distance=dist, rel_height=0.5, width=0)

    if len(ENGpeaks) == 0:
        return None

    hwidth = props['widths'] / sr

    timeENGPeak = time.iloc[ENGpeaks].values
    magPeak = eng1.iloc[ENGpeaks].values

    amplitude = magPeak[0]
    latency = timeENGPeak[0]
    halfwidth = hwidth[0]


    ###################################################
    ### plotting the pulse and ENG along with the raw data
    plt.plot(time, eng)
    plt.plot(time, eng1)
    plt.plot(time, pulse1)
    plt.plot(timeENGPeak, magPeak, 'o')

    if magPeak.shape[0] > 1:
        titleText = f'{category}'\
                    f'AP mag 1: {magPeak[0] * 1000:.1f}mV, mag 2: {magPeak[1] * 1000:.1f}mV' \
                    f'\nLatency 1st: {timeENGPeak[0]:.1f}ms, 2nd {timeENGPeak[1]:.1f}ms' \
                    f'\nhalfwidth 1st: {hwidth[0]:.1f}ms, 2nd: {hwidth[1]:.1f}ms'
    else:
        titleText = f'{category}'\
                    f'AP mag: {magPeak[0] * 1000:.1f}mV' \
                    f'\nLatency: {timeENGPeak[0] * 1000:.1f}ms' \
                    f'\nhalfwidth: {hwidth[0]:.1f}ms'

    plt.title(titleText)
    plt.xlabel('time (ms)')
    plt.ylabel('magnitude (V)')
    plt.show()

    plt.show()

    # order = 3
    # band = [50, 3000]
    # print(sr)
    # sos = signal.butter(order,band, btype='bandpass', fs=sr, output='sos')
    # filtered_ekg = signal.sosfiltfilt(sos, eng)


    # need to add function for second peak if detected.
    # use for loop for this
    # if magPeak.shape[0] > 1:
    #     avLatency = np.mean(latency[0])
    #     avAmps = np.mean(amplitude[0])
    #     avWidth = np.mean(halfwidth[0])
    # else:
    #     avLatency = np.mean(latency)
    #     avAmps = np.mean(amplitude)
    #     avWidth = np.mean(halfwidth)

    # print(f'average amplitude is: {avAmps * 1000: .2f}mV\n'
    #       f'average latency is: {avLatency * 1000: .2f}ms\n'
    #       f'average half width is: {avWidth:.2f}ms\n')

    return amplitude, latency, halfwidth
