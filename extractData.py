from CAPcharac import CAPcharac
from pathlib import Path
import pandas as pd

results = []

for file in Path("data").rglob("*.csv"):
    output = CAPcharac(file)

    if output is not None:
        amp, lat, hw = output

        category = file.parent.name

        results.append([category, file.name, amp, lat, hw])

df = pd.DataFrame(results, columns=["category", "file", "amplitude", "latency", "halfwidth"])
print(df)