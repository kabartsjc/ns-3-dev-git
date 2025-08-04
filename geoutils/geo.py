import math
import random
from typing import List
from core.navdata import NavData
from core.airports import Airport

def distance_haversine(lat1, lon1, lat2, lon2):
    """Calculates the distance in km between two geographic points using the Haversine formula."""
    R = 6371  # Radius of the Earth in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def angle_between(p1, p2, wp):
    """Calculates the angle between the route origin-destination and the intermediate waypoint."""
    def to_vector(a, b):
        return (b[0] - a[0], b[1] - a[1])

    def dot(u, v):
        return u[0]*v[0] + u[1]*v[1]

    def norm(v):
        return math.sqrt(dot(v, v))

    A = (p1.latitude, p1.longitude)
    B = (p2.latitude, p2.longitude)
    W = (wp.latitude, wp.longitude)

    vec_AB = to_vector(A, B)
    vec_AW = to_vector(A, W)

    cos_theta = dot(vec_AB, vec_AW) / (norm(vec_AB) * norm(vec_AW))
    cos_theta = max(-1.0, min(1.0, cos_theta))  # Clamp to avoid numerical errors
    angle = math.acos(cos_theta)
    return math.degrees(angle)

def is_waypoint_on_route(origin: Airport, dest: Airport, wp: NavData, max_deviation_deg: float = 15.0) -> bool:
    """Checks if the waypoint is aligned with the route within an angular deviation tolerance."""
    return angle_between(origin, dest, wp) <= max_deviation_deg

def generate_random_route_between_airports(
    orig: Airport,
    dest: Airport,
    waypoints: List[NavData],
    N: int = 5,
    max_deviation_deg: float = 15.0
) -> List[NavData]:
    """Generates a plausible route between two airports using N intermediate waypoints that make geographic sense."""
    valid_wps = [wp for wp in waypoints if is_waypoint_on_route(orig, dest, wp, max_deviation_deg)]
    if len(valid_wps) < N:
        print(f"Only {len(valid_wps)} plausible waypoints found (needed {N})")
        return []

    selected = random.sample(valid_wps, N)
    # Sort waypoints by cumulative distance from the origin (to maintain logical geographic order)
    selected.sort(key=lambda wp: distance_haversine(orig.latitude, orig.longitude, wp.latitude, wp.longitude))
    return selected


def ete_seconds_km(route_latlon, speed_knots):
    # route_latlon: [(lat0,lon0), (lat1,lon1), ... , (latN,lonN)]
    import math

    def hav(lat1, lon1, lat2, lon2):
        R = 6371.0
        from math import radians, sin, cos, atan2, sqrt
        φ1, φ2 = radians(lat1), radians(lat2)
        dφ = radians(lat2 - lat1); dλ = radians(lon2 - lon1)
        a = sin(dφ/2)**2 + cos(φ1)*cos(φ2)*sin(dλ/2)**2
        return 2*R*atan2(math.sqrt(a), math.sqrt(1-a))

    # total distance (km)
    d_km = sum(hav(route_latlon[i][0], route_latlon[i][1],
                   route_latlon[i+1][0], route_latlon[i+1][1])
               for i in range(len(route_latlon)-1))

    # convert speed to km/h (1 kt = 1.852 km/h)
    v_kmh = speed_knots * 1.852
    hours = d_km / v_kmh if v_kmh > 0 else 0
    return int(hours * 3600)

def hhmmss(seconds):
    h = seconds // 3600; m = (seconds % 3600) // 60; s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}.00"


