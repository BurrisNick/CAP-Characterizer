import numpy as np
from matplotlib import pyplot as plt
from CAPcharac import CAPcharac
from pathlib import Path
import pandas as pd

results = []

for file in Path("data").rglob("*.csv"):
    category = file.parent.name # determines what category of trials

    output = CAPcharac(file, category)

    if output is not None:

        amp, lat, hw = output

        results.append([category, file.name, amp, lat, hw])

df = pd.DataFrame(results, columns=["category", "file", "amplitude", "latency", "halfwidth"])
print(df)

# groups frog, nerve, and temp
df["frog"] = df["category"].str[0]
df["nerve"] = df["category"].str[1]
df["temp"] = df["category"].str[2:] 

stats = df.groupby("temp")["amplitude"].agg(["mean", "std"]).reset_index()
plt.errorbar(stats["temp"], stats["mean"], yerr=stats["std"])
plt.xlabel("Temperature")
plt.ylabel("Amplitude")
plt.title("Mean Amplitude by Temperature")
plt.show()

nerve_means = df.groupby(["frog", "nerve", "temp"])["amplitude"].mean().reset_index()
pivot = nerve_means.pivot_table(
    index=["frog", "nerve"],
    columns="temp",
    values="amplitude"
).reset_index()

for _, row in pivot.iterrows():
    plt.plot(["cold", "room"], [row["cold"], row["room"]], marker='o')

plt.xlabel("Temperature")
plt.ylabel("Amplitude")
plt.title("Paired Nerve Responses")
plt.show()