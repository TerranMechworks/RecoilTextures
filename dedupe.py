import json
import re
import math
import subprocess
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict
from tqdm import tqdm

FFMPEG_BIN = "ffmpeg"
SSIM_REGEX = re.compile(
    r"^\[Parsed_ssim_0 @ 0x[0-9a-fA-F]+\] SSIM "
    r"R:(?P<r1>-?\d+\.\d+) \((?P<r2>inf|-?\d+\.\d+)\) "
    r"G:(?P<g1>-?\d+\.\d+) \((?P<g2>inf|-?\d+\.\d+)\) "
    r"B:(?P<b1>-?\d+\.\d+) \((?P<b2>inf|-?\d+\.\d+)\) "
    r"All:(?P<all1>-?\d+\.\d+) \((?P<all2>inf|-?\d+\.\d+)\)$"
)


def ffmpeg_ssim(a: Path, b: Path) -> float:
    cmd = [
        FFMPEG_BIN,
        "-hide_banner",
        "-i",
        str(a),
        "-i",
        str(b),
        "-lavfi",
        "ssim",
        "-f",
        "null",
        "-",
    ]
    completed = subprocess.run(cmd, check=True, capture_output=True, encoding="utf-8")
    # ffmpeg output goes to stderr
    lines = completed.stderr.splitlines()
    ssim_result = lines[-1]
    m = SSIM_REGEX.match(ssim_result)
    # if this fails, it's a bug because we couldn't parse the output
    assert m, ssim_result
    return float(m.group("all1"))


def mission_number(mission: str) -> int:
    assert mission.startswith("m")
    return int(mission[1:])


# "best" to "worst"
PACKAGE_NAMES = [
    "rtexture4",
    "rtexture2",
    "texture8",
    "texture6",
    "texture4",
    "texture2",
]
PACKAGE_SCORE_MIN = {p: i for (i, p) in enumerate(PACKAGE_NAMES)}


def package_number(package: str) -> int:
    return PACKAGE_SCORE_MIN[package]


def maybe_same(a: Any, b: Any) -> bool:
    # we want to test as many conditions here as possible,
    # because the ffmpeg SSIM test is expensive. at this stage,
    # we are only checking for very similar images. however,
    # even with all these conditions it isn't enough to
    # actually say the images are the same.
    return bool(
        a["width"] == b["width"]
        and a["height"] == b["height"]
        and a["stretch"] == b["stretch"]
        and a["alpha"] == b["alpha"]
        and a["colors"] == b["colors"]
    )


def dedupe_missions(png_dir: Path, texture_atlas: Any) -> None:
    for texture_name, texture_infos in tqdm(sorted(texture_atlas.items())):
        # group texture infos by package
        ti_by_package = defaultdict(list)
        for ti in texture_infos:
            # ignore duplicates
            if "duplicate" in ti:
                continue
            ti_by_package[ti["package"]].append(ti)
        # sort them by mission number
        for package_tis in ti_by_package.values():
            package_tis.sort(key=lambda ti: mission_number(ti["mission"]))
        # check for duplicates with the same package name
        for package_name, package_tis in ti_by_package.items():
            # zero or one textures cannot have duplicates
            if len(package_tis) < 2:
                continue

            # keep track of duplicates. the key is is the second textures's
            # mission, and the value is the first textures's mission
            duplicates: Dict[str, str] = {}
            # try all combinations (we can shortcut some of these later)
            for a in package_tis:
                for b in package_tis:
                    # check we are working on the expected textures...
                    assert a["name"] == texture_name
                    assert b["name"] == texture_name
                    assert a["package"] == package_name
                    assert b["package"] == package_name

                    a_mission = a["mission"]
                    b_mission = b["mission"]
                    # don't compare the same mission
                    if a_mission == b_mission:
                        continue
                    # don't compare if we have already found a duplicate
                    if a_mission in duplicates or b_mission in duplicates:
                        continue

                    if maybe_same(a, b):
                        a_filename = f"{texture_name}-{a_mission}-{package_name}.png"
                        b_filename = f"{texture_name}-{b_mission}-{package_name}.png"
                        a_path = png_dir / texture_name / a_filename
                        b_path = png_dir / texture_name / b_filename

                        all_ssim = ffmpeg_ssim(a_path, b_path)
                        ssim_same = math.isclose(all_ssim, 1.0)

                        if ssim_same:
                            duplicates[b_mission] = a_mission

            for ti in package_tis:
                mission = ti["mission"]
                # there maybe a chain of duplicates
                maybe_dupe = mission
                try:
                    for _ in range(30):
                        maybe_dupe = duplicates[maybe_dupe]
                    raise RuntimeError(
                        f"Duplicate cycle for '{texture_name}-{mission}-{package_name}'"
                    )
                except KeyError:
                    pass
                # if `maybe_dupe` is different than the original mission,
                # record the de-dupe information
                if maybe_dupe != mission:
                    ti["duplicate"] = {
                        "texture": texture_name,
                        "mission": maybe_dupe,
                        "package": package_name,
                    }


def dedupe_packages(png_dir: Path, texture_atlas: Any) -> None:
    for texture_name, texture_infos in tqdm(sorted(texture_atlas.items())):
        # group texture infos by mission
        ti_by_mission = defaultdict(list)
        for ti in texture_infos:
            # ignore duplicates
            if "duplicate" in ti:
                continue
            ti_by_mission[ti["mission"]].append(ti)
        # sort them by package
        for mission_tis in ti_by_mission.values():
            mission_tis.sort(key=lambda ti: package_number(ti["package"]))
        # check for duplicates with the same mission name
        for mission_name, mission_tis in ti_by_mission.items():
            # zero or one textures cannot have duplicates
            if len(mission_tis) < 2:
                continue

            # keep track of duplicates. the key is is the second textures's
            # package, and the value is the first textures's package
            duplicates: Dict[str, str] = {}
            # try all combinations (we can shortcut some of these later)
            for a in mission_tis:
                for b in mission_tis:
                    # check we are working on the expected textures...
                    assert a["name"] == texture_name
                    assert b["name"] == texture_name
                    assert a["mission"] == mission_name
                    assert b["mission"] == mission_name

                    a_package = a["package"]
                    b_package = b["package"]
                    # don't compare the same package
                    if a_package == b_package:
                        continue
                    # don't compare if we have already found a duplicate
                    if a_package in duplicates or b_package in duplicates:
                        continue

                    if maybe_same(a, b):
                        a_filename = f"{texture_name}-{mission_name}-{a_package}.png"
                        b_filename = f"{texture_name}-{mission_name}-{b_package}.png"
                        a_path = png_dir / texture_name / a_filename
                        b_path = png_dir / texture_name / b_filename

                        all_ssim = ffmpeg_ssim(a_path, b_path)
                        ssim_same = math.isclose(all_ssim, 1.0)

                        if ssim_same:
                            duplicates[b_package] = a_package

            for ti in mission_tis:
                package = ti["package"]
                # there maybe a chain of duplicates
                maybe_dupe = package
                try:
                    for _ in range(30):
                        maybe_dupe = duplicates[maybe_dupe]
                    raise RuntimeError(
                        f"Duplicate cycle for '{texture_name}-{mission_name}-{package}'"
                    )
                except KeyError:
                    pass
                # if `maybe_dupe` is different than the original mission,
                # record the de-dupe information
                if maybe_dupe != package:
                    ti["duplicate"] = {
                        "texture": texture_name,
                        "mission": mission_name,
                        "package": maybe_dupe,
                    }


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

    dedupe_missions(args.png_dir, texture_atlas)
    dedupe_packages(args.png_dir, texture_atlas)

    dedupe_path = args.png_dir / "dedupe.json"
    with dedupe_path.open("w") as f:
        json.dump(texture_atlas, f, indent=2)


if __name__ == "__main__":
    main()
