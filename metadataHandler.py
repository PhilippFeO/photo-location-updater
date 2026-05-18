from exiftoolService import ExifToolService
import re


def _normalize_exif_datetime(value):
    if not value:
        return None

    text = str(value).strip()
    # Normalize to format expected by takeout matcher: YYYY:MM:DD HH:MM:SS
    match = re.search(r"\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}", text)
    if match:
        return match.group(0)

    return text


def _extract_created_date(exif_metadata):
    date_candidates = [
        "DateTimeOriginal",
        "SubSecDateTimeOriginal",
        "CreateDate",
        "DateCreated",
        "MediaCreateDate",
        "TrackCreateDate",
        "CreationDate",
        "ModifyDate",
        "FileCreateDate",
        "FileModifyDate",
    ]

    for key in date_candidates:
        value = exif_metadata.get(key)
        if value:
            normalized = _normalize_exif_datetime(value)
            if normalized:
                return normalized

    return None


def get_image_metadata(image_path):
    exif_metadata = ExifToolService.read_metadata(image_path)
    metadata = {}

    latitude = exif_metadata.get("GPSLatitude")
    longitude = exif_metadata.get("GPSLongitude")
    created_date = _extract_created_date(exif_metadata)
    city = exif_metadata.get("City")
    country = exif_metadata.get("Country") or exif_metadata.get("Country-PrimaryLocationName")
    country_code = exif_metadata.get("Country-PrimaryLocationCode") or exif_metadata.get("LocationCreatedCountryCode")

    if latitude is not None and longitude is not None:
        metadata["GPSLatitude"] = float(latitude)
        metadata["GPSLongitude"] = float(longitude)

    if created_date:
        metadata["CreatedDate"] = created_date

    if city:
        metadata["City"] = city

    if country:
        metadata["Country"] = country

    if country_code:
        metadata["CountryCode"] = country_code

    return metadata


def apply_metadata_to_image(image_path, metadata):
    latitude = metadata.get("GPSLatitude")
    longitude = metadata.get("GPSLongitude")
    city = metadata.get("City")
    country = metadata.get("Country")
    country_code = metadata.get("CountryCode")

    if latitude is None or longitude is None:
        return

    ExifToolService.write_gps_metadata(
        image_path,
        float(latitude),
        float(longitude),
        city=city,
        country=country,
        country_code=country_code,
    )