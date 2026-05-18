from exiftoolService import ExifToolService


def get_image_metadata(image_path):
    exif_metadata = ExifToolService.read_metadata(image_path)
    metadata = {}

    latitude = exif_metadata.get("GPSLatitude")
    longitude = exif_metadata.get("GPSLongitude")
    created_date = exif_metadata.get("DateTimeOriginal")
    city = exif_metadata.get("City")
    country = exif_metadata.get("Country") or exif_metadata.get("Country-PrimaryLocationName")

    if latitude is not None and longitude is not None:
        metadata["GPSLatitude"] = float(latitude)
        metadata["GPSLongitude"] = float(longitude)

    if created_date:
        metadata["CreatedDate"] = created_date

    if city:
        metadata["City"] = city

    if country:
        metadata["Country"] = country

    return metadata


def apply_metadata_to_image(image_path, metadata):
    latitude = metadata.get("GPSLatitude")
    longitude = metadata.get("GPSLongitude")
    city = metadata.get("City")
    country = metadata.get("Country")

    if latitude is None or longitude is None:
        return

    ExifToolService.write_gps_metadata(
        image_path,
        float(latitude),
        float(longitude),
        city=city,
        country=country,
    )