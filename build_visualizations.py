"""
Visualizing Data
The charts are used to explore how flight prices vary across airlines, routes, booking time, number of stops, and other
numeric factors.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

CLEAN_PATH = "data/flight_price_clean.csv"
PLOTS_DIR = Path("plots")
PLOTS_DIR.mkdir(exist_ok=True)

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 110

df = pd.read_csv(CLEAN_PATH)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / f"{name}.png")
    plt.close(fig)
    print(f"Saved plots/{name}.png")


# 1. Price distribution
fig, ax = plt.subplots(figsize=(8, 5))
sns.histplot(df["Price"], bins=50, kde=True, color="#4C72B0", ax=ax)

ax.set_title("Distribution of Flight Prices")
ax.set_xlabel("Price (Rs)")
save(fig, "01_price_distribution")

 
# 2. Price vs. days before departure

lead = df.groupby("Days_Before_Departure")["Price"].mean().sort_index()
lead_smooth = lead.rolling(5, min_periods=1, center=True).mean()
 
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(lead.index, lead.values, alpha=0.25, color="#4C72B0", label="Daily average")
ax.plot(lead_smooth.index, lead_smooth.values, color="#C44E52", lw=2.5,label="5-day rolling average")

ax.set_title("Average Price vs. Days Before Departure")
ax.set_xlabel("Days Before Departure")
ax.set_ylabel("Average Price (Rs)")
ax.legend()
save(fig, "02_price_vs_days_before_departure")
print(f"Correlation (Days_Before_Departure vs Price): "
      f"{df['Days_Before_Departure'].corr(df['Price']):.3f}\n")

 
# 3. Price by travel class

fig, ax = plt.subplots(figsize=(7, 5))
class_order = df.groupby("Travel_Class")["Price"].mean().sort_values().index
sns.violinplot(data=df, x="Travel_Class", y="Price", order=class_order,hue="Travel_Class", legend=False, palette="Set2", ax=ax)

ax.set_title("Price Distribution by Travel Class")
ax.set_xlabel("")
ax.set_ylabel("Price (Rs)")
save(fig, "03_price_by_class")
print(df.groupby("Travel_Class")["Price"].mean().round(0).sort_values(), "\n")


# 4. Price vs. number of stops
fig, ax = plt.subplots(figsize=(7, 5))
sns.boxplot(data=df, x="Total_Stops", y="Price", ax=ax, showfliers=False, color="#C44E52")
ax.set_title("Price vs. Number of Stops")
ax.set_xlabel("Total stops")
save(fig,"04_price_v_stops")


# 5. Price by route (top 10 busiest routes)
df["Route"] = df["Source"] + " → " + df["Destination"]
top_routes = df["Route"].value_counts().head(10).index
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(
    data=df[df["Route"].isin(top_routes)],
    x="Price", y="Route", ax=ax, showfliers=False,
    order=df.groupby("Route")["Price"].median().loc[top_routes].sort_values().index,
)
ax.set_title("Price by Route (top 10 busiest routes)")
save(fig,"05_price_by_route")

 
# 6. Price by Days of Week
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_avg = df.groupby("Weekday")["Price"].mean().reindex(weekday_order)
colors = ["#C44E52" if v == weekday_avg.max() else
          "#55A868" if v == weekday_avg.min() else "#4C72B0" for v in weekday_avg.values]
 
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(weekday_avg.index, weekday_avg.values, color=colors)
ax.set_title("Average Price by Day of Week (Min = green, Max = red)")
ax.set_ylabel("Avg Price (Rs)")
plt.xticks(rotation=30)
save(fig, "06_price_by_weekday")
print(weekday_avg.round(0), "\n")


# 7. Airline and Travel Class heatmap
fig, ax = plt.subplots(figsize=(9, 7))
pivot = df.pivot_table(index="Airline", columns="Travel_Class", values="Price", aggfunc="mean")
pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="rocket_r", ax=ax,cbar_kws={"label": "Avg Price (Rs)"})

ax.set_title("Average Price: Airline x Travel Class")
ax.set_xlabel("")
ax.set_ylabel("")
save(fig, "07_airline_class_heatmap")


# 8. Top 10 / bottom 10 routes
route_avg = df.groupby("Route")["Price"].mean()
route_counts = df.groupby("Route")["Price"].count()
route_avg = route_avg[route_counts >= 20]  # ignore noisy low-volume routes
 
top10 = route_avg.sort_values(ascending=False).head(10)
bottom10 = route_avg.sort_values().head(10)
 
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
sns.barplot(x=top10.values, y=top10.index, hue=top10.index, palette="rocket",legend=False, ax=axes[0])
axes[0].set_title("10 Most Expensive Routes")
axes[0].set_xlabel("Avg Price (Rs)")
 
sns.barplot(x=bottom10.values, y=bottom10.index, hue=bottom10.index, palette="crest",legend=False, ax=axes[1])
axes[1].set_title("10 Cheapest Routes")
axes[1].set_xlabel("Avg Price (Rs)")
save(fig, "08_top_bottom_routes")


 
# 9. Correlation Heatmap
numeric_cols = ["Price", "Distance_km", "Duration_Minutes", "Days_Before_Departure","Passenger_Count", "Total_Stops"]
corr = df[numeric_cols].corr()

fig, ax = plt.subplots(figsize=(10, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax,cbar_kws={"label": "Correlation"})
ax.set_title("Correlation Heatmap")
save(fig, "09_correlation_heatmap")
 
print("=" * 50)
print("PRICE CORRELATIONS, RANKED:")
print(corr["Price"].drop("Price").abs().sort_values(ascending=False))
