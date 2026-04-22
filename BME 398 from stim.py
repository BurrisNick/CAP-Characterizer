import ObjectInterface_OE as OI
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from scipy import signal
from scipy.signal import find_peaks
path = 'C:/Users/burri/OneDrive - purdue.edu/school/Junior/jr design/frog stim/cold'
file = '/scope_36.csv'
dataPath = path + file

data = pd.read_csv(dataPath)
print(data.shape)

time = data['x-axis']
eng = data['1']
pulse = data['2']

time.pop(0)*1000 #(ms)
eng.pop(0)
pulse.pop(0)

time = pd.to_numeric(time)
eng = pd.to_numeric(eng)
pulse = pd.to_numeric(pulse)

sr = int(len(time) / (abs(np.min(time)) + abs(np.max(time))))

dist = sr*0.005 #distance between APs


eng1 = eng
pulse1 = pulse
# soopa smooth
for i in range(12):
    eng1 = eng1.rolling(window=7).mean()

dataMax = np.max(eng1)

ENGpeaks, props = find_peaks(eng1, height=(dataMax / 3), distance=dist, rel_height=0.5, width=0)
pulsePeaks, _ = find_peaks(-pulse, height=np.max(pulse)/2,distance=dist)

hwidth = props['widths'] / sr * 1000

timeENGPeak = time.iloc[ENGpeaks].values
magPeak = eng1.iloc[ENGpeaks].values
# timePulsePeak = time.iloc[pulsePeaks].values
# print(timePulsePeak)



plt.plot(time,eng)
plt.plot(time,eng1)
plt.plot(time, pulse)
plt.plot(time, pulse1)
plt.plot(timeENGPeak, magPeak, 'o')

plt.title(f'AP mag 1: {magPeak[0]*1000:.1f}mV, mag 2: {magPeak[1]*1000:.1f}mV'
          f'\nLatency 1st: {timeENGPeak[0]*1000:.1f}ms, 2nd {timeENGPeak[1]*1000:.1f}ms'
          f'\nhalfwidth 1st: {hwidth[0]:.1f}ms, 2nd: {hwidth[1]:.1f}ms')
plt.xlabel('time (ms)')
plt.ylabel('magnitude (V)')
plt.show()

plt.show()




# order = 3
# band = [50, 3000]
# print(sr)
# sos = signal.butter(order,band, btype='bandpass', fs=sr, output='sos')
# filtered_ekg = signal.sosfiltfilt(sos, eng)

