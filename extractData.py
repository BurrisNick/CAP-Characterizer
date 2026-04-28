import numpy as np
from matplotlib import pyplot as plt
from CAPcharac import CAPcharac
from pathlib import Path
from scipy.stats import ttest_rel
import pandas as pd

results = []
trial = 0 #keep track of the which CSV we are in (DEBUG)
CDist = [0.02, 0.03] # conduction distance between stimilating electrode and the recording electrodes in mm
CDcold = 0.02 #m
CDroom = 0.03 #m
last = False #tells CAPcharac that its the last data set and to save all the neccissary figures

for file in Path("data").rglob("*.csv"):
    category = file.parent.name # determines what category of trials
    print("category is: ", category) # for debug


    output = CAPcharac(file, category)

    if output is not None:

        amp, lat, hw = output
        # 2 nerve trials had CD recorded, so we calculate CV to take into consideration distance of propagation for lat
        # units are mm / ms = m/s
        if category.endswith('cold'):
            CV = CDist[0]*1000 / lat #conduction velocity based on the latency and conduction distance recorded for frog 2 cold
        else:
            CV = CDist[1]*1000 / lat #conduction velocity based on the latency and conduction distance recorded for frog 2 room

        results.append([category, file.name, amp, lat, hw, CV])

print('Done going through data')
CAPcharac(-1, -1) # identify that we have ran through all the data and to save the last group figure

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
    mean_cv=("velocity", "mean"),
    sd_cv=("velocity", "std"),
    mean_hw=("halfwidth", "mean"),
    sd_hw=("halfwidth", "std"),
).reset_index()
print(summary)

# have each temp together by nerve 
pivot_amp = summary.pivot_table(
    index=["frog", "nerve"],
    columns="temp",
    values="mean_amp"
).reset_index()
pivot_amp = pivot_amp[["frog", "nerve", "cold", "room"]]
pivot_cv = summary.pivot_table(
    index=["frog", "nerve"],
    columns="temp",
    values="mean_cv"
).reset_index()
pivot_cv = pivot_cv[["frog", "nerve", "cold", "room"]]
pivot_hw = summary.pivot_table(
    index=["frog", "nerve"],
    columns="temp",
    values="mean_hw"
).reset_index()
pivot_hw = pivot_hw[["frog", "nerve", "cold", "room"]]

plt.figure(figsize=(5,4))

means = df.groupby("temp")["amplitude"].mean()
stds = df.groupby("temp")["amplitude"].std()
plt.bar(means.index, means.values, yerr=stds.values, capsize=5)
plt.title("Amplitude by Temperature")
plt.ylabel("Amplitude")
plt.show()

plt.figure(figsize=(5,4))
means = df.groupby("temp")["velocity"].mean()
stds = df.groupby("temp")["velocity"].std()
plt.bar(means.index, means.values, yerr=stds.values, capsize=5)
plt.title("Conduction Velocity by Temperature")
plt.ylabel("Velocity (m/s)")
plt.show()

plt.figure(figsize=(5,4))

means = df.groupby("temp")["halfwidth"].mean()
stds = df.groupby("temp")["halfwidth"].std()
plt.bar(means.index, means.values, yerr=stds.values, capsize=5)
plt.title("Half Width by Temperature")
plt.ylabel("Half Width")
plt.show()


# calculate average differences
pivot_amp["delta"] = pivot_amp["room"] - pivot_amp["cold"]
print(pivot_amp["delta"].mean(), pivot_amp["delta"].std())
pivot_cv["delta"] = pivot_cv["room"] - pivot_cv["cold"]
print(pivot_cv["delta"].mean(), pivot_cv["delta"].std())
pivot_hw["delta"] = pivot_hw["room"] - pivot_hw["cold"]
print(pivot_hw["delta"].mean(), pivot_hw["delta"].std())

t_stat, p_val = ttest_rel(pivot_amp["room"], pivot_amp["cold"])
print(t_stat, p_val)
damp = pivot_amp["delta"].mean() / pivot_amp["delta"].std()
print("Cohen's d:", damp)

t_stat, p_val = ttest_rel(pivot_cv["room"], pivot_cv["cold"])
print(t_stat, p_val)
dlat = pivot_cv["delta"].mean() / pivot_cv["delta"].std()
print("Cohen's d:", dlat)

t_stat, p_val = ttest_rel(pivot_hw["room"], pivot_hw["cold"])
print(t_stat, p_val)
dhw = pivot_hw["delta"].mean() / pivot_hw["delta"].std()
print("Cohen's d:", dhw)
