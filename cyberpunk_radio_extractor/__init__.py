#!/usr/bin/env python3
#
#  __init__.py
"""
Extract Cyberpunk 2077 radios (and jingles) as MP3 files with album art.
"""
#
#  Copyright © 2025 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
from io import BytesIO
from typing import IO

# 3rd party
from cp2077_extractor.audio_data.radio_stations import Track
from cp2077_extractor.cr2w.io import parse_cr2w_buffer
from cp2077_extractor.cr2w.textures import texture_to_image
from cp2077_extractor.redarchive_reader import REDArchive
from cp2077_extractor.utils import transcode_file
from domdf_python_tools.paths import PathPlus, TemporaryPathPlus
from PIL import Image, ImageDraw, ImageOps

__all__ = ["extract_track", "get_album_art", "get_album_art_base", "get_bottom_left_text"]

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2025 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.0.0"
__email__: str = "dominic@davis-foster.co.uk"

image_size: tuple[int, int] = 512, 512


def get_bottom_left_text(archive: REDArchive, fp: IO) -> Image.Image:
	scanner_atlas_file = "base/gameplay/gui/widgets/scanning/scanner_tooltip/atlas_scanner.xbm"
	file = archive.file_list.find_filename(scanner_atlas_file)
	crw2_file = parse_cr2w_buffer(BytesIO(archive.extract_file(fp, file)))
	img: Image.Image = texture_to_image(crw2_file.root_chunk)
	img = img.crop((745, 305, img.width, 364))
	offset_l, offset_b = 20, 23
	add_top = image_size[1] - offset_b - img.height
	add_right = image_size[0] - offset_l - img.width
	img = ImageOps.expand(img, (offset_l, add_top, add_right, offset_b))

	return img


def get_album_art_base(
		bottom_left_text_img: Image.Image,
		background: Image.Image,
		) -> tuple[Image.Image, Image.Image]:

	border_colour = "#913232"

	draw = ImageDraw.Draw(bottom_left_text_img)
	draw.line([(17, 17), (17, image_size[1] - 17), (image_size[0] - 17 - 20, image_size[1] - 17),
				(image_size[0] - 17, image_size[1] - 17 - 20), (image_size[0] - 17, 17), (17, 17)],
				width=4,
				fill=border_colour)
	draw.line([(17, 17 - 2), (17, image_size[1] - 17 + 2)], width=4, fill=border_colour)
	draw.line([(17, 15), (image_size[0] - 17 + 1, 15)], width=2, fill=border_colour)
	bottom_left_text_img_bg = Image.composite(
			Image.new("RGBA", image_size, border_colour), background, bottom_left_text_img
			)

	return bottom_left_text_img_bg, bottom_left_text_img


def get_album_art(install_dir: PathPlus) -> dict[str, bytes]:
	archive_file = install_dir / "archive/pc/content" / "basegame_1_engine.archive"
	assert archive_file.is_file()

	archive = REDArchive.load_archive(archive_file)

	station_icons_file = "base/gameplay/gui/common/icons/radiostations_icons.xbm"
	with open(archive_file, "rb") as fp:
		file = archive.file_list.find_filename(station_icons_file)
		crw2_file = parse_cr2w_buffer(BytesIO(archive.extract_file(fp, file)))
		img: Image.Image = texture_to_image(crw2_file.root_chunk)
		bottom_left_text_img = get_bottom_left_text(archive, fp)

	image_bounds = {
			"96.1 Ritual FM": (0, 0, 346, 332),  #
			# TODO: "99.9 Impulse": (0, 332, 345, 642),
			"89.7 Growl FM": (0, 642, 246, 971),
			"103.5 Radio PEBKAC": (0, 971, 357, img.height),
			"107.3 Morro Rock Radio": (346, 0, 750, 196),
			"89.3 Radio Vexelstrom": (346, 196, 733, 328),
			"91.9 Royal Blue Radio": (346, 328, 713, 532),
			"98.7 Body Heat Radio": (346, 532, 702, 729),
			"101.9 The Dirge": (246, 725, 585, 912),
			"88.9 Pacific Dreams": (357, 907, 630, img.height - 12),
			"95.2 Samizdat Radio": (750, 0, img.width - 13, 298),
			"106.9 30 Principales": (713, 327, img.width, 593),
			"107.5 Dark Star": (628, 809, img.width - 25, 968),
			"92.9 Night FM": (628, 965, img.width - 30, img.height - 65),
			}

	album_art_data = {}

	background = Image.new("RGBA", image_size, "#0e0204")
	foreground = Image.new("RGBA", image_size, "#77ffff")

	album_art_base, album_art_base_mask = get_album_art_base(bottom_left_text_img, background)

	for station, bounds in image_bounds.items():
		new_img = img.crop(bounds)
		width, height = new_img.size

		add_width = image_size[0] - width

		add_left = add_right = add_width // 2
		if add_width % 2:
			# Odd
			add_left += 1

		add_height = image_size[1] - height

		add_top = add_bottom = add_height // 2
		if add_height % 2:
			# Odd
			add_top += 1

		new_img = ImageOps.expand(new_img, (add_left, add_top, add_right, add_bottom))
		album_art = Image.composite(foreground, background, new_img)

		album_art = Image.composite(album_art_base, album_art, album_art_base_mask)

		buffer = BytesIO()
		album_art.save(buffer, "png")
		album_art_data[station] = buffer.getvalue()

	return album_art_data


def extract_track(
		track: Track,
		station: str,
		mp3_filename: PathPlus,
		archive: REDArchive,
		fp: IO,
		album_art_data: dict[str, bytes],
		) -> None:
	if not mp3_filename.is_file():
		with TemporaryPathPlus() as tmpdir:
			wem_filename = tmpdir.joinpath(mp3_filename.with_suffix(".wem").name)
			file = archive.file_list.find_filename(fr"base\sound\soundbanks\media\{track.wem_name}.wem")
			contents = archive.extract_file(fp, file)
			wem_filename.write_bytes(contents)
			transcode_file(wem_filename, mp3_filename)

	track.set_id3_metadata(mp3_filename, station, album_art=album_art_data.get(station))
