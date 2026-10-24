/**
 * Geodesic Area Calculation & GeoJSON Polygon Validation for KisanCare
 * Computes ellipsoidal/spherical polygon area using WGS84 coordinates.
 */

const EARTH_RADIUS = 6378137; // WGS84 semi-major axis in meters

/**
 * Calculates polygon surface area in square meters using spherical excess formula.
 * @param coords Array of [lon, lat] pairs in GeoJSON order.
 */
export function calculateGeodesicAreaM2(coords: Array<[number, number]>): number {
  if (!coords || coords.length < 3) return 0;

  // Ensure ring is closed
  const ring = [...coords];
  const first = ring[0];
  const last = ring[ring.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) {
    ring.push(first);
  }

  if (ring.length < 4) return 0;

  let totalAngle = 0;
  const len = ring.length - 1;

  for (let i = 0; i < len; i++) {
    const p1 = ring[i];
    const p2 = ring[i + 1];

    const lon1 = (p1[0] * Math.PI) / 180;
    const lat1 = (p1[1] * Math.PI) / 180;
    const lon2 = (p2[0] * Math.PI) / 180;
    const lat2 = (p2[1] * Math.PI) / 180;

    totalAngle += (lon2 - lon1) * (2 + Math.sin(lat1) + Math.sin(lat2));
  }

  const areaM2 = Math.abs((totalAngle * EARTH_RADIUS * EARTH_RADIUS) / 2.0);
  return areaM2;
}

/**
 * Converts square meters to agricultural units (acres, hectares, guntha).
 */
export function convertM2ToUnit(m2: number, unit: string = 'acre'): number {
  switch (unit.toLowerCase()) {
    case 'acre':
    case 'acres':
      return m2 / 4046.8564224;
    case 'hectare':
    case 'hectares':
    case 'ha':
      return m2 / 10000;
    case 'guntha':
      return m2 / 101.1714;
    default:
      return m2 / 4046.8564224;
  }
}

/**
 * Computes the haversine distance in meters between two [lon, lat] points.
 */
export function haversineDistanceMeters(p1: [number, number], p2: [number, number]): number {
  const lon1 = (p1[0] * Math.PI) / 180;
  const lat1 = (p1[1] * Math.PI) / 180;
  const lon2 = (p2[0] * Math.PI) / 180;
  const lat2 = (p2[1] * Math.PI) / 180;

  const dLat = lat2 - lat1;
  const dLon = lon2 - lon1;

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return EARTH_RADIUS * c;
}

/**
 * Validates whether an incoming GPS fix is suitable for recording.
 * Rejects fixes with accuracy > maxAccuracyMeters or suspicious physical jumps > maxSpeedMps.
 */
export function filterGpsFix(
  newCoord: [number, number],
  accuracy: number,
  lastCoord?: [number, number],
  timeDeltaSec?: number,
  maxAccuracyMeters: number = 30,
  minDistanceMeters: number = 2.0,
  maxJumpSpeedMps: number = 20 // 72 km/h - filters teleports/multipath jumps
): { accept: boolean; reason?: string; isDuplicate?: boolean; isSuspiciousJump?: boolean } {
  const [lon, lat] = newCoord;

  if (typeof lon !== 'number' || typeof lat !== 'number' || isNaN(lon) || isNaN(lat)) {
    return { accept: false, reason: 'Invalid GPS numbers.' };
  }
  if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
    return { accept: false, reason: 'Coordinates out of geographic range.' };
  }

  // Reject fixes with poor GPS dilution of precision / high inaccuracy
  if (accuracy > maxAccuracyMeters) {
    return {
      accept: false,
      reason: `Accuracy too low (${Math.round(accuracy)}m > ${maxAccuracyMeters}m limit). Walk with clear sky view.`
    };
  }

  if (lastCoord) {
    const dist = haversineDistanceMeters(lastCoord, newCoord);

    // Filter duplicate / stationary jitter (< 2m)
    if (dist < minDistanceMeters) {
      return { accept: false, reason: 'Stationary position jitter (< 2m).', isDuplicate: true };
    }

    // Filter physical teleport jumps
    if (timeDeltaSec && timeDeltaSec > 0) {
      const speed = dist / timeDeltaSec;
      if (speed > maxJumpSpeedMps) {
        return {
          accept: false,
          reason: `Suspicious GPS jump: ${Math.round(dist)}m in ${timeDeltaSec.toFixed(1)}s (${Math.round(speed * 3.6)} km/h).`,
          isSuspiciousJump: true
        };
      }
    }
  }

  return { accept: true };
}

/**
 * Validates GeoJSON coordinates for range and basic non-degeneracy.
 */
export function validatePolygonCoordinates(coords: Array<[number, number]>): { valid: boolean; reason?: string } {
  if (!coords || coords.length < 3) {
    return { valid: false, reason: 'A boundary polygon requires at least 3 distinct vertices.' };
  }

  for (let i = 0; i < coords.length; i++) {
    const [lon, lat] = coords[i];
    if (typeof lon !== 'number' || typeof lat !== 'number' || isNaN(lon) || isNaN(lat)) {
      return { valid: false, reason: `Invalid coordinate pair at point ${i + 1}.` };
    }
    if (lat < -90 || lat > 90) {
      return { valid: false, reason: `Latitude ${lat} is out of range (-90 to 90).` };
    }
    if (lon < -180 || lon > 180) {
      return { valid: false, reason: `Longitude ${lon} is out of range (-180 to 180).` };
    }
  }

  return { valid: true };
}
