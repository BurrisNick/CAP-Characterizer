from CAPcharac import CAPcharac
from pathlib import Path
import pandas as pd

results = []

for file in Path("data").rglob("*.csv"):
    output = CAPcharac(file)

    if output is not None:
        amp, lat, hw = output
        results.append([file.name, amp, lat, hw])

df = pd.DataFrame(results, columns=["file", "amplitude", "latency", "halfwidth"])
print(df)