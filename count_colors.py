import json
from argparse import ArgumentParser
from pathlib import Path
from PIL import Image
from tqdm import tqdm


def count_colors_full(texture_path: Path) -> int:
    img = Image.open(texture_path)
    unique_colors = set()
    w, h = img.size
    for x in range(w):
        for y in range(h):
            pixel = img.getpixel((x, y))
            unique_colors.add(pixel[0:3])
    return len(unique_colors)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "png_dir",
        type=lambda value: Path(value).resolve(strict=True),
    )
    args = parser.parse_args()

    atlas_path = args.png_dir / "atlas.json"
    with atlas_path.open("r") as f:
        texture_atlas = json.load(f)

    backup_path = args.png_dir / "atlas.bak"
    with backup_path.open("w") as f:
        json.dump(texture_atlas, f, indent=2)

    for texture_name, texture_infos in tqdm(sorted(texture_atlas.items())):
        for texture_info in texture_infos:
            filename = f"{texture_name}-{texture_info['mission']}-{texture_info['package']}.png"
            texture_path = args.png_dir / texture_name / filename
            count = count_colors_full(texture_path)
            texture_info["colors"] = count

    with atlas_path.open("w") as f:
        json.dump(texture_atlas, f, indent=2)


if __name__ == "__main__":
    main()
