# Recoil Textures

Pipeline to process textures from Recoil and find the "best" textures.

## Development

Needs:

* Python 3.10 (maybe 3.8 or 3.9 will work)
* FFmpeg (https://ffmpeg.org/)

Create a python virtual environment and install `requirements.txt`.

Steps:

1. Convert ZBD texture packages to ZIP
1. Extract PNG textures from ZIP, combine manifests into texture atlas grouped by texture name
1. Count PNG texture colors, adding them into the texture atlas
1. Dedupe PNG textures per package (this will take a looong time!)
1. TODO: Score PNG textures

```
mkdir "png"
python3 convert_zbd.py "zbd/" "./unzbd"
python3 extract_zip.py "zbd/" "png/"
python3 count_colors.py "png/"
# warning: very slow!
python3 dedupe.py "png/"
# optional
python3 copy_dedupe.py "png/" "dedupe/"
python3 score.py "png/"
```

## License

Licensed under the European Union Public Licence (EUPL) 1.2 ([LICENSE](LICENSE) or https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12).
