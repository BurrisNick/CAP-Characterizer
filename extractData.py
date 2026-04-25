import numpy as np
from matplotlib import pyplot as plt
from CAPcharac import CAPcharac
from pathlib import Path
from scipy.stats import ttest_rel
import pandas as pd
import seaborn as sns

results = []
trial = 0 #keep track of the which CSV we are in (DEBUG)
for file in Path("data").rglob("*.csv"):
    category = file.parent.name # determines what category of trials
    trial += 1
    output = CAPcharac(file, category, trial)

    if output is not None:

        amp, lat, hw = output

        results.append([category, file.name, amp, lat, hw])

df = pd.DataFrame(results, columns=["category", "file", "amplitude", "latency", "halfwidth"])
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
