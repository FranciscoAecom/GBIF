from __future__ import annotations


BRAZIL_BBOX = {
    "min_latitude": -34.0,
    "max_latitude": 6.0,
    "min_longitude": -74.0,
    "max_longitude": -28.0,
}


def normalize_brazil_coordinate(latitude, longitude, has_geospatial_issue=None) -> dict:
    if not _is_number(latitude) or not _is_number(longitude):
        return _result(None, None)

    lat = float(latitude)
    lon = float(longitude)
    if not _is_valid_world_coordinate(lat, lon):
        return _result(None, None)

    if _is_inside_brazil_bbox(lat, lon) and has_geospatial_issue is not True:
        return _result(lat, lon)

    if _is_valid_world_coordinate(lon, lat) and _is_inside_brazil_bbox(lon, lat):
        return _result(lon, lat)

    if has_geospatial_issue is True:
        return _result(None, None)

    return _result(None, None)


def _result(latitude, longitude) -> dict:
    return {
        "acm_decimal_latitude": latitude,
        "acm_decimal_longitude": longitude,
    }


def _is_number(value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _is_valid_world_coordinate(latitude: float, longitude: float) -> bool:
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def _is_inside_brazil_bbox(latitude: float, longitude: float) -> bool:
    return (
        BRAZIL_BBOX["min_latitude"] <= latitude <= BRAZIL_BBOX["max_latitude"]
        and BRAZIL_BBOX["min_longitude"] <= longitude <= BRAZIL_BBOX["max_longitude"]
    )
