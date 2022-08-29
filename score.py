import json
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from typing import Any

# "best" to "worst"
MISSION_NAMES = [
    "m1",
    "m2",
    "m3",
    "m4",
    "m5",
    "m6",
    "m7",
    "m8",
    "m9",
    "m10",
    "m11",
    "m12",
    "m13",
]
# score the mission names so that max("m1", "m2") == "m1" etc.
MISSION_SCORE_MAX = {m: i for (i, m) in enumerate(reversed(MISSION_NAMES))}
assert max("m1", "m2", key=lambda m: MISSION_SCORE_MAX[m]) == "m1"

# "best" to "worst"
PACKAGE_NAMES = [
    "rtexture4",
    "rtexture2",
    "texture8",
    "texture6",
    "texture4",
    "texture2",
]
RGB_PACKAGE_NAMES = {"rtexture4", "rtexture2"}
PAL_PACKAGE_NAMES = {"texture8", "texture6", "texture4", "texture2"}

PACKAGE_SCORE_MAX = {p: i for (i, p) in enumerate(reversed(PACKAGE_NAMES))}
assert max("rtexture4", "rtexture2", key=lambda p: PACKAGE_SCORE_MAX[p]) == "rtexture4"
assert max("texture4", "texture2", key=lambda p: PACKAGE_SCORE_MAX[p]) == "texture4"
assert max("rtexture2", "texture6", key=lambda p: PACKAGE_SCORE_MAX[p]) == "rtexture2"

# "best" to "worst"
STRETCH_NAMES = [
    "None",
    "Horizontal",
    "Vertical",
    "Both",
]
STRETCH_SCORE_MAX = {s: i for (i, s) in enumerate(reversed(STRETCH_NAMES))}
assert max("None", "Horizontal", key=lambda s: STRETCH_SCORE_MAX[s]) == "None"
assert max("None", "Both", key=lambda s: STRETCH_SCORE_MAX[s]) == "None"

# "best" to "worst"
ALPHA_NAMES = [
    "Full",
    "Simple",
    "None",
]
ALPHA_SCORE_MAX = {a: i for (i, a) in enumerate(reversed(ALPHA_NAMES))}
assert max("Full", "Simple", key=lambda a: ALPHA_SCORE_MAX[a]) == "Full"
assert max("Full", "None", key=lambda a: ALPHA_SCORE_MAX[a]) == "Full"


def score_texture(ti: Any) -> Any:
    w = ti["width"]
    h = ti["height"]
    size = w * h
    colors = ti["colors"]
    alpha = ALPHA_SCORE_MAX[ti["alpha"]]
    stretch = STRETCH_SCORE_MAX[ti["stretch"]]
    mission = MISSION_SCORE_MAX[ti["mission"]]
    package = PACKAGE_SCORE_MAX[ti["package"]]
    return (size, colors, alpha, stretch, package, mission)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "png_dir",
        type=lambda value: Path(value).resolve(strict=True),
    )
    args = parser.parse_args()

    atlas_path = args.png_dir / "dedupe.json"
    with atlas_path.open("r") as f:
        texture_atlas = json.load(f)

    for texture_name, texture_infos in sorted(texture_atlas.items()):
        # group texture infos by mission
        ti_by_mission = defaultdict(list)
        for ti in texture_infos:
            # ignore duplicates
            if "duplicate" in ti:
                continue
            ti_by_mission[ti["mission"]].append(ti)

        for mission_name, mission_tis in ti_by_mission.items():
            mission_tis_rgb = [
                ti for ti in mission_tis if ti["package"] in RGB_PACKAGE_NAMES
            ]
            mission_tis_pal = [
                ti for ti in mission_tis if ti["package"] in PAL_PACKAGE_NAMES
            ]

            if mission_tis_rgb and mission_tis_pal:
                best_rgb_ti = max(mission_tis_rgb, key=score_texture)
                best_pal_ti = max(mission_tis_pal, key=score_texture)
                best_all_ti = max(mission_tis, key=score_texture)

                if best_rgb_ti == best_all_ti:
                    # rgb wins, probably by size or colors?
                    assert best_pal_ti["alpha"] == best_rgb_ti["alpha"], (
                        best_pal_ti,
                        best_rgb_ti,
                    )
                    rgb_color_better = best_rgb_ti["colors"] >= best_pal_ti["colors"]
                    if not rgb_color_better:
                        print("rgb color worse", texture_name, mission_name)
                    pass
                elif best_pal_ti == best_all_ti:
                    # pal wins, probably by size or colors?
                    assert best_pal_ti["alpha"] == best_rgb_ti["alpha"], (
                        best_pal_ti,
                        best_rgb_ti,
                    )
                    pal_color_better = best_pal_ti["colors"] >= best_rgb_ti["colors"]
                    if not pal_color_better:
                        print("pal color worse", texture_name, mission_name)
                    pass
                else:
                    raise RuntimeError(
                        f"best is neither pal nor rgb? {texture_name} {mission_name}"
                    )
            elif mission_tis_rgb:
                assert mission_tis_rgb == mission_tis, (mission_tis_rgb, mission_tis)
                # no pal textures, so only need to look at rgb
                best_all_ti = max(mission_tis, key=score_texture)
            elif mission_tis_pal:
                assert mission_tis_pal == mission_tis, (mission_tis_pal, mission_tis)
                # no rgb textures, so only need to look at pal
                best_all_ti = max(mission_tis, key=score_texture)
            else:
                raise RuntimeError(f"no textures? {texture_name} {mission_name}")


if __name__ == "__main__":
    main()
