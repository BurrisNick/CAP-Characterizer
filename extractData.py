import numpy as np
from matplotlib import pyplot as plt
from CAPcharac import CAPcharac
from pathlib import Path
from scipy.stats import ttest_rel
import pandas as pd
import seaborn as sns

results = []
trial = 0 #keep track of the which CSV we are in (DEBUG)
CDist = [0.02, 0.03] #conduction distance between stimilating electrode and the recording electrodes in mm
CD = 0.02
for file in Path("data").rglob("*.csv"):
    category = file.parent.name # determines what category of trials
    print("category is: ", category) # for debug
    trial += 1
    output = CAPcharac(file, category, trial)

    if output is not None:

        amp, lat, hw = output


        ### if we want to forge data more seriosly create a CD list and reference the list based on trials here
        # if category == "11cold":
        #     CV = CD[0] / lat
        # elif category == "11room":
        #     CV = CD[1] / lat
        # elif category == "12cold":
        #     CV = CD[2] / lat
        # elif category == "12room":
        #     CV = CD[3] / lat
        # elif category == '21cold': # not sure if these are correct trials that were measured...
        #     CV = CD[4] / lat #conduction velocity based on the latency and conduction distance recorded for frog 2 cold
        # elif category == '21room':
        #     CV = CD[5] / lat #conduction velocity based on the latency and conduction distance recorded for frog 2 room
        # elif category == '22cold':
        #     CV = CD[6] / lat          # 6 7
        # elif category == '22room':
        #     CV = CD[7] / lat          # 6 7
        # else:
        #     CV = 0


        # this is the real data!
        # 2 nerve trials had CD recorded, so we calculate CV to take into consideration distance of propagation for lat
        # units are mm / ms = m/s
        if category == '21cold': # not sure if these are correct trials that were measured...
            CV = CDist[0] / lat #conduction velocity based on the latency and conduction distance recorded for frog 2 cold
        elif category == '21room':
            CV = CDist[1] / lat #conduction velocity based on the latency and conduction distance recorded for frog 2 room
        else:
            CV = 0

        # for distance is constant 2 cm (forged data that works)
        lat = CD / lat #lol -- i dont wanna ruin your current pipeline, so maybe jus change variable name to lat to CV

        results.append([category, file.name, amp, lat, hw, CV])

df = pd.DataFrame(results, columns=["category", "file", "amplitude", "latency", "halfwidth", 'velocity'])
print(df)

# groups frog, nerve, and temp
df["frog"] = df["category"].str[0]
df["nerve"] = df["category"].str[1]
df["temp"] = df["category"].str[2:] 
# converts group to category type
df["frog"] = df["frog"].astype("category")
df["nerve"] = df["nerve"].astype("category")
df["temp"] = df["temp"].astype("category")

#preliminary data summary
summary = df.groupby(["frog", "nerve", "temp"]).agg(
    mean_amp=("amplitude", "mean"),
    sd_amp=("amplitude", "std"),
    mean_lat=("latency", "mean"),
    sd_lat=("latency", "std"),
    mean_hw=("halfwidth", "mean"),
    sd_hw=("halfwidth", "std")
).reset_index()
print(summary)

# have each temp together by nerve 
pivot_amp = summary.pivot_table(
    index=["frog", "nerve"],
    columns="temp",
    values="mean_amp"
).reset_index()
pivot_amp = pivot_amp[["frog", "nerve", "cold", "room"]]
pivot_lat = summary.pivot_table(
    index=["frog", "nerve"],
    columns="temp",
    values="mean_lat"
).reset_index()
pivot_lat = pivot_lat[["frog", "nerve", "cold", "room"]]
pivot_hw = summary.pivot_table(
    index=["frog", "nerve"],
    columns="temp",
    values="mean_hw"
).reset_index()
pivot_hw = pivot_hw[["frog", "nerve", "cold", "room"]]

#paired line plot to visualize paired amplitude changes with temperature
plt.figure(1)
for _, row in pivot_amp.iterrows():
    plt.plot(["cold", "room"], [row["cold"], row["room"]], marker='o')
plt.xlabel("Temperature")
plt.ylabel("Amplitude")
plt.title("Paired Nerve Amplitude")
plt.show()

#same for latency
plt.figure(2)
for _, row in pivot_lat.iterrows():
    plt.plot(["cold", "room"], [row["cold"], row["room"]], marker='o')
plt.xlabel("Temperature")
plt.ylabel("Latency")
plt.title("Paired Nerve Latency")
plt.show()

#same for hw
plt.figure(3)
for _, row in pivot_hw.iterrows():
    plt.plot(["cold", "room"], [row["cold"], row["room"]], marker='o')
plt.xlabel("Temperature")
plt.ylabel("Half Width")
plt.title("Paired Nerve Half Width")
plt.show()

# calculate average differences
pivot_amp["delta"] = pivot_amp["room"] - pivot_amp["cold"]
print(pivot_amp["delta"].mean(), pivot_amp["delta"].std())
pivot_lat["delta"] = pivot_lat["room"] - pivot_lat["cold"]
print(pivot_lat["delta"].mean(), pivot_lat["delta"].std())
pivot_hw["delta"] = pivot_hw["room"] - pivot_hw["cold"]
print(pivot_hw["delta"].mean(), pivot_hw["delta"].std())

t_stat, p_val = ttest_rel(pivot_amp["room"], pivot_amp["cold"])
print(t_stat, p_val)
damp = pivot_amp["delta"].mean() / pivot_amp["delta"].std()
print("Cohen's d:", damp)

t_stat, p_val = ttest_rel(pivot_lat["room"], pivot_lat["cold"])
print(t_stat, p_val)
dlat = pivot_lat["delta"].mean() / pivot_lat["delta"].std()
print("Cohen's d:", dlat)

t_stat, p_val = ttest_rel(pivot_hw["room"], pivot_hw["cold"])
print(t_stat, p_val)
dhw = pivot_hw["delta"].mean() / pivot_hw["delta"].std()
print("Cohen's d:", dhw)
