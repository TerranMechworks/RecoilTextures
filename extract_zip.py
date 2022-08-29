import json
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from shutil import copyfileobj
from zipfile import ZipFile


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "zbd_dir",
        type=lambda value: Path(value).resolve(strict=True),
    )
    parser.add_argument(
        "png_dir",
        type=lambda value: Path(value).resolve(strict=True),
    )
    args = parser.parse_args()

    texture_atlas = defaultdict(list)

    for mission_zbd_dir in args.zbd_dir.glob("m*"):
        mission_name = mission_zbd_dir.name
        for package_path in mission_zbd_dir.glob("*texture*.zip"):
            package_name = package_path.stem

            print(mission_name, package_name)
            with ZipFile(package_path, mode="r") as zip:
                # load manifest
                with zip.open("manifest.json", mode="r") as f:
                    manifest = json.load(f)
                texture_infos = {ti["name"]: ti for ti in manifest["texture_infos"]}

                # load textures
                for info in zip.infolist():
                    if info.filename == "manifest.json":
                        continue
                    texture_name, _, ext = info.filename.rpartition(".")
                    assert ext == "png", info.filename
                    ti = texture_infos[texture_name]

                    ti["mission"] = mission_name
                    ti["package"] = package_name
                    del ti["image_loaded"]
                    del ti["alpha_loaded"]
                    del ti["palette_loaded"]

                    texture_dir = args.png_dir / texture_name
                    texture_dir.mkdir(exist_ok=True)

                    png_name = f"{texture_name}-{mission_name}-{package_name}.png"
                    png_path = texture_dir / png_name
                    with zip.open(info) as fsrc, png_path.open("wb") as fdst:
                        copyfileobj(fsrc, fdst)

                    texture_atlas[texture_name].append(ti)

    atlas_path = args.png_dir / "atlas.json"
    with atlas_path.open("w") as f:
        json.dump(texture_atlas, f, indent=2)


if __name__ == "__main__":
    main()
