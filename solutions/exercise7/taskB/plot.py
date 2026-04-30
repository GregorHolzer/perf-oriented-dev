import matplotlib.pyplot as plt
import pandas as pd

default_df = pd.read_csv("./DefaultAllocator.csv")

custom_df = pd.read_csv("./CustomAllocator.csv")

data = {
  "Default Allocator": default_df['wall_clock_s'].median(),
  "Custom Allocator": custom_df['wall_clock_s'].median()
}
print(data)

fig, ax = plt.subplots(figsize=(8, 5))