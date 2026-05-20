import json
import os
import shutil
import subprocess
import threading
import atexit


class ExifToolService:
    _process = None
    _lock = threading.Lock()
    _command_counter = 0
    _atexit_registered = False

    @staticmethod
    def _get_exiftool_command():
        project_dir = os.path.dirname(os.path.abspath(__file__))
        local_candidates = [
            os.path.join(project_dir, "exiftoll.exe"),
            os.path.join(project_dir, "exiftool.exe"),
            os.path.join(project_dir, "exiftool-13.58_64", "exiftool.exe"),
        ]

        for candidate in local_candidates:
            if os.path.isfile(candidate):
                return candidate

        exiftool_cmd = shutil.which("exiftool") or shutil.which("exiftool.exe")
        if not exiftool_cmd:
            raise RuntimeError(
                "ExifTool executable not found. Add exiftool.exe to the project folder, "
                "or install ExifTool and ensure it is in PATH."
            )
        return exiftool_cmd

    @staticmethod
    def _build_windows_hidden_process_kwargs():
        process_kwargs = {}
        if os.name == "nt":
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process_kwargs["startupinfo"] = startup_info
            process_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return process_kwargs

    @staticmethod
    def _ensure_process():
        if ExifToolService._process and ExifToolService._process.poll() is None:
            return ExifToolService._process

        command = [
            ExifToolService._get_exiftool_command(),
            "-stay_open",
            "True",
            "-@",
            "-",
            "-common_args",
            "-charset",
            "filename=utf8",
            "-charset",
            "exif=utf8",
        ]

        ExifToolService._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1,
            **ExifToolService._build_windows_hidden_process_kwargs(),
        )

        if not ExifToolService._atexit_registered:
            atexit.register(ExifToolService.close)
            ExifToolService._atexit_registered = True

        return ExifToolService._process

    @staticmethod
    def _run_exiftool(args):
        with ExifToolService._lock:
            process = ExifToolService._ensure_process()
            ExifToolService._command_counter += 1
            command_id = ExifToolService._command_counter
            ready_token = f"{{ready{command_id}}}"

            payload = "".join(f"{arg}\n" for arg in args)
            payload += f"-execute{command_id}\n"

            process.stdin.write(payload)
            process.stdin.flush()

            output_lines = []
            while True:
                line = process.stdout.readline()
                if line == "":
                    raise RuntimeError("ExifTool process ended unexpectedly.")

                if line.strip() == ready_token:
                    break

                output_lines.append(line)

            output = "".join(output_lines)
            if "Error" in output:
                raise RuntimeError(f"ExifTool failed: {output.strip()}")

            return output

    @staticmethod
    def close():
        with ExifToolService._lock:
            process = ExifToolService._process
            if not process or process.poll() is not None:
                ExifToolService._process = None
                return

            process.stdin.write("-stay_open\n")
            process.stdin.write("False\n")
            process.stdin.flush()
            process.wait(timeout=2)
            ExifToolService._process = None

    @staticmethod
    def read_metadata(image_path):
        output = ExifToolService._run_exiftool(
            [
                "-j",
                "-n",
                "-GPSLatitude",
                "-GPSLongitude",
                "-DateTimeOriginal",
                "-SubSecDateTimeOriginal",
                "-CreateDate",
                "-DateCreated",
                "-MediaCreateDate",
                "-TrackCreateDate",
                "-Keys:CreationDate",
                "-ModifyDate",
                "-FileCreateDate",
                "-FileModifyDate",
                "-City",
                "-Country",
                "-Country-PrimaryLocationName",
                "-Country-PrimaryLocationCode",
                "-XMP-iptcExt:LocationCreatedCountryCode",
                image_path,
            ]
        )

        parsed = json.loads(output)
        if not parsed:
            return {}

        return parsed[0]

    @staticmethod
    def write_gps_metadata(image_path, latitude, longitude, city=None, country=None, country_code=None):
        latitude_ref = "N" if latitude >= 0 else "S"
        longitude_ref = "E" if longitude >= 0 else "W"

        args = [
            "-overwrite_original",
            f"-GPSLatitude={abs(latitude)}",
            f"-GPSLatitudeRef={latitude_ref}",
            f"-GPSLongitude={abs(longitude)}",
            f"-GPSLongitudeRef={longitude_ref}",
        ]

        if city and city != "Unknown":
            args.extend(
                [
                    f"-IPTC:City={city}",
                    f"-XMP:City={city}",
                    f"-XMP-iptcExt:LocationCreatedCity={city}",
                ]
            )

        if country and country != "Unknown":
            args.extend(
                [
                    f"-IPTC:Country-PrimaryLocationName={country}",
                    f"-XMP:Country={country}",
                    f"-XMP-iptcExt:LocationCreatedCountryName={country}",
                ]
            )

        if country_code:
            args.extend(
                [
                    f"-Country-PrimaryLocationCode={country_code}",
                    f"-IPTC:Country-PrimaryLocationCode={country_code}",
                    f"-XMP-iptcExt:LocationCreatedCountryCode={country_code}",
                ]
            )

        args.append(image_path)

        ExifToolService._run_exiftool(
            args
        )