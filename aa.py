import pandas as pd
from scipy.special import factorial
import folium
import branca
file_path = "~/OneDrive/Documents/Palo_Alto_Final.csv"
df = pd.read_csv(file_path, low_memory=False)

df['Start_Datetime'] = pd.to_datetime(df['Start_Date'] + ' ' + df['Start Time'])
df = df.sort_values(by=['Address', 'Start_Datetime'])

stations_per_location = {
    "1213 Newell Rd": 3,
    "250 Hamilton Ave": 2,
    "275 Cambridge Ave": 4,
    "3700 Middlefield Rd": 3,
    "445 Bryant St": 6,
    "475 Cambridge Ave": 5,
    "520 Webster St": 3,
    "528 High St": 4
}

arrival_rates = {}
service_rates = {}
utilization = {}
queue_lengths = {}
p0_ = {}
average_wait_times = {}

def mmc_queue(λ, μ, c):
    if λ == 0 or μ == 0 or c == 0: return 0, 0, 0
    # intensity
    rho = λ / (c * μ)
    
    sum_ = sum((λ / μ) ** n / factorial(n) for n in range(c))
    # probabilty of 0 cars being there
    p0 = 1 / (sum_ + ((λ / μ) ** c / (factorial(c) * (1 - rho))) if rho < 1 else float('inf'))
    
    if rho < 1:
        # queue length
        lq = (p0 * ((λ / μ) ** c) * rho) / (factorial(c) * ((1 - rho) ** 2))
    else:
        # arrival rate greater than service rate, not good
        lq = float('inf')
    
    # wait time
    wq = lq / λ if λ > 0 else 0
    return rho, lq, wq, p0

for location, group in df.groupby('Address'):
    group = group.sort_values(by='Start_Datetime')
    interarrival_times = group['Start_Datetime'].diff().dt.total_seconds() / 3600
    arrival_rate_lambda = 1 / interarrival_times.mean()
    arrival_rates[location] = arrival_rate_lambda
    
    service_rate_mu = 1 / group['Charging_Time_hours'].mean()
    service_rates[location] = service_rate_mu
    
    c = stations_per_location.get(location)
    
    rho, lq, wq, p0 = mmc_queue(arrival_rate_lambda, service_rate_mu, c)
    utilization[location] = rho
    queue_lengths[location] = lq
    average_wait_times[location] = wq
    p0_[location] = p0



print("Arrival Rates (λ) per Location:")
for location, rate in arrival_rates.items():
    print(f"{location}: {rate:.4f} vehicles per hour")

print("Service Rates (μ) per Location:")
for location, rate in service_rates.items():
    print(f"{location}: {rate:.4f} vehicles per hour")

print("Utilization (rho) per Location:")
for location, util in utilization.items():
    print(f"{location}: {util:.4f}")

print("Average Queue Length (Lq) per Location:")
for location, lq in queue_lengths.items():
    print(f"{location}: {lq:.4f} vehicles")

print("Average Wait Time in Queue (Wq) per Location:")
for location, wq in average_wait_times.items():
    print(f"{location}: {wq:.4f} hours")

print("Probability of there being zero demand (P0) per Location:")
for location, p0 in p0_.items():
    print(f"{location}: {p0:.4f}")



# heatmap

map = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()])

colormap = branca.colormap.LinearColormap(
    colors=['green', 'yellow', 'orange', 'red'], 
    vmin=min(average_wait_times.values()), 
    vmax=max(average_wait_times.values())
).to_step(n=30)

for location, wq in average_wait_times.items():
    lat = df.loc[df['Address'] == location, 'Latitude'].values[0]
    lon = df.loc[df['Address'] == location, 'Longitude'].values[0]
    
    folium.CircleMarker(
        location=[lat, lon],
        radius=15,
        color=colormap(wq),
        fill=True,
        fill_color=colormap(wq),
        fill_opacity=0.4,
        popup=f"{location}: {wq:.2f} hours"
    ).add_to(map)

colormap.add_to(map)

map.save('avg_wait_time_map.html')
