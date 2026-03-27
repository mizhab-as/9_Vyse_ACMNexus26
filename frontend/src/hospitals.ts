export type LatLon = { lat: number; lon: number };

export type HospitalCandidate = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  address?: string;
};

export type RankedHospital = HospitalCandidate & {
  etaMinutes: number;
  distanceKm: number;
};

function haversineKm(a: LatLon, b: LatLon): number {
  const R = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const la1 = (a.lat * Math.PI) / 180;
  const la2 = (b.lat * Math.PI) / 180;

  const x =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;

  return 2 * R * Math.asin(Math.sqrt(x));
}

async function osrmRoute(
  from: LatLon,
  to: LatLon
): Promise<{ durationSec: number; distanceM: number }> {
  const url = `https://router.project-osrm.org/route/v1/driving/${from.lon},${from.lat};${to.lon},${to.lat}?overview=false`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`OSRM ${res.status}`);
  const data = (await res.json()) as any;
  const route = data?.routes?.[0];
  if (!route) throw new Error('No route');
  return { durationSec: route.duration, distanceM: route.distance };
}

export async function fetchNearbyHospitals(
  center: LatLon,
  radiusMeters = 8000
): Promise<HospitalCandidate[]> {
  const query = `
[out:json];
(
  node["amenity"="hospital"](around:${radiusMeters},${center.lat},${center.lon});
  way["amenity"="hospital"](around:${radiusMeters},${center.lat},${center.lon});
  relation["amenity"="hospital"](around:${radiusMeters},${center.lat},${center.lon});
);
out center 50;
`;

  const res = await fetch('https://overpass-api.de/api/interpreter', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded;charset=UTF-8' },
    body: new URLSearchParams({ data: query }).toString(),
  });

  if (!res.ok) throw new Error(`Overpass ${res.status}`);
  const json = (await res.json()) as any;

  const elements: any[] = Array.isArray(json?.elements) ? json.elements : [];
  const raw: HospitalCandidate[] = [];

  for (const el of elements) {
    const lat: number | undefined =
      typeof el?.lat === 'number' ? el.lat : el?.center?.lat;
    const lon: number | undefined =
      typeof el?.lon === 'number' ? el.lon : el?.center?.lon;
    if (typeof lat !== 'number' || typeof lon !== 'number') continue;

    const name =
      (typeof el?.tags?.name === 'string' && el.tags.name.trim()) ||
      'Unnamed Hospital';

    const addrParts = [
      el?.tags?.['addr:street'],
      el?.tags?.['addr:city'],
      el?.tags?.['addr:district'],
      el?.tags?.['addr:state'],
    ].filter(Boolean);

    const address = addrParts.length ? String(addrParts.join(', ')) : undefined;

    raw.push({
      id: `${el.type}/${el.id}`,
      name,
      lat,
      lon,
      address,
    });
  }

  const seen = new Set<string>();
  const deduped: HospitalCandidate[] = [];
  for (const h of raw) {
    const key = `${h.name}|${h.lat.toFixed(5)}|${h.lon.toFixed(5)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(h);
  }

  deduped.sort((a, b) => haversineKm(center, a) - haversineKm(center, b));
  return deduped.slice(0, 8);
}

export async function rankHospitalsByEta(
  center: LatLon,
  hospitals: HospitalCandidate[]
): Promise<RankedHospital[]> {
  const results = await Promise.allSettled(
    hospitals.map(async (h) => {
      const { durationSec, distanceM } = await osrmRoute(center, {
        lat: h.lat,
        lon: h.lon,
      });

      // No true traffic feed; lightly buffer baseline ETA.
      const etaMinutes = Math.max(1, Math.ceil((durationSec * 1.15) / 60));
      const distanceKm = Math.max(0.1, Math.round((distanceM / 1000) * 10) / 10);

      const ranked: RankedHospital = {
        ...h,
        etaMinutes,
        distanceKm,
      };
      return ranked;
    })
  );

  const ok: RankedHospital[] = [];
  for (const r of results) {
    if (r.status === 'fulfilled') ok.push(r.value);
  }

  ok.sort((a, b) => a.etaMinutes - b.etaMinutes);
  return ok;
}
