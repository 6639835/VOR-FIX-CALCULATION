"""
File operations for reading and parsing navigation data files.
"""

from pathlib import Path
from typing import Optional

from .constants import (FIX_FILE_IDENTIFIER_INDEX, FIX_FILE_LAT_INDEX, FIX_FILE_LON_INDEX,
                        NAV_FILE_IDENTIFIER_INDEX, NAV_FILE_LAT_INDEX, NAV_FILE_LON_INDEX,
                        NAV_FILE_TENTH_PART_INDEX, FileType)
from .models import NavAidEntry


class DataFileReader:
    """Reader for navigation data files (NAV and FIX)."""

    @staticmethod
    def read_file(file_path: str, file_type: FileType, identifier: str) -> list[NavAidEntry]:
        """
        Read and parse navigation data file, searching for specific identifier.

        Args:
            file_path: Path to the data file
            file_type: Type of file (NAV or FIX)
            identifier: Identifier to search for

        Returns:
            List of matching navigation aid entries

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine indices based on file type
        if file_type == FileType.NAV:
            lat_idx = NAV_FILE_LAT_INDEX
            lon_idx = NAV_FILE_LON_INDEX
            id_idx = NAV_FILE_IDENTIFIER_INDEX
            name_idx = NAV_FILE_TENTH_PART_INDEX
        else:  # FIX
            lat_idx = FIX_FILE_LAT_INDEX
            lon_idx = FIX_FILE_LON_INDEX
            id_idx = FIX_FILE_IDENTIFIER_INDEX
            name_idx = None

        matching_entries = []

        with open(file_path, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, 1):
                parts = line.strip().split()

                # Skip empty lines
                if not parts:
                    continue

                # Check if line has enough parts
                if len(parts) <= max(lat_idx, lon_idx, id_idx):
                    continue

                # Check if identifier matches
                if parts[id_idx].upper() != identifier.upper():
                    continue

                try:
                    # Parse coordinates
                    latitude = float(parts[lat_idx])
                    longitude = float(parts[lon_idx])

                    # Get name if available
                    name = None
                    if name_idx is not None and len(parts) > name_idx:
                        name = parts[name_idx]

                    # Create entry
                    entry = NavAidEntry(
                        type_code=parts[0],
                        latitude=latitude,
                        longitude=longitude,
                        identifier=parts[id_idx],
                        name=name,
                        raw_parts=parts,
                    )
                    matching_entries.append(entry)

                except (ValueError, IndexError) as e:
                    raise ValueError(f"Invalid data format at line {line_num}: {e}") from e

        return matching_entries

    @staticmethod
    def validate_file_path(file_path: str) -> Optional[str]:
        """
        Validate that a file path exists and is readable.

        Args:
            file_path: Path to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not file_path:
            return "No file path provided"

        path = Path(file_path)
        if not path.exists():
            return f"File does not exist: {file_path}"

        if not path.is_file():
            return f"Path is not a file: {file_path}"

        try:
            with open(file_path, "r", encoding="utf-8"):
                pass
        except PermissionError:
            return f"No permission to read file: {file_path}"
        except Exception as e:
            return f"Error accessing file: {e}"

        return None
