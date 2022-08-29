import subprocess
from argparse import ArgumentParser
from pathlib import Path


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "zbd_dir",
        type=lambda value: Path(value).resolve(strict=True),
    )
    parser.add_argument(
        "unzbd_exe", type=lambda value: Path(value).resolve(strict=True)
    )
    args = parser.parse_args()

    for mission_dir in args.zbd_dir.glob("m*"):
        for texture_zbd in mission_dir.glob("*texture*.zbd"):
            texture_zip = texture_zbd.with_suffix(".zip")
            print(texture_zbd, texture_zip)
            cmd = [str(args.unzbd_exe), "textures", str(texture_zbd), str(texture_zip)]
            subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
