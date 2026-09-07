"""
Research Archive Checkpoint
===========================

Purpose
-------
Create reproducible archival checkpoints for completed research stages.

Each checkpoint records:
    1. Preserved files
    2. Dataset metadata
    3. SHA-256 checksums
    4. Checkpoint manifest
    5. Creation timestamp

IMPORTANT
---------
This module does NOT automatically publish third-party datasets.
Publication/archiving to Zenodo is handled separately after
checking source licensing and redistribution conditions.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def sha256_file(
    path: str | Path,
    chunk_size: int = 1024 * 1024
) -> str:
    """
    Calculate SHA-256 checksum for a file.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Expected a file, not a directory: {path}"
        )

    digest = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def _safe_stage_name(stage: str) -> str:
    """
    Convert a stage name into a filesystem-safe name.
    """
    return "".join(
        char if char.isalnum() or char in "-_"
        else "_"
        for char in stage
    )


def create_checkpoint(
    stage: str,
    files: Iterable[str | Path],
    metadata: dict,
    archive_root: str | Path = "research_archive",
) -> Path:
    """
    Create a timestamped research archive checkpoint.

    Parameters
    ----------
    stage:
        Name of the completed research stage.

    files:
        Files that must be preserved.

    metadata:
        Dictionary describing the research stage.

    archive_root:
        Root folder for checkpoints.

    Returns
    -------
    Path
        Location of the created checkpoint.
    """

    if not stage.strip():
        raise ValueError(
            "Stage name cannot be empty."
        )

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    stage_name = _safe_stage_name(stage)

    checkpoint_dir = (
        Path(archive_root)
        / f"{timestamp}_{stage_name}"
    )

    files_dir = checkpoint_dir / "files"

    checkpoint_dir.mkdir(
        parents=True,
        exist_ok=False
    )

    files_dir.mkdir(
        parents=True,
        exist_ok=False
    )

    manifest = {
        "checkpoint_created_utc": timestamp,
        "stage": stage,
        "metadata": metadata,
        "files": [],
    }

    for file_path in files:

        source = Path(file_path)

        if not source.exists():
            raise FileNotFoundError(
                f"Source file does not exist: {source}"
            )

        if not source.is_file():
            raise ValueError(
                f"Expected a file: {source}"
            )

        destination = files_dir / source.name

        shutil.copy2(
            source,
            destination
        )

        manifest["files"].append(
            {
                "filename": source.name,
                "size_bytes": destination.stat().st_size,
                "sha256": sha256_file(
                    destination
                ),
            }
        )

    # --------------------------------------------------------
    # Save manifest
    # --------------------------------------------------------

    manifest_path = (
        checkpoint_dir / "manifest.json"
    )

    with manifest_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Save metadata separately
    # --------------------------------------------------------

    metadata_path = (
        checkpoint_dir / "metadata.json"
    )

    with metadata_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False
        )

    return checkpoint_dir
