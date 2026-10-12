#!/usr/bin/env python3
"""Fetch pinned Concordia sources, build six DARs, and verify the local dependencies."""

import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "daml/concordia/lib"
REVISION = "ac516498da433f1e6b211f5b7c6cc9c9ba2ec549"
ARCHIVE_SHA256 = "6b135273c4f746511a9d2b92d46722b550fb0a23a1fcc84d6bb3ca42d2d0cb0e"
URL = f"https://codeload.github.com/unlockitio/concordia/tar.gz/{REVISION}"
PACKAGES = (
    ("cap-core/types", "cap-core-types-0.1.0.dar"),
    ("cap-core/utils", "cap-core-utils-0.1.0.dar"),
    ("cap-governance/types", "cap-governance-types-0.1.0.dar"),
    ("cap-governance/interfaces/executable", "cap-governance-executable-v1-0.1.0.dar"),
    ("cap-governance/interfaces/action", "cap-governance-action-v1-0.1.0.dar"),
    ("cap-governance/utils", "cap-governance-utils-0.1.0.dar"),
)
CHECKSUMS = {
    "splice-api-token-metadata-v1-1.0.0.dar": "455eb160cb5abd4ae9918a6fbb9dad471f721adda39f0e5c76feef08d05637fc",
    "splice-util-0.1.7.dar": "96ba05e6bf7f41b6ab2cf0d54bbfe2f479980cac0fc4a1c4768652baed091f46",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    dpm = os.environ.get("DPM", str(Path.home() / ".dpm/bin/dpm"))
    with urllib.request.urlopen(URL, timeout=120) as response:
        archive = response.read()
    if digest(archive) != ARCHIVE_SHA256:
        raise ValueError("Concordia source archive checksum mismatch")
    with tempfile.TemporaryDirectory(prefix="syncvotes-concordia-") as temporary:
        source = Path(temporary) / "concordia"
        source.mkdir()
        prefix = f"concordia-{REVISION}/"
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            for member in tar:
                if not member.isfile() or not member.name.startswith(prefix):
                    continue
                relative = Path(member.name[len(prefix):])
                if ".." in relative.parts or relative.is_absolute():
                    raise ValueError("Unsafe source archive path")
                if relative.parts[:1] not in (("cap-core",), ("cap-governance",), ("lib",)):
                    continue
                target = source / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as input_file, target.open("wb") as output:
                    shutil.copyfileobj(input_file, output)
        for filename in CHECKSUMS:
            binary = source / "lib" / filename
            if digest(binary.read_bytes()) != CHECKSUMS[filename]:
                raise ValueError(f"Upstream Splice DAR checksum mismatch: {filename}")
        (source / "multi-package.yaml").write_text(
            "packages:\n" + "".join(f"- ./{folder}\n" for folder, _ in PACKAGES)
        )
        subprocess.run([dpm, "build", "--all"], check=True, cwd=source)
        expected = {
            filename: checksum
            for checksum, filename in (
                line.split() for line in (LIB / "SHA256SUMS").read_text().splitlines()
            )
        }
        if set(expected) != {filename for _, filename in PACKAGES} | set(CHECKSUMS):
            raise ValueError("Dependency checksum list does not match the build inputs")
        outputs = {
            filename: source / folder / ".daml/dist" / filename
            for folder, filename in PACKAGES
        }
        outputs.update({filename: source / "lib" / filename for filename in CHECKSUMS})
        for filename, built in outputs.items():
            if digest(built.read_bytes()) != expected[filename]:
                raise ValueError(f"Generated DAR checksum mismatch: {filename}")
        LIB.mkdir(parents=True, exist_ok=True)
        for filename, built in outputs.items():
            shutil.copyfile(built, LIB / filename)
            print(f"{expected[filename]}  {filename}")


if __name__ == "__main__":
    main()
