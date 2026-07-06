/* aqi.js — category lookup + health guidance, mirrors scripts/aqi_utils.py */

const AQI_CATEGORIES = [
  { low: 0,   high: 50,  label: "Good",                            color: "#4CD97B" },
  { low: 51,  high: 100, label: "Moderate",                        color: "#E8D34C" },
  { low: 101, high: 150, label: "Unhealthy for Sensitive Groups",   color: "#F0973B" },
  { low: 151, high: 200, label: "Unhealthy",                       color: "#E85C4C" },
  { low: 201, high: 300, label: "Very Unhealthy",                  color: "#B564D4" },
  { low: 301, high: 500, label: "Hazardous",                       color: "#8A3D4E" },
];

const HEALTH_RECOMMENDATIONS = {
  "Good": "Air quality is satisfactory. Enjoy your normal outdoor activities.",
  "Moderate": "Air quality is acceptable. Unusually sensitive people should consider limiting prolonged outdoor exertion.",
  "Unhealthy for Sensitive Groups": "Children, the elderly, and people with respiratory or heart conditions should limit prolonged outdoor exertion.",
  "Unhealthy": "Limit outdoor activities. Wear an N95 mask if you must go outside. Sensitive groups should avoid outdoor exertion entirely.",
  "Very Unhealthy": "Avoid outdoor activities. Keep windows closed and use air purifiers indoors if available. Wear an N95 mask outdoors.",
  "Hazardous": "Stay indoors. This is an emergency-level condition — avoid all outdoor exertion and seek medical attention if experiencing symptoms.",
};

function aqiCategory(aqi) {
  if (aqi === null || aqi === undefined || isNaN(aqi)) {
    return { label: "Unknown", color: "#4E5867" };
  }
  for (const c of AQI_CATEGORIES) {
    if (aqi >= c.low && aqi <= c.high) return c;
  }
  return AQI_CATEGORIES[AQI_CATEGORIES.length - 1];
}

function healthRecommendation(label) {
  return HEALTH_RECOMMENDATIONS[label] || "No data available.";
}
