import json
import shutil
from argparse import ArgumentParser
from pathlib import Path


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "png_dir",
        type=lambda value: Path(value).resolve(strict=True),
    )
    parser.add_argument(
        "dedupe_dir",
        type=lambda value: Path(value).resolve(strict=True),
    )
    args = parser.parse_args()

    atlas_path = args.png_dir / "dedupe.json"
    with atlas_path.open("r") as f:
        texture_atlas = json.load(f)

    for texture_name, texture_infos in texture_atlas.items():
        src_dir = args.png_dir / texture_name
        dst_dir = args.dedupe_dir / texture_name
        dst_dir.mkdir(exist_ok=True)
        for ti in texture_infos:
            if "duplicate" in ti:
                continue
            filename = f"{texture_name}-{ti['mission']}-{ti['package']}.png"
            src_path = src_dir / filename
            dst_path = dst_dir / filename
            shutil.copy(src_path, dst_path, follow_symlinks=False)


if __name__ == "__main__":
    main()
