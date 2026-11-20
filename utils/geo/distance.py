import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two points on Earth in kilometers.
    """
    if None in (lat1, lon1, lat2, lon2):
        return 0.0

    R = 6371.0  # Earth radius in KM

    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))

    a = math.sin(dlat / 2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    print(f"Distância entre ({lat1}, {lon1}) e ({lat2}, {lon2}): {distance} km")
    return distance
