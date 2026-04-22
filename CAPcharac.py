import ObjectInterface_OE as OI
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from scipy import signal
from scipy.signal import find_peaks

def CAPcharac(dataPath):
    data = pd.read_csv(dataPath)

    # booooooo

    time = data['x-axis']
    eng = data['1']
    pulse = data['2']
    #deletes row of headers
    time.pop(0)
    eng.pop(0)
    pulse.pop(0)

    #converts any strings to number 
    time = pd.to_numeric(time)
    eng = pd.to_numeric(eng)
    pulse = pd.to_numeric(pulse)

    #calculates sampling rate 
    sr = int(len(time) / (abs(np.min(time)) + abs(np.max(time))))


    dist = sr*0.005 #minimum distance between APs

    eng1 = eng
    pulse1 = pulse
    #applies rolling average to minimize noise 
    eng1 = eng.rolling(window=7, center=True).mean()
    eng1 = eng1.rolling(window=7, center=True).mean()
    eng1 = eng1.rolling(window=7, center=True).mean()
    dataMax = np.max(eng1)

    ENGpeaks, props = find_peaks(eng1, height=(dataMax / 3), distance=dist, rel_height=0.5, width=0)

    if len(ENGpeaks) == 0:
        return None

    hwidth = props['widths'] / sr * 1000

    timeENGPeak = time.iloc[ENGpeaks].values
    magPeak = eng1.iloc[ENGpeaks].values

    amplitude = magPeak[0]
    latency = timeENGPeak[0]
    halfwidth = hwidth[0]

    return amplitude, latency, halfwidth
