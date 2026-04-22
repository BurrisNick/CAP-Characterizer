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