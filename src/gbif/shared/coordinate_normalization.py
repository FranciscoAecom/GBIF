from __future__ import annotations


BRAZIL_BBOX = {
    "min_latitude": -34.0,
    "max_latitude": 6.0,
    "min_longitude": -74.0,
    "max_longitude": -28.0,
}


def normalize_brazil_coordinate(latitude, longitude, has_geospatial_issue=None) -> dict:
    if not _is_number(latitude) or not _is_number(longitude):
        return _result(None, None, False, "MISSING_OR_INVALID", "missing_or_invalid_coordinate")

    lat = float(latitude)
    lon = float(longitude)
    if not _is_valid_world_coordinate(lat, lon):
        return _result(None, None, False, "INVALID_WORLD_COORDINATE", "outside_world_coordinate_range")

    if _is_inside_brazil_bbox(lat, lon) and has_geospatial_issue is not True:
        return _result(lat, lon, False, "VALID_ORIGINAL", None)

    if _is_valid_world_coordinate(lon, lat) and _is_inside_brazil_bbox(lon, lat):
        return _result(lon, lat, True, "POSSIBLE_SWAPPED", "latitude_longitude_probably_swapped")

    if has_geospatial_issue is True:
        return _result(None, None, False, "GBIF_GEOSPATIAL_ISSUE", "gbif_geospatial_issue")

    return _result(None, None, False, "OUTSIDE_BRAZIL_BBOX", "outside_brazil_approximate_bbox")


def _result(latitude, longitude, was_swapped: bool, status: str, issue: str | None) -> dict:
    return {
        "acm_decimal_latitude": latitude,
        "acm_decimal_longitude": longitude,
        "acm_coordinate_was_swapped": was_swapped,
        "acm_coordinate_status": status,
        "acm_coordinate_issue": issue,
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
