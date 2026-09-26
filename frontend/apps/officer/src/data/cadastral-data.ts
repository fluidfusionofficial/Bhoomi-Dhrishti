// Comprehensive georeferenced cadastral data — Tirupporur village, Chengalpattu district, Tamil Nadu
// 50 parcels with 14-digit ULPINs (DILRMP standard) + infrastructure overlay layers
// ULPIN format: SS-DD-TT-VV-NNNNNN (State-District-Taluk-Village-Seq)
// TN=33, Chengalpattu=23, Tirupporur=01, Village=01 → prefix 33230101

export interface ParcelData {
  parcel_id: string;
  ulpin: string;
  survey_number: string;
  patta_no: string;
  area: number;
  land_use: string;
  owner: string;
  status: string;
  status_detail: string;
  risk_level: string;
  anomaly_score: number;
  district: string;
  taluk: string;
  village: string;
  place: string;
}

// ── 50 Georeferenced Cadastral Parcels ──────────────────────────────────────────

export const PARCEL_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    // ── EXISTING NORTHERN BELT (lat ~12.729–12.734) ─────────────────────────────
    { type: 'Feature', properties: { parcel_id: 'P001', ulpin: '33230101000001', survey_number: '41/1A', patta_no: 'PT/2019/1042', area: 3.1, land_use: 'Agricultural', owner: 'Lakshmi Narayanan', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.12, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1806,12.7322],[80.1838,12.7331],[80.1851,12.7318],[80.1843,12.7302],[80.1818,12.7294],[80.1798,12.7306],[80.1806,12.7322]]] } },

    { type: 'Feature', properties: { parcel_id: 'P002', ulpin: '33230101000002', survey_number: '41/2B', patta_no: 'PT/2021/0221', area: 1.85, land_use: 'Residential', owner: 'Meena Rajendran', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.08, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1853,12.7320],[80.1866,12.7325],[80.1876,12.7315],[80.1870,12.7300],[80.1853,12.7296],[80.1843,12.7302],[80.1853,12.7320]]] } },

    { type: 'Feature', properties: { parcel_id: 'P003', ulpin: '33230101000003', survey_number: '42/3B', patta_no: 'PT/2020/0789', area: 2.4, land_use: 'Residential', owner: 'Arun Kumar', status: 'Conflict', status_detail: 'Ownership Conflict', risk_level: 'High', anomaly_score: 0.91, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1876,12.7323],[80.1896,12.7330],[80.1910,12.7317],[80.1904,12.7298],[80.1882,12.7290],[80.1870,12.7300],[80.1876,12.7323]]] } },

    { type: 'Feature', properties: { parcel_id: 'P004', ulpin: '33230101000004', survey_number: '42/4A', patta_no: 'PT/2018/0634', area: 4.2, land_use: 'Agricultural', owner: 'Suresh Babu', status: 'Warning', status_detail: 'Encumbrance Warning', risk_level: 'Medium', anomaly_score: 0.52, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1910,12.7317],[80.1928,12.7328],[80.1944,12.7322],[80.1946,12.7304],[80.1928,12.7291],[80.1908,12.7290],[80.1904,12.7298],[80.1910,12.7317]]] } },

    { type: 'Feature', properties: { parcel_id: 'P005', ulpin: '33230101000005', survey_number: '43/1C', patta_no: 'PT/2022/1128', area: 0.95, land_use: 'Commercial', owner: 'Priya Venkatesh', status: 'Warning', status_detail: 'Tax Warning', risk_level: 'Medium', anomaly_score: 0.48, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1946,12.7318],[80.1960,12.7324],[80.1970,12.7312],[80.1966,12.7297],[80.1948,12.7291],[80.1946,12.7304],[80.1946,12.7318]]] } },

    // ── EXISTING MIDDLE BELT (lat ~12.725–12.731) ───────────────────────────────
    { type: 'Feature', properties: { parcel_id: 'P006', ulpin: '33230101000006', survey_number: '43/2A', patta_no: 'PT/2017/0512', area: 2.75, land_use: 'Mixed', owner: 'Karthik Selvam', status: 'Conflict', status_detail: 'Planning Conflict', risk_level: 'High', anomaly_score: 0.87, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon', coordinates: [[[80.1798,12.7306],[80.1818,12.7294],[80.1826,12.7279],[80.1814,12.7264],[80.1793,12.7260],[80.1782,12.7273],[80.1790,12.7292],[80.1798,12.7306]]] } },

    { type: 'Feature', properties: { parcel_id: 'P007', ulpin: '33230101000007', survey_number: '44/1B', patta_no: 'PT/2020/0856', area: 1.4, land_use: 'Residential', owner: 'Divya Anand', status: 'Warning', status_detail: 'Building Permission Warning', risk_level: 'Medium', anomaly_score: 0.55, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon', coordinates: [[[80.1843,12.7302],[80.1853,12.7296],[80.1859,12.7280],[80.1846,12.7266],[80.1830,12.7268],[80.1826,12.7279],[80.1843,12.7302]]] } },

    { type: 'Feature', properties: { parcel_id: 'P008', ulpin: '33230101000008', survey_number: '45/2A', patta_no: 'PT/2018/1204', area: 3.6, land_use: 'Agricultural', owner: 'Arun Raj', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.15, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon', coordinates: [[[80.1870,12.7300],[80.1882,12.7290],[80.1892,12.7275],[80.1882,12.7258],[80.1860,12.7253],[80.1846,12.7260],[80.1846,12.7266],[80.1859,12.7280],[80.1870,12.7300]]] } },

    { type: 'Feature', properties: { parcel_id: 'P009', ulpin: '33230101000009', survey_number: '45/3B', patta_no: 'PT/2019/0945', area: 2.1, land_use: 'Residential', owner: 'Ganesh Moorthy', status: 'Warning', status_detail: 'Area Discrepancy', risk_level: 'Medium', anomaly_score: 0.61, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon', coordinates: [[[80.1904,12.7298],[80.1920,12.7290],[80.1930,12.7276],[80.1918,12.7260],[80.1898,12.7254],[80.1882,12.7258],[80.1892,12.7275],[80.1904,12.7298]]] } },

    { type: 'Feature', properties: { parcel_id: 'P010', ulpin: '33230101000010', survey_number: '46/1A', patta_no: 'PT/2021/1067', area: 1.2, land_use: 'Commercial', owner: 'Ravi Chandran', status: 'Pending', status_detail: 'Pending Transaction', risk_level: 'Medium', anomaly_score: 0.44, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon', coordinates: [[[80.1946,12.7304],[80.1948,12.7291],[80.1964,12.7282],[80.1966,12.7265],[80.1946,12.7258],[80.1930,12.7264],[80.1930,12.7276],[80.1946,12.7304]]] } },

    // ── EXISTING SOUTHERN BELT (lat ~12.722–12.727) ─────────────────────────────
    { type: 'Feature', properties: { parcel_id: 'P011', ulpin: '33230101000011', survey_number: '46/2C', patta_no: 'PT/2016/0445', area: 5.3, land_use: 'Agricultural', owner: 'Saravanan Pillai', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.10, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Manimangalam' },
      geometry: { type: 'Polygon', coordinates: [[[80.1782,12.7273],[80.1793,12.7260],[80.1814,12.7264],[80.1830,12.7268],[80.1828,12.7248],[80.1808,12.7236],[80.1784,12.7232],[80.1768,12.7248],[80.1782,12.7273]]] } },

    { type: 'Feature', properties: { parcel_id: 'P012', ulpin: '33230101000012', survey_number: '47/1B', patta_no: 'PT/2023/1334', area: 0.8, land_use: 'Industrial', owner: 'Nithya Sundaram', status: 'Conflict', status_detail: 'High Risk Transaction', risk_level: 'High', anomaly_score: 0.93, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Padappai Nagar' },
      geometry: { type: 'Polygon', coordinates: [[[80.1830,12.7268],[80.1846,12.7266],[80.1860,12.7253],[80.1854,12.7238],[80.1836,12.7232],[80.1820,12.7238],[80.1820,12.7252],[80.1830,12.7268]]] } },

    { type: 'Feature', properties: { parcel_id: 'P013', ulpin: '33230101000013', survey_number: '47/3A', patta_no: 'PT/2022/1256', area: 2.95, land_use: 'Residential', owner: 'Bala Subramani', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.18, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Padappai Nagar' },
      geometry: { type: 'Polygon', coordinates: [[[80.1860,12.7253],[80.1882,12.7258],[80.1894,12.7244],[80.1888,12.7230],[80.1866,12.7224],[80.1846,12.7230],[80.1854,12.7238],[80.1860,12.7253]]] } },

    { type: 'Feature', properties: { parcel_id: 'P014', ulpin: '33230101000014', survey_number: '48/1A', patta_no: 'PT/2020/0912', area: 3.85, land_use: 'Mixed', owner: 'Kavya Raman', status: 'Warning', status_detail: 'Planning Warning', risk_level: 'Medium', anomaly_score: 0.58, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Padappai Nagar' },
      geometry: { type: 'Polygon', coordinates: [[[80.1898,12.7254],[80.1918,12.7260],[80.1936,12.7252],[80.1940,12.7234],[80.1920,12.7224],[80.1898,12.7226],[80.1888,12.7238],[80.1898,12.7254]]] } },

    { type: 'Feature', properties: { parcel_id: 'P015', ulpin: '33230101000015', survey_number: '48/2B', patta_no: 'WB/1948/0003', area: 1.65, land_use: 'Water Body', owner: 'Village Commons', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.05, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Periya Eri' },
      geometry: { type: 'Polygon', coordinates: [[[80.1946,12.7258],[80.1966,12.7265],[80.1978,12.7254],[80.1976,12.7238],[80.1958,12.7228],[80.1940,12.7230],[80.1940,12.7234],[80.1946,12.7258]]] } },

    // ── FAR NORTH ROW — upper agricultural / forest belt (lat ~12.735–12.738) ───
    { type: 'Feature', properties: { parcel_id: 'P016', ulpin: '33230101000016', survey_number: '49/1A', patta_no: 'PT/2018/0842', area: 4.2, land_use: 'Agricultural', owner: 'Murugan Shankar', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.11, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Nallur' },
      geometry: { type: 'Polygon', coordinates: [[[80.1724,12.7356],[80.1770,12.7354],[80.1772,12.7376],[80.1726,12.7378],[80.1724,12.7356]]] } },

    { type: 'Feature', properties: { parcel_id: 'P017', ulpin: '33230101000017', survey_number: '49/2B', patta_no: 'PT/2020/0821', area: 3.5, land_use: 'Agricultural', owner: 'Devi Bala', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.09, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Nallur' },
      geometry: { type: 'Polygon', coordinates: [[[80.1776,12.7354],[80.1822,12.7356],[80.1824,12.7378],[80.1778,12.7376],[80.1776,12.7354]]] } },

    { type: 'Feature', properties: { parcel_id: 'P018', ulpin: '33230101000018', survey_number: '50/RF', patta_no: 'RF/1927/0001', area: 6.8, land_use: 'Forest', owner: 'Reserve Forest Dept', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.03, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Nallur Reserve' },
      geometry: { type: 'Polygon', coordinates: [[[80.1828,12.7356],[80.1886,12.7354],[80.1888,12.7378],[80.1830,12.7380],[80.1828,12.7356]]] } },

    { type: 'Feature', properties: { parcel_id: 'P019', ulpin: '33230101000019', survey_number: '51/1A', patta_no: 'PT/2019/0933', area: 4.1, land_use: 'Agricultural', owner: 'Kumaresan Thevar', status: 'Warning', status_detail: 'Encumbrance Warning', risk_level: 'Medium', anomaly_score: 0.46, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Nallur' },
      geometry: { type: 'Polygon', coordinates: [[[80.1892,12.7354],[80.1938,12.7356],[80.1940,12.7378],[80.1894,12.7376],[80.1892,12.7354]]] } },

    { type: 'Feature', properties: { parcel_id: 'P020', ulpin: '33230101000020', survey_number: '52/PB', patta_no: 'PB/1956/0012', area: 7.5, land_use: 'Poramboke', owner: 'Village Panchayat', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.04, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Poramboke Natham' },
      geometry: { type: 'Polygon', coordinates: [[[80.1944,12.7356],[80.2010,12.7354],[80.2012,12.7378],[80.1946,12.7380],[80.1944,12.7356]]] } },

    // ── FAR NORTH ROW — lower sub-row (lat ~12.734–12.735) ──────────────────────
    { type: 'Feature', properties: { parcel_id: 'P021', ulpin: '33230101000021', survey_number: '53/1C', patta_no: 'PT/2022/1288', area: 1.8, land_use: 'Residential', owner: 'Anbu Chelvan', status: 'Warning', status_detail: 'Building Permission Warning', risk_level: 'Medium', anomaly_score: 0.50, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Puthu Nagar' },
      geometry: { type: 'Polygon', coordinates: [[[80.1724,12.7340],[80.1770,12.7338],[80.1772,12.7354],[80.1726,12.7356],[80.1724,12.7340]]] } },

    { type: 'Feature', properties: { parcel_id: 'P022', ulpin: '33230101000022', survey_number: '54/G', patta_no: 'GV/1972/0008', area: 2.5, land_use: 'Government', owner: 'Panchayat Union', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.02, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'School Campus' },
      geometry: { type: 'Polygon', coordinates: [[[80.1776,12.7338],[80.1822,12.7340],[80.1824,12.7356],[80.1778,12.7354],[80.1776,12.7338]]] } },

    { type: 'Feature', properties: { parcel_id: 'P023', ulpin: '33230101000023', survey_number: '55/2A', patta_no: 'PT/2021/1156', area: 2.2, land_use: 'Residential', owner: 'Valli Ammal', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.14, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Puthu Nagar' },
      geometry: { type: 'Polygon', coordinates: [[[80.1828,12.7340],[80.1886,12.7338],[80.1888,12.7354],[80.1830,12.7356],[80.1828,12.7340]]] } },

    { type: 'Feature', properties: { parcel_id: 'P024', ulpin: '33230101000024', survey_number: '56/1B', patta_no: 'PT/2017/0744', area: 3.6, land_use: 'Agricultural', owner: 'Senthil Nathan', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.13, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Nallur' },
      geometry: { type: 'Polygon', coordinates: [[[80.1892,12.7338],[80.1938,12.7340],[80.1940,12.7356],[80.1894,12.7354],[80.1892,12.7338]]] } },

    { type: 'Feature', properties: { parcel_id: 'P025', ulpin: '33230101000025', survey_number: '57/UC', patta_no: 'RV/1989/0034', area: 5.0, land_use: 'Unoccupied', owner: 'Revenue Dept (TN)', status: 'Pending', status_detail: 'Classification Pending', risk_level: 'Low', anomaly_score: 0.22, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Vazhi Nilam' },
      geometry: { type: 'Polygon', coordinates: [[[80.1944,12.7340],[80.2010,12.7338],[80.2012,12.7354],[80.1946,12.7356],[80.1944,12.7340]]] } },

    // ── NORTH INFILL (lat ~12.733–12.734) — residential subdivision ─────────────
    { type: 'Feature', properties: { parcel_id: 'P026', ulpin: '33230101000026', survey_number: '58/1A', patta_no: 'PT/2023/1402', area: 0.65, land_use: 'Residential', owner: 'Rajeshwari Devi', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.10, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1728,12.7332],[80.1778,12.7334],[80.1776,12.7340],[80.1726,12.7338],[80.1728,12.7332]]] } },

    { type: 'Feature', properties: { parcel_id: 'P027', ulpin: '33230101000027', survey_number: '58/1B', patta_no: 'PT/2023/1403', area: 0.55, land_use: 'Residential', owner: 'Muthulakshmi K', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.07, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1782,12.7334],[80.1832,12.7332],[80.1830,12.7340],[80.1780,12.7338],[80.1782,12.7334]]] } },

    { type: 'Feature', properties: { parcel_id: 'P028', ulpin: '33230101000028', survey_number: '58/2A', patta_no: 'PT/2023/1404', area: 0.70, land_use: 'Residential', owner: 'Alaguraja P', status: 'Warning', status_detail: 'Tax Arrears', risk_level: 'Medium', anomaly_score: 0.42, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1836,12.7332],[80.1886,12.7334],[80.1884,12.7340],[80.1834,12.7338],[80.1836,12.7332]]] } },

    { type: 'Feature', properties: { parcel_id: 'P029', ulpin: '33230101000029', survey_number: '58/2B', patta_no: 'PT/2022/1289', area: 0.48, land_use: 'Commercial', owner: 'Tamilarasi V', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.16, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1890,12.7334],[80.1940,12.7332],[80.1938,12.7340],[80.1888,12.7338],[80.1890,12.7334]]] } },

    { type: 'Feature', properties: { parcel_id: 'P030', ulpin: '33230101000030', survey_number: '58/3A', patta_no: 'PT/2024/1520', area: 0.60, land_use: 'Residential', owner: 'Gopalakrishnan R', status: 'Conflict', status_detail: 'Boundary Dispute', risk_level: 'High', anomaly_score: 0.84, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1944,12.7332],[80.2006,12.7334],[80.2004,12.7340],[80.1942,12.7338],[80.1944,12.7332]]] } },

    // ── WEST EXTENSION (lng ~80.172–80.176) ─────────────────────────────────────
    { type: 'Feature', properties: { parcel_id: 'P031', ulpin: '33230101000031', survey_number: '39/1A', patta_no: 'PT/2016/0612', area: 5.8, land_use: 'Agricultural', owner: 'Sundaramoorthy M', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.08, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Manimangalam' },
      geometry: { type: 'Polygon', coordinates: [[[80.1722,12.7302],[80.1762,12.7300],[80.1764,12.7332],[80.1724,12.7334],[80.1722,12.7316],[80.1722,12.7302]]] } },

    { type: 'Feature', properties: { parcel_id: 'P032', ulpin: '33230101000032', survey_number: '39/2B', patta_no: 'PT/2018/0845', area: 4.5, land_use: 'Agricultural', owner: 'Vijayalakshmi S', status: 'Warning', status_detail: 'Area Discrepancy', risk_level: 'Medium', anomaly_score: 0.51, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Manimangalam' },
      geometry: { type: 'Polygon', coordinates: [[[80.1720,12.7264],[80.1762,12.7262],[80.1764,12.7298],[80.1722,12.7300],[80.1720,12.7282],[80.1720,12.7264]]] } },

    { type: 'Feature', properties: { parcel_id: 'P033', ulpin: '33230101000033', survey_number: '40/1A', patta_no: 'PT/2015/0501', area: 5.2, land_use: 'Agricultural', owner: 'Karuppusamy T', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.12, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Manimangalam' },
      geometry: { type: 'Polygon', coordinates: [[[80.1720,12.7224],[80.1764,12.7222],[80.1766,12.7260],[80.1722,12.7262],[80.1720,12.7244],[80.1720,12.7224]]] } },

    // ── EAST EXTENSION (lng ~80.198–80.202) ─────────────────────────────────────
    { type: 'Feature', properties: { parcel_id: 'P034', ulpin: '33230101000034', survey_number: '59/1A', patta_no: 'PT/2021/1178', area: 2.8, land_use: 'Residential', owner: 'Parvathi Devi', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.11, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Vandalur Cross' },
      geometry: { type: 'Polygon', coordinates: [[[80.1982,12.7302],[80.2014,12.7300],[80.2016,12.7334],[80.1984,12.7336],[80.1982,12.7318],[80.1982,12.7302]]] } },

    { type: 'Feature', properties: { parcel_id: 'P035', ulpin: '33230101000035', survey_number: '59/2C', patta_no: 'PT/2020/0988', area: 1.5, land_use: 'Commercial', owner: 'Nagarajan B', status: 'Warning', status_detail: 'Zoning Violation', risk_level: 'Medium', anomaly_score: 0.56, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Vandalur Cross' },
      geometry: { type: 'Polygon', coordinates: [[[80.1980,12.7266],[80.2014,12.7264],[80.2016,12.7300],[80.1982,12.7302],[80.1980,12.7284],[80.1980,12.7266]]] } },

    { type: 'Feature', properties: { parcel_id: 'P036', ulpin: '33230101000036', survey_number: '60/WB', patta_no: 'WB/1948/0005', area: 3.4, land_use: 'Water Body', owner: 'Village Panchayat', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.04, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Periya Eri' },
      geometry: { type: 'Polygon', coordinates: [[[80.1980,12.7226],[80.2016,12.7224],[80.2018,12.7264],[80.1982,12.7266],[80.1980,12.7246],[80.1980,12.7226]]] } },

    // ── SOUTH INFILL (lat ~12.721–12.722) ───────────────────────────────────────
    { type: 'Feature', properties: { parcel_id: 'P037', ulpin: '33230101000037', survey_number: '61/1A', patta_no: 'PT/2022/1301', area: 0.45, land_use: 'Residential', owner: 'Chandra Sekar', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.09, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Padappai Nagar' },
      geometry: { type: 'Polygon', coordinates: [[[80.1772,12.7210],[80.1826,12.7208],[80.1828,12.7222],[80.1774,12.7224],[80.1772,12.7210]]] } },

    { type: 'Feature', properties: { parcel_id: 'P038', ulpin: '33230101000038', survey_number: '61/1B', patta_no: 'PT/2024/1545', area: 0.52, land_use: 'Residential', owner: 'Kanagavalli M', status: 'Pending', status_detail: 'Mutation Pending', risk_level: 'Low', anomaly_score: 0.28, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Padappai Nagar' },
      geometry: { type: 'Polygon', coordinates: [[[80.1832,12.7208],[80.1886,12.7210],[80.1888,12.7224],[80.1834,12.7222],[80.1832,12.7208]]] } },

    { type: 'Feature', properties: { parcel_id: 'P039', ulpin: '33230101000039', survey_number: '62/RW', patta_no: 'RW/1952/0007', area: 3.2, land_use: 'Government', owner: 'Southern Railway', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.02, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Railway Colony' },
      geometry: { type: 'Polygon', coordinates: [[[80.1892,12.7210],[80.1942,12.7208],[80.1944,12.7224],[80.1894,12.7222],[80.1892,12.7210]]] } },

    { type: 'Feature', properties: { parcel_id: 'P040', ulpin: '33230101000040', survey_number: '61/2A', patta_no: 'PT/2019/0956', area: 0.55, land_use: 'Residential', owner: 'Ponnu Swamy', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.13, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Padappai Nagar' },
      geometry: { type: 'Polygon', coordinates: [[[80.1948,12.7208],[80.1998,12.7210],[80.2000,12.7224],[80.1950,12.7222],[80.1948,12.7208]]] } },

    { type: 'Feature', properties: { parcel_id: 'P041', ulpin: '33230101000041', survey_number: '61/3A', patta_no: 'PT/2025/1612', area: 0.38, land_use: 'Residential', owner: 'Saroja Devi', status: 'Conflict', status_detail: 'Title Dispute', risk_level: 'High', anomaly_score: 0.88, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Padappai Nagar' },
      geometry: { type: 'Polygon', coordinates: [[[80.2004,12.7210],[80.2018,12.7208],[80.2020,12.7224],[80.2006,12.7222],[80.2004,12.7210]]] } },

    // ── FAR SOUTH ROW — upper sub-row (lat ~12.719–12.721) ──────────────────────
    { type: 'Feature', properties: { parcel_id: 'P042', ulpin: '33230101000042', survey_number: '63/1A', patta_no: 'PT/2017/0762', area: 2.8, land_use: 'Agricultural', owner: 'Easwari Bai', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.10, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Eri Karai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1724,12.7194],[80.1778,12.7192],[80.1780,12.7208],[80.1726,12.7210],[80.1724,12.7194]]] } },

    { type: 'Feature', properties: { parcel_id: 'P043', ulpin: '33230101000043', survey_number: '63/2B', patta_no: 'PT/2018/0886', area: 2.0, land_use: 'Residential', owner: 'Rangasamy Mudaliar', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.14, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Eri Karai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1784,12.7192],[80.1838,12.7194],[80.1840,12.7210],[80.1786,12.7208],[80.1784,12.7192]]] } },

    { type: 'Feature', properties: { parcel_id: 'P044', ulpin: '33230101000044', survey_number: '64/G', patta_no: 'GV/1965/0004', area: 3.5, land_use: 'Government', owner: 'Revenue Dept (TN)', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.02, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Railway Station' },
      geometry: { type: 'Polygon', coordinates: [[[80.1844,12.7194],[80.1900,12.7192],[80.1902,12.7210],[80.1846,12.7208],[80.1844,12.7194]]] } },

    { type: 'Feature', properties: { parcel_id: 'P045', ulpin: '33230101000045', survey_number: '63/3C', patta_no: 'PT/2021/1189', area: 1.2, land_use: 'Residential', owner: 'Kuppu Swamy', status: 'Warning', status_detail: 'Tax Arrears', risk_level: 'Medium', anomaly_score: 0.47, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Eri Karai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1906,12.7192],[80.1960,12.7194],[80.1962,12.7210],[80.1908,12.7208],[80.1906,12.7192]]] } },

    { type: 'Feature', properties: { parcel_id: 'P046', ulpin: '33230101000046', survey_number: '65/1A', patta_no: 'PT/2016/0634', area: 2.4, land_use: 'Agricultural', owner: 'Meenakshi Ammal', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.07, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Eri Karai' },
      geometry: { type: 'Polygon', coordinates: [[[80.1966,12.7194],[80.2012,12.7192],[80.2014,12.7210],[80.1968,12.7208],[80.1966,12.7194]]] } },

    // ── FAR SOUTH ROW — lower sub-row (lat ~12.718–12.719) ──────────────────────
    { type: 'Feature', properties: { parcel_id: 'P047', ulpin: '33230101000047', survey_number: '65/2B', patta_no: 'PT/2019/0978', area: 2.6, land_use: 'Agricultural', owner: 'Natarajan P', status: 'Pending', status_detail: 'Mutation Pending', risk_level: 'Low', anomaly_score: 0.25, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon', coordinates: [[[80.1724,12.7180],[80.1780,12.7178],[80.1782,12.7192],[80.1726,12.7194],[80.1724,12.7180]]] } },

    { type: 'Feature', properties: { parcel_id: 'P048', ulpin: '33230101000048', survey_number: '66/1A', patta_no: 'PT/2020/1045', area: 2.2, land_use: 'Residential', owner: 'Ganesan K', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.11, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon', coordinates: [[[80.1786,12.7178],[80.1842,12.7180],[80.1844,12.7194],[80.1788,12.7192],[80.1786,12.7178]]] } },

    { type: 'Feature', properties: { parcel_id: 'P049', ulpin: '33230101000049', survey_number: '66/2C', patta_no: 'PT/2018/0912', area: 3.0, land_use: 'Agricultural', owner: 'Kamala Devi', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.09, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon', coordinates: [[[80.1848,12.7180],[80.1906,12.7178],[80.1908,12.7194],[80.1850,12.7192],[80.1848,12.7180]]] } },

    { type: 'Feature', properties: { parcel_id: 'P050', ulpin: '33230101000050', survey_number: '67/1A', patta_no: 'PT/2023/1422', area: 1.8, land_use: 'Industrial', owner: 'Subramanian R', status: 'Conflict', status_detail: 'Environmental Violation', risk_level: 'High', anomaly_score: 0.86, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon', coordinates: [[[80.1912,12.7178],[80.1968,12.7180],[80.1970,12.7194],[80.1914,12.7192],[80.1912,12.7178]]] } },
  ],
} as const;

export const PARCEL_DATA: ParcelData[] = PARCEL_GEOJSON.features.map(
  (f) => f.properties as unknown as ParcelData
);

// ── Conflict overlay geometry (overlap zone between P003 & P008) ────────────────
export const CONFLICT_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { label: 'OVERLAP 42m²', type: 'BOUNDARY_OVERLAP', parcels: 'P003 / P008' },
      geometry: { type: 'Polygon', coordinates: [[[80.1876,12.7302],[80.1886,12.7300],[80.1884,12.7292],[80.1874,12.7294],[80.1876,12.7302]]] } },
  ],
};

// ── Road Network ────────────────────────────────────────────────────────────────
export const ROADS_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { road_id: 'SH49A', name: 'SH-49A Tirupporur Road', road_class: 'STATE_HIGHWAY', surface: 'BT', width_m: 12, authority: 'TN Highways Dept' },
      geometry: { type: 'LineString', coordinates: [[80.1700,12.7295],[80.1750,12.7293],[80.1800,12.7292],[80.1850,12.7290],[80.1900,12.7291],[80.1950,12.7293],[80.2000,12.7295],[80.2050,12.7296]] } },

    { type: 'Feature', properties: { road_id: 'MDR12', name: 'Tirupporur–Vandalur Road', road_class: 'MAJOR_DISTRICT_ROAD', surface: 'BT', width_m: 8, authority: 'TN Highways Dept' },
      geometry: { type: 'LineString', coordinates: [[80.1870,12.7390],[80.1868,12.7350],[80.1866,12.7310],[80.1864,12.7270],[80.1862,12.7230],[80.1860,12.7190],[80.1858,12.7170]] } },

    { type: 'Feature', properties: { road_id: 'VR01', name: 'Kovilpathagai Lane', road_class: 'VILLAGE_ROAD', surface: 'CC', width_m: 5, authority: 'Village Panchayat' },
      geometry: { type: 'LineString', coordinates: [[80.1820,12.7385],[80.1818,12.7345],[80.1816,12.7305],[80.1815,12.7265],[80.1814,12.7225],[80.1812,12.7175]] } },

    { type: 'Feature', properties: { road_id: 'VR02', name: 'Nallur Path', road_class: 'VILLAGE_ROAD', surface: 'WBM', width_m: 4, authority: 'Village Panchayat' },
      geometry: { type: 'LineString', coordinates: [[80.1940,12.7385],[80.1938,12.7345],[80.1936,12.7305],[80.1935,12.7265],[80.1934,12.7225],[80.1932,12.7175]] } },

    { type: 'Feature', properties: { road_id: 'VR03', name: 'Padappai Road', road_class: 'VILLAGE_ROAD', surface: 'BT', width_m: 5, authority: 'Village Panchayat' },
      geometry: { type: 'LineString', coordinates: [[80.1710,12.7222],[80.1770,12.7224],[80.1830,12.7223],[80.1890,12.7224],[80.1950,12.7222],[80.2030,12.7223]] } },

    { type: 'Feature', properties: { road_id: 'VR04', name: 'North Ring Road', road_class: 'VILLAGE_ROAD', surface: 'CC', width_m: 4, authority: 'Village Panchayat' },
      geometry: { type: 'LineString', coordinates: [[80.1710,12.7340],[80.1770,12.7338],[80.1830,12.7336],[80.1890,12.7337],[80.1950,12.7338],[80.2030,12.7340]] } },
  ],
};

// ── Railway ─────────────────────────────────────────────────────────────────────
export const RAILWAY_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { line_id: 'SR_BCH_CGL', name: 'Chennai Beach – Chengalpattu Line', operator: 'Southern Railway', gauge: 'BROAD_GAUGE', gauge_mm: 1676, electrified: true },
      geometry: { type: 'LineString', coordinates: [[80.1690,12.7188],[80.1750,12.7190],[80.1810,12.7191],[80.1870,12.7190],[80.1930,12.7189],[80.1990,12.7191],[80.2050,12.7193]] } },
  ],
};

// ── Village Administrative Boundary ─────────────────────────────────────────────
export const VILLAGE_BOUNDARY_GEOJSON = {
  type: 'Feature',
  properties: { name: 'Tirupporur Revenue Village', taluk: 'Tirupporur', district: 'Chengalpattu', state: 'Tamil Nadu', lgd_code: '33230101' },
  geometry: {
    type: 'Polygon',
    coordinates: [[[80.1705,12.7385],[80.1740,12.7390],[80.1850,12.7392],[80.1960,12.7390],[80.2035,12.7386],[80.2040,12.7350],[80.2038,12.7280],[80.2035,12.7210],[80.2030,12.7172],[80.1960,12.7168],[80.1850,12.7170],[80.1740,12.7172],[80.1708,12.7175],[80.1705,12.7250],[80.1703,12.7320],[80.1705,12.7385]]],
  },
} as const;

// ── Government & Institutional Land Zones ───────────────────────────────────────
export const GOVERNMENT_LAND_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { zone_id: 'GZ01', name: 'Railway Corridor', authority: 'Southern Railway', type: 'RAILWAY_LAND', gazette_ref: 'G.O. Ms. No. 442/1952' },
      geometry: { type: 'Polygon', coordinates: [[[80.1690,12.7184],[80.2050,12.7184],[80.2050,12.7196],[80.1690,12.7196],[80.1690,12.7184]]] } },

    { type: 'Feature', properties: { zone_id: 'GZ02', name: 'Panchayat Union Middle School', authority: 'Dept of School Education', type: 'GOVERNMENT_BUILDING', gazette_ref: 'G.O. Ms. No. 218/1972' },
      geometry: { type: 'Polygon', coordinates: [[[80.1776,12.7338],[80.1822,12.7340],[80.1824,12.7356],[80.1778,12.7354],[80.1776,12.7338]]] } },

    { type: 'Feature', properties: { zone_id: 'GZ03', name: 'Tirupporur Bus Terminus & Revenue Office', authority: 'Revenue Dept (TN)', type: 'GOVERNMENT_BUILDING', gazette_ref: 'G.O. Ms. No. 891/1965' },
      geometry: { type: 'Polygon', coordinates: [[[80.1844,12.7194],[80.1900,12.7192],[80.1902,12.7210],[80.1846,12.7208],[80.1844,12.7194]]] } },

    { type: 'Feature', properties: { zone_id: 'GZ04', name: 'Poramboke Grazing Land', authority: 'Village Panchayat', type: 'PORAMBOKE', gazette_ref: 'Settlement Register 1956' },
      geometry: { type: 'Polygon', coordinates: [[[80.1944,12.7356],[80.2010,12.7354],[80.2012,12.7378],[80.1946,12.7380],[80.1944,12.7356]]] } },

    { type: 'Feature', properties: { zone_id: 'GZ05', name: 'Periya Eri (Village Tank)', authority: 'PWD - Water Resources', type: 'WATER_BODY', gazette_ref: 'PWD/WR/Tank/1948/003' },
      geometry: { type: 'Polygon', coordinates: [[[80.1936,12.7226],[80.1982,12.7224],[80.2020,12.7230],[80.2022,12.7266],[80.1984,12.7268],[80.1940,12.7260],[80.1936,12.7226]]] } },
  ],
};

// ── Tier 2: Governance overlay GeoJSON (retained from original) ─────────────────

export const REGISTRATION_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { parcel_id: 'P001', deed_no: '1042/2019', deed_type: 'SALE_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1825, 12.7312] } },
    { type: 'Feature', properties: { parcel_id: 'P002', deed_no: '0221/2021', deed_type: 'SALE_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1858, 12.7311] } },
    { type: 'Feature', properties: { parcel_id: 'P004', deed_no: '0891/2021', deed_type: 'MORTGAGE_DEED', sro: 'SRO Tirupporur', status: 'ENCUMBERED' }, geometry: { type: 'Point', coordinates: [80.1928, 12.7308] } },
    { type: 'Feature', properties: { parcel_id: 'P008', deed_no: '1204/2018', deed_type: 'SALE_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1868, 12.7277] } },
    { type: 'Feature', properties: { parcel_id: 'P013', deed_no: '0562/2022', deed_type: 'GIFT_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1869, 12.7238] } },
    { type: 'Feature', properties: { parcel_id: 'P031', deed_no: '0612/2016', deed_type: 'SALE_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1742, 12.7316] } },
    { type: 'Feature', properties: { parcel_id: 'P034', deed_no: '1178/2021', deed_type: 'SALE_DEED', sro: 'SRO Tirupporur', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1998, 12.7318] } },
    { type: 'Feature', properties: { parcel_id: 'P048', deed_no: '1045/2020', deed_type: 'SALE_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1814, 12.7186] } },
  ],
};

export const ENCUMBRANCE_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { parcel_id: 'P004', ec_type: 'MORTGAGE', lender: 'SBI Chengalpattu', amount: 1500000, period: '2021–2031' },
      geometry: { type: 'Polygon', coordinates: [[[80.1908,12.7320],[80.1946,12.7325],[80.1948,12.7303],[80.1908,12.7298],[80.1908,12.7320]]] } },
    { type: 'Feature', properties: { parcel_id: 'P007', ec_type: 'LIEN', lender: 'Canara Bank', amount: 800000, period: '2020–2030' },
      geometry: { type: 'Polygon', coordinates: [[[80.1836,12.7296],[80.1860,12.7282],[80.1855,12.7268],[80.1832,12.7272],[80.1836,12.7296]]] } },
    { type: 'Feature', properties: { parcel_id: 'P019', ec_type: 'MORTGAGE', lender: 'Indian Bank', amount: 2200000, period: '2019–2029' },
      geometry: { type: 'Polygon', coordinates: [[[80.1892,12.7354],[80.1938,12.7356],[80.1940,12.7378],[80.1894,12.7376],[80.1892,12.7354]]] } },
  ],
};

export const LITIGATION_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { parcel_id: 'P003', case_no: 'OS-421/2024', court: 'Chengalpattu District Court', type: 'OWNERSHIP_DISPUTE', status: 'STAY_GRANTED' },
      geometry: { type: 'Polygon', coordinates: [[[80.1876,12.7328],[80.1910,12.7332],[80.1912,12.7295],[80.1876,12.7292],[80.1876,12.7328]]] } },
    { type: 'Feature', properties: { parcel_id: 'P012', case_no: 'OS-188/2023', court: 'Chengalpattu District Court', type: 'TITLE_DISPUTE', status: 'PENDING' },
      geometry: { type: 'Polygon', coordinates: [[[80.1828,12.7270],[80.1862,12.7255],[80.1857,12.7232],[80.1823,12.7238],[80.1828,12.7270]]] } },
    { type: 'Feature', properties: { parcel_id: 'P041', case_no: 'OS-067/2025', court: 'Chengalpattu District Court', type: 'TITLE_DISPUTE', status: 'PENDING' },
      geometry: { type: 'Polygon', coordinates: [[[80.2004,12.7210],[80.2018,12.7208],[80.2020,12.7224],[80.2006,12.7222],[80.2004,12.7210]]] } },
  ],
};

export const ZONING_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { zone: 'Residential', plan: 'Tirupporur Master Plan 2041' },
      geometry: { type: 'Polygon', coordinates: [[[80.1840,12.7340],[80.1980,12.7340],[80.1980,12.7305],[80.1840,12.7305],[80.1840,12.7340]]] } },
    { type: 'Feature', properties: { zone: 'Agricultural', plan: 'Tirupporur Master Plan 2041' },
      geometry: { type: 'Polygon', coordinates: [[[80.1700,12.7310],[80.1840,12.7310],[80.1840,12.7170],[80.1700,12.7170],[80.1700,12.7310]]] } },
    { type: 'Feature', properties: { zone: 'Commercial', plan: 'Tirupporur Master Plan 2041' },
      geometry: { type: 'Polygon', coordinates: [[[80.1940,12.7305],[80.2040,12.7305],[80.2040,12.7255],[80.1940,12.7255],[80.1940,12.7305]]] } },
    { type: 'Feature', properties: { zone: 'Industrial', plan: 'Tirupporur Master Plan 2041' },
      geometry: { type: 'Polygon', coordinates: [[[80.1840,12.7210],[80.1940,12.7210],[80.1940,12.7170],[80.1840,12.7170],[80.1840,12.7210]]] } },
  ],
};

export const UTILITY_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { type: 'WATER_MAIN', operator: 'TWAD Board', diameter_mm: 200 },
      geometry: { type: 'LineString', coordinates: [[80.1710,12.7290],[80.1780,12.7288],[80.1850,12.7285],[80.1920,12.7283],[80.1990,12.7280],[80.2040,12.7278]] } },
    { type: 'Feature', properties: { type: 'ELECTRICITY', operator: 'TANGEDCO', voltage_kv: 11 },
      geometry: { type: 'LineString', coordinates: [[80.1710,12.7330],[80.1780,12.7325],[80.1850,12.7318],[80.1920,12.7312],[80.1990,12.7308],[80.2040,12.7305]] } },
    { type: 'Feature', properties: { type: 'GAS_PIPELINE', operator: 'GAIL', pressure: 'medium' },
      geometry: { type: 'LineString', coordinates: [[80.1710,12.7245],[80.1780,12.7248],[80.1850,12.7250],[80.1920,12.7250],[80.1990,12.7248],[80.2040,12.7246]] } },
  ],
};

export const ROW_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { type: 'STATE_HIGHWAY', road_no: 'SH-49A', row_width_m: 30 },
      geometry: { type: 'Polygon', coordinates: [[[80.1700,12.7298],[80.2050,12.7298],[80.2050,12.7288],[80.1700,12.7288],[80.1700,12.7298]]] } },
    { type: 'Feature', properties: { type: 'PANCHAYAT_ROAD', row_width_m: 7 },
      geometry: { type: 'Polygon', coordinates: [[[80.1866,12.7390],[80.1870,12.7390],[80.1870,12.7170],[80.1866,12.7170],[80.1866,12.7390]]] } },
  ],
};

export const ENV_BUFFER_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { type: 'WATERBODY_BUFFER', body: 'Periya Eri (Village Tank)', buffer_m: 100, regulation: 'TN Tanks Act 2007' },
      geometry: { type: 'Polygon', coordinates: [[[80.1930,12.7220],[80.2026,12.7224],[80.2030,12.7272],[80.1988,12.7274],[80.1934,12.7266],[80.1930,12.7220]]] } },
    { type: 'Feature', properties: { type: 'FOREST_BUFFER', body: 'Nallur Reserve Forest Block', buffer_m: 50, regulation: 'Forest Act 1980' },
      geometry: { type: 'Polygon', coordinates: [[[80.1824,12.7352],[80.1892,12.7350],[80.1894,12.7382],[80.1826,12.7384],[80.1824,12.7352]]] } },
  ],
};
