########################################################################################################################
# This script contains all the neccessary python functions for expierments and data transfer for the object interface
# plugin. includes data analysis helpers for experiments ran with the custom plug in as well as general ephys data anylsis,
# file converters, file locators for files not stored locally, and plug in control functions.
# created 8/1/25
# last edit 3/12/26
########################################################################################################################
# from open_ephys.analysis import Session
import soundfile as sf
import numpy as np
import os
import matplotlib.pyplot as plt
import requests
import time
import json
from datetime import datetime
from open_ephys.analysis import Session
import scipy.io as sio

 ########################################################################################################################
# library variable initiation
########################################################################################################################
configTimeout = 0.5
timeStop = 0.1


def getDataOE(DataPath, expDate ,wavFile):
    """
    gets the data files from open-ephys. data must be aquired by OE for this file format.
    You must know the path of the recorded open ephys data. change the data path in this function
    to match your own file structure.

    inputs: :param expDate: date recorded of open ephys/experiment name in OE file structure
            :param wavFile: the wave file name from the specific experiment of interest.
    outputs: data: the data array of the experiment. (LFP, channels)
            sr: the sample rate that was used to aquire the data
            path: the full path name of the file with data
    date modified: 3/12/26
    """
    #must set based on your own personal computer data structure
    dash = "/"

    path = DataPath + dash + expDate + dash + wavFile  # generate the full path from the pieces
    print(f"{path}")
    print(f"does the path exist?   {os.path.exists(path)}")

    while not os.path.exists(path):
        print("path does not exist! \nCheck data path location, experiment date, .wav file name")
        expDate = input("expDate:  ")
        wavFile = input("waveFile name:  ")
        path = DataPath + dash + expDate + dash + wavFile  # generate the full path from the pieces

    # read the data and gather metadata
    data, sr = sf.read(path)
    numChan = np.shape(data)[1]
    return data, sr, numChan, path

def bin_to_wav(directory, experimentName):
    """
    # convert the binary recorded data from the OE record node plugin and export it as a .wav file in the same
    # directory. also saves the metadata in Json format under a directory,experimentName, Meta.txt
    # parameters. will convert all ephys data files to .wav in the directory. makes a seperate file, does not replace
    original files.
    #   :param directory: the file directory that the record node is saving the binary data to
    #   :param experimentName: the name you give the experiment -> will be the title of your file

   """
    session = Session(directory)  # gets the data being used

    for rn_idx, record_node in enumerate(session.recordnodes):
        print(f"RecordNode {rn_idx}")
        recording = record_node.recordings
        print(f"{record_node} WITH {recording}")
        for rec_ind in range(len(recording)):

            continuous = recording[rec_ind].continuous[0]  # Assuming first analog input stream (RhythmFPGA)
            data = continuous.samples  # shape: (16, n_samples)
            metadata = continuous.metadata
            print(metadata)

            # uncomment section if you want more details on metadata
            sourceNodeID = metadata.source_node_id
            sourceNodeName = metadata.source_node_name
            streamName = metadata.stream_name
            numAIChannel = metadata.num_channels
            channelNames = metadata.channel_names
            bitVolts = metadata.bit_volts
            SR = metadata.sample_rate  # sample rate

            data = data.astype(np.float32)
            # data /= np.max(np.abs(data))  # normalize per session
            wav_data = data * bitVolts  # scale the data from record node binary operations

            output_path = os.path.join(directory, f"{experimentName}_rn{rec_ind}.wav")
            sf.write(output_path, wav_data, int(SR), subtype='FLOAT')

            #file_name = f"{experimentName}_{numAIChannel}ch_Meta.txt"  # You can use .json or .txt extension
            txtFilePath = os.path.join(directory, f"{experimentName}_rn{rec_ind}_Meta.txt")
            with open(txtFilePath, "w") as file:
                json.dump(metadata.__dict__, file, indent=4)  # indent=4 makes the JSON human-readable




def send_config(command, ID):
    """
    # sends a configure message to the plugin if your using local host
    # parameters
    #   :param command: the config command to send
    #   :param ID: processor ID to recieve the message
    """
    url = f"http://localhost:37497/api/processors/{ID}/config"
    payload = {"text": json.dumps(command)}
    try:
        r = requests.put(url, json=payload, timeout=configTimeout)
        r.raise_for_status()
        return r  # return full response object
    except Exception as e:
        print(f"Failed to send {command}: {e}")
        return False

def startAquisition():
    """
    # sends a message to local URL to start aquisition of the OE GUI
    """
    r = requests.put(
        "http://localhost:37497/api/status",
        json={"mode": "ACQUIRE"})

def stopAquisition():
    """
    # sends a message to local URL to Stop aquisition of the OE GUI
    """
    r = requests.put(
        "http://localhost:37497/api/status",
        json={"mode": "IDLE"})

def startRecording():
    """
    # sends a message to local URL to start recording the data being aquired
    """
    r = requests.put(
        "http://localhost:37497/api/status",
        json={"mode": "RECORD"})


def stopRecording():
    """
    # sends a message to local URL to stop aquisition of but keep recording on
"""
    r = requests.put(
        "http://localhost:37497/api/status",
        json={"mode": "ACQUIRE"})


def setValue(field, value, ID):
    """
    # sets the value of a parameter in the Plug-in
    # parameters
    #   :param field: the parameter to change
    #   :param value: the value to set to the parameter
    #   :param ID: processor ID to recieve the message
    """

    m2sSet = {"command": "set", "field": field, "value": value}
    while not send_config(m2sSet, ID):
        time.sleep(timeStop)


def getValue(field, ID):
    """
    # gets the value of a parameter in the Plug-in
    # parameters
    #   :param field: the parameter to get the value of
    #   :param ID: processor ID to recieve the message
    #
    # outputs
    #   value: value of the parameter
    """
    m2sSet = {"command": "get", "field": field}

    while True:
        response = send_config(m2sSet, ID)
        if response is not None:
            try:
                data = response.json()
                if "info" in data:
                    inner_json = json.loads(data["info"])
                    print(f"data variable: {inner_json}")
                    value = inner_json.get(field)
                    print(f"{field}: {value}")
                    return value
                else:
                    print("No 'info' field in response")

                return value
            except Exception as e:
                print(f"Failed to parse response: {e}")

            time.sleep(timeStop)


def logValue(field, ID, experiment, directory):
    """
    # gets the value of a parameter in the Plug-in
    # parameters
    #   :param field: the parameter to get the value of
    #   :param  ID: processor ID to recieve the message
    #   :param experiment: identification for experiment to match data
    #   :param directory: directory that you want to log th value
    #
    # outputs
    #   value: value of the parameter
    """
    x = getValue(field, ID)

    txtFilePath = os.path.join(directory, f"{experiment}_Parameters.txt")
    with open(txtFilePath, 'a') as f:
        print(f"{field}: {x}    timestamp: {datetime.now().time()}", file=f)


def saveAllValues(ID, experiment, directory):
    """
    # saves the value of all the parameters in object interface
    # parameters
    #   :param ID: processor ID to receive the message
    #   :param experiment: identification for experiment to match data
    #   :param directory: directory that you want to log th value
    #
    # outputs
    #   :return value: value of the parameter
    """

    amp1 = getValue("amp1", ID)
    amp2 = getValue("amp2", ID)
    phase1 = getValue("phase1", ID)
    phase2 = getValue("phase2", ID)
    pulseamp1 = getValue("pulse amp1", ID)
    pulseamp2 = getValue("pulse amp2", ID)
    pulsephase1 = getValue("pulse phase1", ID)
    pulsephase2 = getValue("pulse phase2", ID)
    pulsewidth1 = getValue("pulse width1", ID)
    pulsewidth2 = getValue("pulse width2", ID)
    pulsenwidth1 = getValue("pulse nwidth1", ID)
    pulsenwidth2 = getValue("pulse nwidth2", ID)
    numberpulse1 = getValue("number pulse1", ID)
    numberpulse2 = getValue("number pulse2", ID)
    numberwaves = getValue("number waves", ID)

    txtFilePath = os.path.join(directory, f"{experiment}_Parameters.txt")

    with open(txtFilePath, 'a') as f:
        print(f"====================================================", file=f)
        print(f"parameters from experiment {experiment}", file=f)
        print(f"Time-Stamp: format UNIX: {time.time()}", file=f)
        print(f"            format H:M:S {datetime.now().time()}", file=f)
        print(f"====================================================", file=f)
        print(f"LFAC amp 1 : {amp1}", file=f)
        print(f"LFAC amp 2 : {amp2}", file=f)
        print(f"LFAC phase 1 : {phase1}", file=f)
        print(f"LFAC phase 2 : {phase2}", file=f)
        print(f"Pulse amp 1 : {pulseamp1}", file=f)
        print(f"Pulse amp 2 : {pulseamp2}", file=f)
        print(f"Pulse phase 1 : {pulsephase1}", file=f)
        print(f"Pulse phase 2 : {pulsephase2}", file=f)
        print(f"Pulse width 1 : {pulsewidth1}", file=f)
        print(f"Pulse width 2 : {pulsewidth2}", file=f)
        print(f"Interpulse delay 1 : {pulsenwidth1}", file=f)
        print(f"Interpulse delay 2 : {pulsenwidth2}", file=f)
        print(f"Number of pulses 1 : {numberpulse1}", file=f)
        print(f"Number of pulses 2 : {numberpulse2}", file=f)
        print(f"number of waves : {numberwaves}", file=f)
        print(f"====================================================",file=f)
        print(f"\n")


def startWaveGen(ID):
    """
    # sends a configure message to the plug-in to activate stimulation
    #   parameters
    #   :param ID: processor ID to recieve the message
    """

    m2sSet = {"command": "start"}
    while not send_config(m2sSet, ID):
        time.sleep(timeStop)


def stopWaveGen(ID):
    """
    # sends a configure message to the plug-in to stop stimulation
    #   parameters
    #   :param ID: processor ID to recieve the message
    """
    m2sSet = {"command": "stop"}
    while not send_config(m2sSet, ID):
        time.sleep(timeStop)


def tbf(functions):
    """
    # returns the time between functions that will need to be subtracted from sleep times
    #   parameters
    #   :param functions: number of functions the tbf will calculate for
    #
    #   returns
    #   :return t: the time between functions
    """

    t = (timeStop + configTimeout) * functions
    return t

def AverageData(data, sr, on, off=0, channel=0, startSamp=0, freq=1, preStimTime=5, postStimTime=30, plots=False):
    """
    averages a section of data gathered by basic pulses for a specific time period.
    over the number of pulse periods
    inputs:
        :param data: the .wav data from exp
        :param on: the time the stimulator was on (seconds)
        :param off: the time the stimulator was off (seconds)
        :param channel: the recorded channel of interest
        :param startSamp: sample to start at, good for arbitrary data anlysis
        :param freq: the frequency of the pulse cycle (Hz)
        :param preStimTime: time before stimulus artifact to display (ms) (currently does nothing)
        :param postStimTime: time after stimulus artifact to display (ms)
        :param plots: Bool -> True plots the averaged data, False does not plot the data allows for own plot mech
    outputs:
        :return dataAv: averaged data blocks
        :return graphs when plots=True: outputs a visual plot of the averaged data overlayed on the raw data
    """

    slicedData = []
    choppedData = []

    if data.ndim == 1:
        data = np.expand_dims(data, axis=1)


    print(np.shape(data)[1])

    onSamps = int(on * sr)
    offSamps = int(off * sr)
    numPulses = int(on*freq)
    postStimTimeSamps = int(postStimTime*sr / 1000) #(ms)
    preStimTimeSamps = int(preStimTime*sr / 1000) #(ms)
    sampsBetweenPulses = int(sr / freq)


    for ind in range(np.shape(data)[1]):
        slicedData.append(data[startSamp:(startSamp + onSamps), ind])

    slicedData = np.array(slicedData).T  #numpy array transposes python lists. transpose back
    knd = 0
    for ind in range(numPulses):
        knd = int(ind * sampsBetweenPulses)
        choppedData.append(slicedData[knd: (knd + postStimTimeSamps), channel])

    avData = np.mean(choppedData, axis=0)

    if plots is True:
        timevec = np.arange(0, len(avData), 1) / sr * 1000

        plt.plot(timevec, np.array(choppedData).T, 'b',lw=0.5) # all data in averaged block
        plt.plot(timevec, avData, 'k',lw=2.0, label='averaged') #average data
        plt.title(f"Channel: {channel} Averaged Data Over {on} With {numPulses} Pulses")
        plt.xlabel(f"Time (ms)")
        plt.ylabel(f"Magnitude (V)")
        plt.legend()

        plt.show()

    return avData


def dataVis(data, channels=[], sr=1,timeVec=[], channelNames=None, extraInfo='',yAxisTitle='', saveFig=False):
    '''
    visualizes data of all channels on a subplot with axis linked for easy data analysis
    :param data: data matrix containing all channels of data
    :param channels: channels you want to plot
    :param sr: the sample rate of aquisition
    :return: NONE
    '''

    lw = 1
    ind = 1
    ax = []

    if channels == []:
        channums = data.shape[1]
        print("\n channel shape: ",channums)

        for chans in range(channums):
            channels.append(chans)
        print("\nchannels: ",channels)

    if channelNames is None:
        channelNames = channels



    for chan in channels:
        ax.append('ax' + f'{ind}')
        ind += 1

    fig, ax = plt.subplots(len(ax), 1, sharex=True)  # 1 row, 2 columns

    if len(timeVec) == 0:
        timevec = np.arange(0, len(data), 1) / sr * 1000
    else:
        timevec = timeVec

    fig.suptitle(f'Ephys Data: {extraInfo}', fontsize=12)  #

    ind = 0
    for chan in channels:

        ax[ind].plot(timevec, data[:, chan-1], lw=lw)
        ax[ind].set_ylabel(f"{channelNames[ind]}")

        ind += 1

    plt.tight_layout()
    if yAxisTitle == '':
        plt.xlabel(f" Time (ms)")
    else:
        plt.xlabel(f"{yAxisTitle}")

    if saveFig is not True:
        plt.show()

#################################################################################################
# data analysis for ephys experiments: there are OE specific and ANC specific files.
#################################################################################################

def chargeDurationAnalysis():
    """
    analze data gathered from the ANC stimulation algorithm. this data will soon be collected by
    the LFAC generator plug-in.
    """


def getDataCD(DataPath, expName, trial):
    """
    gets data loaded from matlab files
    :param DataPath the main data folder path, will hold
    :param expName name of the experiment folder containing data
    :param trial specific trial or mat file you are wanting to extract
    :return: data: all of the contents of the .mat file as a dictionary and variable names as keys
    """

    dash = "/"

    path = DataPath + dash + expName + dash + trial  # generate the full path from the pieces
    print(f"{path}")
    print(f"does the path exist?   {os.path.exists(path)}")

    while not os.path.exists(path):
        print("path does not exist! \nCheck data path location and trial name")
        DataPath = input("DataPath:  ")
        expName = input("expDate:  ")
        trial = input("Trial name:  ")
        path = DataPath + dash + expName + dash + trial  # generate the full path from the pieces

    data = sio.loadmat(path)
    return data
