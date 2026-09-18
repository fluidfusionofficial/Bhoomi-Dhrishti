"""
OGC WFS 2.0 and WMS 1.3.0 GetCapabilities stubs.

These endpoints provide standards-compliant capability documents so that
desktop GIS tools (QGIS, ArcGIS, OpenLayers) can discover and load
Bhoomi Dhrishti layers without needing bespoke connectors.

Both documents are minimal but structurally valid according to the
respective OGC schemas.  Full GetFeature / GetMap support is left for a
future sprint.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import Response

router = APIRouter(prefix="/ogc", tags=["OGC"])

_XML_CONTENT_TYPE = "application/xml; charset=utf-8"

# ---------------------------------------------------------------------------
# WFS 2.0.0 GetCapabilities
# ---------------------------------------------------------------------------

_WFS_CAPABILITIES = """\
<?xml version="1.0" encoding="UTF-8"?>
<wfs:WFS_Capabilities
    version="2.0.0"
    xmlns:wfs="http://www.opengis.net/wfs/2.0"
    xmlns:ows="http://www.opengis.net/ows/1.1"
    xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:fes="http://www.opengis.net/fes/2.0"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/wfs/2.0
        http://schemas.opengis.net/wfs/2.0/wfs.xsd">

  <!-- ── Service Identification ─────────────────────────────────────────── -->
  <ows:ServiceIdentification>
    <ows:Title>Bhoomi Dhrishti WFS</ows:Title>
    <ows:Abstract>Land parcel vector feature service for the Bhoomi Dhrishti
      land governance platform (SIH 2026, PS-26014).</ows:Abstract>
    <ows:Keywords>
      <ows:Keyword>land</ows:Keyword>
      <ows:Keyword>parcel</ows:Keyword>
      <ows:Keyword>India</ows:Keyword>
      <ows:Keyword>ULPIN</ows:Keyword>
      <ows:Keyword>cadastre</ows:Keyword>
    </ows:Keywords>
    <ows:ServiceType>WFS</ows:ServiceType>
    <ows:ServiceTypeVersion>2.0.0</ows:ServiceTypeVersion>
    <ows:Fees>NONE</ows:Fees>
    <ows:AccessConstraints>Restricted – Government of India authorized users only</ows:AccessConstraints>
  </ows:ServiceIdentification>

  <!-- ── Service Provider ───────────────────────────────────────────────── -->
  <ows:ServiceProvider>
    <ows:ProviderName>Bhoomi Dhrishti Platform</ows:ProviderName>
    <ows:ServiceContact>
      <ows:ContactInfo>
        <ows:OnlineResource xlink:type="simple" xlink:href="https://bhoomidhrishti.gov.in"/>
      </ows:ContactInfo>
    </ows:ServiceContact>
  </ows:ServiceProvider>

  <!-- ── Operations Metadata ────────────────────────────────────────────── -->
  <ows:OperationsMetadata>
    <ows:Operation name="GetCapabilities">
      <ows:DCP>
        <ows:HTTP>
          <ows:Get xlink:type="simple" xlink:href="/ogc/wfs?"/>
        </ows:HTTP>
      </ows:DCP>
    </ows:Operation>
    <ows:Operation name="DescribeFeatureType">
      <ows:DCP>
        <ows:HTTP>
          <ows:Get xlink:type="simple" xlink:href="/ogc/wfs?"/>
        </ows:HTTP>
      </ows:DCP>
    </ows:Operation>
    <ows:Operation name="GetFeature">
      <ows:DCP>
        <ows:HTTP>
          <ows:Get xlink:type="simple" xlink:href="/ogc/wfs?"/>
        </ows:HTTP>
      </ows:DCP>
      <ows:Parameter name="resultType">
        <ows:AllowedValues>
          <ows:Value>results</ows:Value>
          <ows:Value>hits</ows:Value>
        </ows:AllowedValues>
      </ows:Parameter>
      <ows:Parameter name="outputFormat">
        <ows:AllowedValues>
          <ows:Value>application/json</ows:Value>
          <ows:Value>text/xml; subtype=gml/3.2</ows:Value>
        </ows:AllowedValues>
      </ows:Parameter>
    </ows:Operation>
  </ows:OperationsMetadata>

  <!-- ── Feature Type List ──────────────────────────────────────────────── -->
  <wfs:FeatureTypeList>

    <wfs:FeatureType>
      <wfs:Name>bhoomi:parcels</wfs:Name>
      <wfs:Title>Land Parcels</wfs:Title>
      <wfs:Abstract>Cadastral land parcel boundaries with BDPR / ULPIN identifiers.</wfs:Abstract>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::4326</wfs:DefaultCRS>
      <ows:WGS84BoundingBox>
        <ows:LowerCorner>68.1766 6.7535</ows:LowerCorner>
        <ows:UpperCorner>97.4026 35.6745</ows:UpperCorner>
      </ows:WGS84BoundingBox>
    </wfs:FeatureType>

    <wfs:FeatureType>
      <wfs:Name>bhoomi:admin_districts</wfs:Name>
      <wfs:Title>Administrative Boundaries</wfs:Title>
      <wfs:Abstract>LGD administrative hierarchy polygons (state, district, subdistrict, village).</wfs:Abstract>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::4326</wfs:DefaultCRS>
      <ows:WGS84BoundingBox>
        <ows:LowerCorner>68.1766 6.7535</ows:LowerCorner>
        <ows:UpperCorner>97.4026 35.6745</ows:UpperCorner>
      </ows:WGS84BoundingBox>
    </wfs:FeatureType>

    <wfs:FeatureType>
      <wfs:Name>bhoomi:restriction_zones</wfs:Name>
      <wfs:Title>Restriction Zones</wfs:Title>
      <wfs:Abstract>Protected areas, buffer zones, and regulatory exclusion areas.</wfs:Abstract>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::4326</wfs:DefaultCRS>
      <ows:WGS84BoundingBox>
        <ows:LowerCorner>68.1766 6.7535</ows:LowerCorner>
        <ows:UpperCorner>97.4026 35.6745</ows:UpperCorner>
      </ows:WGS84BoundingBox>
    </wfs:FeatureType>

    <wfs:FeatureType>
      <wfs:Name>bhoomi:topology_conflicts</wfs:Name>
      <wfs:Title>Topology Conflicts</wfs:Title>
      <wfs:Abstract>Open boundary overlap and gap conflicts between parcels.</wfs:Abstract>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::4326</wfs:DefaultCRS>
      <ows:WGS84BoundingBox>
        <ows:LowerCorner>68.1766 6.7535</ows:LowerCorner>
        <ows:UpperCorner>97.4026 35.6745</ows:UpperCorner>
      </ows:WGS84BoundingBox>
    </wfs:FeatureType>

  </wfs:FeatureTypeList>

</wfs:WFS_Capabilities>
"""

# ---------------------------------------------------------------------------
# WMS 1.3.0 GetCapabilities
# ---------------------------------------------------------------------------

_WMS_CAPABILITIES = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE WMT_MS_Capabilities SYSTEM "http://schemas.opengis.net/wms/1.3.0/capabilities_1_3_0.dtd">
<WMS_Capabilities version="1.3.0"
    xmlns="http://www.opengis.net/wms"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/wms
        http://schemas.opengis.net/wms/1.3.0/capabilities_1_3_0.xsd">

  <Service>
    <Name>WMS</Name>
    <Title>Bhoomi Dhrishti WMS</Title>
    <Abstract>Web Map Service for Bhoomi Dhrishti land parcel layers.</Abstract>
    <KeywordList>
      <Keyword>land</Keyword>
      <Keyword>parcel</Keyword>
      <Keyword>cadastre</Keyword>
      <Keyword>India</Keyword>
    </KeywordList>
    <OnlineResource xlink:type="simple" xlink:href="/ogc/wms?"/>
    <Fees>none</Fees>
    <AccessConstraints>Restricted – Government of India authorized users only</AccessConstraints>
    <MaxWidth>4096</MaxWidth>
    <MaxHeight>4096</MaxHeight>
  </Service>

  <Capability>
    <Request>
      <GetCapabilities>
        <Format>text/xml</Format>
        <DCPType>
          <HTTP>
            <Get><OnlineResource xlink:type="simple" xlink:href="/ogc/wms?"/></Get>
          </HTTP>
        </DCPType>
      </GetCapabilities>
      <GetMap>
        <Format>image/png</Format>
        <Format>image/jpeg</Format>
        <DCPType>
          <HTTP>
            <Get><OnlineResource xlink:type="simple" xlink:href="/ogc/wms?"/></Get>
          </HTTP>
        </DCPType>
      </GetMap>
    </Request>

    <Exception>
      <Format>XML</Format>
      <Format>INIMAGE</Format>
    </Exception>

    <Layer>
      <Title>Bhoomi Dhrishti</Title>
      <CRS>EPSG:4326</CRS>
      <CRS>EPSG:3857</CRS>
      <EX_GeographicBoundingBox>
        <westBoundLongitude>68.1766</westBoundLongitude>
        <eastBoundLongitude>97.4026</eastBoundLongitude>
        <southBoundLatitude>6.7535</southBoundLatitude>
        <northBoundLatitude>35.6745</northBoundLatitude>
      </EX_GeographicBoundingBox>

      <Layer queryable="1" opaque="0">
        <Name>parcels</Name>
        <Title>Land Parcels</Title>
        <Abstract>Cadastral land parcel boundaries.</Abstract>
        <CRS>EPSG:4326</CRS>
        <EX_GeographicBoundingBox>
          <westBoundLongitude>68.1766</westBoundLongitude>
          <eastBoundLongitude>97.4026</eastBoundLongitude>
          <southBoundLatitude>6.7535</southBoundLatitude>
          <northBoundLatitude>35.6745</northBoundLatitude>
        </EX_GeographicBoundingBox>
      </Layer>

      <Layer queryable="1" opaque="0">
        <Name>admin_districts</Name>
        <Title>Administrative Boundaries</Title>
        <Abstract>LGD administrative hierarchy polygons.</Abstract>
        <CRS>EPSG:4326</CRS>
        <EX_GeographicBoundingBox>
          <westBoundLongitude>68.1766</westBoundLongitude>
          <eastBoundLongitude>97.4026</eastBoundLongitude>
          <southBoundLatitude>6.7535</southBoundLatitude>
          <northBoundLatitude>35.6745</northBoundLatitude>
        </EX_GeographicBoundingBox>
      </Layer>

      <Layer queryable="0" opaque="0">
        <Name>restriction_zones</Name>
        <Title>Restriction Zones</Title>
        <Abstract>Protected areas and regulatory buffer zones.</Abstract>
        <CRS>EPSG:4326</CRS>
        <EX_GeographicBoundingBox>
          <westBoundLongitude>68.1766</westBoundLongitude>
          <eastBoundLongitude>97.4026</eastBoundLongitude>
          <southBoundLatitude>6.7535</southBoundLatitude>
          <northBoundLatitude>35.6745</northBoundLatitude>
        </EX_GeographicBoundingBox>
      </Layer>

    </Layer>
  </Capability>

</WMS_Capabilities>
"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/wfs",
    summary="OGC WFS 2.0.0 GetCapabilities",
    response_class=Response,
)
async def wfs_capabilities(
    service: str = Query("WFS", description="Must be WFS"),
    request: str = Query("GetCapabilities", description="Must be GetCapabilities"),
) -> Response:
    """
    Returns a WFS 2.0.0 GetCapabilities document.

    Accepted by QGIS, ArcGIS Pro, OpenLayers, and other OGC-compliant clients.
    """
    return Response(content=_WFS_CAPABILITIES, media_type=_XML_CONTENT_TYPE)


@router.get(
    "/wms",
    summary="OGC WMS 1.3.0 GetCapabilities",
    response_class=Response,
)
async def wms_capabilities(
    service: str = Query("WMS", description="Must be WMS"),
    request: str = Query("GetCapabilities", description="Must be GetCapabilities"),
) -> Response:
    """
    Returns a WMS 1.3.0 GetCapabilities document.

    Allows desktop GIS clients to render Bhoomi Dhrishti layers as raster maps.
    """
    return Response(content=_WMS_CAPABILITIES, media_type=_XML_CONTENT_TYPE)
