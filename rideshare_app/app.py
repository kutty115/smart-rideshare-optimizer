from flask import Flask, render_template, request, redirect, url_for
import heapq

app = Flask(__name__)

# Graph with Hyderabad locations
graph = {
    'Madhapur': {'Gachibowli': 4, 'Hitech City': 2},
    'Gachibowli': {'Madhapur': 4, 'Hitech City': 5, 'Banjara Hills': 10},
    'Hitech City': {'Madhapur': 2, 'Gachibowli': 5, 'Banjara Hills': 3, 'Secunderabad': 4},
    'Banjara Hills': {'Gachibowli': 10, 'Hitech City': 3, 'Charminar': 11},
    'Secunderabad': {'Hitech City': 4, 'Charminar': 2},
    'Charminar': {'Banjara Hills': 11, 'Secunderabad': 2}
}

drivers = [
    {"name": "Driver1", "location": "Madhapur", "available": True},
    {"name": "Driver2", "location": "Hitech City", "available": True},
    {"name": "Driver3", "location": "Secunderabad", "available": True}
]

waiting_queue = []
active_rides = []
completed_rides = []

# ---- Dijkstra Shortest Path ----
def dijkstra(start, end):
    pq = [(0, start, [])]
    visited = set()
    while pq:
        (cost, node, path) = heapq.heappop(pq)
        if node in visited:
            continue
        path = path + [node]
        if node == end:
            return (cost, path)
        visited.add(node)
        for neighbor, weight in graph[node].items():
            if neighbor not in visited:
                heapq.heappush(pq, (cost + weight, neighbor, path))
    return (float("inf"), [])

# ---- Routes ----
@app.route("/")
def index():
    nodes = list(graph.keys())   # ✅ Pass city names
    return render_template(
        "index.html",
        drivers=drivers,
        waiting_queue=waiting_queue,
        active_rides=active_rides,
        completed_rides=completed_rides,
        nodes=nodes  # ✅ important
    )

@app.route("/request_ride", methods=["POST"])
def request_ride():
    rider_name = request.form["rider_name"]
    source = request.form["source"]
    destination = request.form["destination"]

    nearest_driver = None
    min_distance = float("inf")
    pickup_path = []
    for d in drivers:
        if d["available"]:
            dist, path = dijkstra(d["location"], source)
            if dist < min_distance:
                min_distance = dist
                nearest_driver = d
                pickup_path = path

    if nearest_driver:
        nearest_driver["available"] = False
        nearest_driver["location"] = destination
        trip_dist, trip_path = dijkstra(source, destination)
        fare = trip_dist * 10

        ride = {
            "rider_name": rider_name,
            "driver": nearest_driver["name"],
            "pickup_path": pickup_path,
            "trip_path": trip_path,
            "distance": trip_dist,
            "fare": fare
        }
        active_rides.append(ride)
    else:
        waiting_queue.append({"rider_name": rider_name, "source": source, "destination": destination})

    return redirect(url_for("index"))

@app.route("/complete_ride/<rider_name>", methods=["POST"])
def complete_ride(rider_name):
    ride = next((r for r in active_rides if r["rider_name"] == rider_name), None)
    if ride:
        active_rides.remove(ride)
        completed_rides.append(ride)
        driver = next(d for d in drivers if d["name"] == ride["driver"])
        driver["available"] = True
        driver["location"] = ride["trip_path"][-1]

        if waiting_queue:
            req = waiting_queue.pop(0)
            return assign_from_queue(req, driver)

    return redirect(url_for("index"))

def assign_from_queue(req, driver):
    source, destination = req["source"], req["destination"]
    driver["available"] = False
    driver["location"] = destination
    trip_dist, trip_path = dijkstra(source, destination)
    fare = trip_dist * 10
    ride = {
        "rider_name": req["rider_name"],
        "driver": driver["name"],
        "pickup_path": [driver["location"]],
        "trip_path": trip_path,
        "distance": trip_dist,
        "fare": fare
    }
    active_rides.append(ride)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)

