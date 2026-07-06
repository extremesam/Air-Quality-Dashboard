"""
aqi_utils.py
Shared constants and AQI calculation helpers used across the project.

The OpenWeather Air Pollution API returns raw pollutant concentrations
(in micrograms/m3) plus its own 1-5 "qualitative" index. To get the
standard 0-500 AQI scale (the one used worldwide, with Good/Moderate/
Unhealthy/etc. categories and the green-yellow-orange-red-purple-maroon
color scheme), we convert PM2.5 and PM10 concentrations using the
official US EPA breakpoint tables. Overall AQI = the worst (max) of the
individual pollutant sub-indices, which is the standard approach used
by WAQI and most national agencies.
"""

# ---------------------------------------------------------------------
# Cities tracked by the dashboard (name -> (lat, lon)).
# Defaults to major Nigerian cities; edit freely.
# ---------------------------------------------------------------------
CITIES = {
    "Lagos": (6.5244, 3.3792),
    "Abuja": (9.0765, 7.3986),
    "Port Harcourt": (4.8156, 7.0498),
    "Kano": (12.0022, 8.5920),
    "Ibadan": (7.3775, 3.9470),
    "Kaduna": (10.5222, 7.4383),
    "Ogun (Ode-Remo)": (6.8500, 3.6167),
}

# ---------------------------------------------------------------------
# EPA breakpoint tables: (C_low, C_high, I_low, I_high)
# ---------------------------------------------------------------------
PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

PM10_BREAKPOINTS = [
    (0, 54, 0, 50),
    (55, 154, 51, 100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, 504, 301, 400),
    (505, 604, 401, 500),
]

# CO in ppm (converted roughly from ug/m3 assuming ~1.145 mg/m3 per ppm at 25C)
CO_BREAKPOINTS = [
    (0.0, 4.4, 0, 50),
    (4.5, 9.4, 51, 100),
    (9.5, 12.4, 101, 150),
    (12.5, 15.4, 151, 200),
    (15.5, 30.4, 201, 300),
    (30.5, 40.4, 301, 400),
    (40.5, 50.4, 401, 500),
]

# NO2 in ppb
NO2_BREAKPOINTS = [
    (0, 53, 0, 50),
    (54, 100, 51, 100),
    (101, 360, 101, 150),
    (361, 649, 151, 200),
    (650, 1249, 201, 300),
    (1250, 1649, 301, 400),
    (1650, 2049, 401, 500),
]

# SO2 in ppb
SO2_BREAKPOINTS = [
    (0, 35, 0, 50),
    (36, 75, 51, 100),
    (76, 185, 101, 150),
    (186, 304, 151, 200),
    (305, 604, 201, 300),
    (605, 804, 301, 400),
    (805, 1004, 401, 500),
]

# O3 8-hr in ppb
O3_BREAKPOINTS = [
    (0, 54, 0, 50),
    (55, 70, 51, 100),
    (71, 85, 101, 150),
    (86, 105, 151, 200),
    (106, 200, 201, 300),
]

AQI_CATEGORIES = [
    (0, 50, "Good", "🟢", "#00E400"),
    (51, 100, "Moderate", "🟡", "#FFFF00"),
    (101, 150, "Unhealthy for Sensitive Groups", "🟠", "#FF7E00"),
    (151, 200, "Unhealthy", "🔴", "#FF0000"),
    (201, 300, "Very Unhealthy", "🟣", "#8F3F97"),
    (301, 500, "Hazardous", "🟤", "#7E0023"),
]

HEALTH_RECOMMENDATIONS = {
    "Good": "Air quality is satisfactory. Enjoy your normal outdoor activities.",
    "Moderate": "Air quality is acceptable. Unusually sensitive people should consider limiting prolonged outdoor exertion.",
    "Unhealthy for Sensitive Groups": "Children, the elderly, and people with respiratory or heart conditions should limit prolonged outdoor exertion.",
    "Unhealthy": "Limit outdoor activities. Wear an N95 mask if you must go outside. Sensitive groups should avoid outdoor exertion entirely.",
    "Very Unhealthy": "Avoid outdoor activities. Keep windows closed and use air purifiers indoors if available. Wear an N95 mask outdoors.",
    "Hazardous": "Stay indoors. This is an emergency-level condition — avoid all outdoor exertion and seek medical attention if experiencing symptoms.",
}


def _linear_scale(conc, bp_low, bp_high, i_low, i_high):
    """Standard EPA linear interpolation formula."""
    return round(((i_high - i_low) / (bp_high - bp_low)) * (conc - bp_low) + i_low)


def _sub_index(conc, breakpoints):
    if conc is None:
        return None
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= conc <= c_high:
            return _linear_scale(conc, c_low, c_high, i_low, i_high)
    # above table range -> cap at max category, scaled loosely
    c_low, c_high, i_low, i_high = breakpoints[-1]
    if conc > c_high:
        return i_high
    return None


def pm25_to_aqi(conc_ugm3):
    return _sub_index(conc_ugm3, PM25_BREAKPOINTS)


def pm10_to_aqi(conc_ugm3):
    return _sub_index(conc_ugm3, PM10_BREAKPOINTS)


def co_to_aqi(conc_ugm3):
    if conc_ugm3 is None:
        return None
    ppm = conc_ugm3 / 1145.0  # rough ug/m3 -> ppm conversion for CO
    return _sub_index(ppm, CO_BREAKPOINTS)


def no2_to_aqi(conc_ugm3):
    if conc_ugm3 is None:
        return None
    ppb = conc_ugm3 / 1.88  # rough ug/m3 -> ppb conversion for NO2
    return _sub_index(ppb, NO2_BREAKPOINTS)


def so2_to_aqi(conc_ugm3):
    if conc_ugm3 is None:
        return None
    ppb = conc_ugm3 / 2.62  # rough ug/m3 -> ppb conversion for SO2
    return _sub_index(ppb, SO2_BREAKPOINTS)


def o3_to_aqi(conc_ugm3):
    if conc_ugm3 is None:
        return None
    ppb = conc_ugm3 / 1.96  # rough ug/m3 -> ppb conversion for O3
    return _sub_index(ppb, O3_BREAKPOINTS)


def overall_aqi(pm25=None, pm10=None, co=None, no2=None, so2=None, o3=None):
    """Overall AQI = max of the individual pollutant sub-indices (EPA method)."""
    sub_indices = [
        pm25_to_aqi(pm25),
        pm10_to_aqi(pm10),
        co_to_aqi(co),
        no2_to_aqi(no2),
        so2_to_aqi(so2),
        o3_to_aqi(o3),
    ]
    valid = [v for v in sub_indices if v is not None]
    return max(valid) if valid else None


def aqi_category(aqi_value):
    """Return (label, emoji, hex_color) for a given AQI value."""
    if aqi_value is None:
        return ("Unknown", "⚪", "#AAAAAA")
    for low, high, label, emoji, color in AQI_CATEGORIES:
        if low <= aqi_value <= high:
            return (label, emoji, color)
    return ("Hazardous", "🟤", "#7E0023")


def health_recommendation(label):
    return HEALTH_RECOMMENDATIONS.get(label, "No data available.")
