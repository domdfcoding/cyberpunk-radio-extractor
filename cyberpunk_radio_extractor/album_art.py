#!/usr/bin/env python3
#
#  album_art.py
"""
Functions for creating album art.
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
from cp2077_extractor.cr2w.datatypes import CBitmapTexture
from cp2077_extractor.cr2w.io import parse_cr2w_buffer
from cp2077_extractor.cr2w.textures import texture_to_image
from cp2077_extractor.redarchive_reader import REDArchive
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from PIL import Image, ImageDraw, ImageOps

__all__ = [
		"AlbumArt",
		"AlbumArtHelper",
		"get_album_art",
		"get_album_art_base",
		"get_bottom_left_text",
		"get_cyberpunk_logo",
		"get_generic_album_art",
		"get_icons_atlas",
		"get_station_logos",
		"image_to_png_bytes",
		]

image_size: tuple[int, int] = 512, 512


def get_bottom_left_text(archive: REDArchive, fp: IO) -> Image.Image:
	"""
	Returns a PIL image with the text for the bottom left corner of the album art.

	:param archive: The ``basegame_1_engine.archive`` archive.
	:param fp: An open file handle for ``basegame_1_engine.archive``.
	"""

	scanner_atlas_file = "base/gameplay/gui/widgets/scanning/scanner_tooltip/atlas_scanner.xbm"
	file = archive.file_list.find_filename(scanner_atlas_file)
	crw2_file = parse_cr2w_buffer(BytesIO(archive.extract_file(fp, file)))
	assert isinstance(crw2_file.root_chunk, CBitmapTexture)
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
	"""
	Returns the PIL image to use as the basis of the album art.

	:param bottom_left_text_img:
	:param background:
	"""

	border_colour = "#913232"

	draw = ImageDraw.Draw(bottom_left_text_img)
	draw.line(
			[
					(17, 17),
					(17, image_size[1] - 17),
					(image_size[0] - 17 - 20, image_size[1] - 17),
					(image_size[0] - 17, image_size[1] - 17 - 20),
					(image_size[0] - 17, 17),
					(17, 17),
					],
			width=4,
			fill=border_colour,
			)
	draw.line([(17, 17 - 2), (17, image_size[1] - 17 + 2)], width=4, fill=border_colour)
	draw.line([(17, 15), (image_size[0] - 17 + 1, 15)], width=2, fill=border_colour)
	bottom_left_text_img_bg = Image.composite(
			Image.new("RGBA", image_size, border_colour),
			background,
			bottom_left_text_img,
			)

	return bottom_left_text_img_bg, bottom_left_text_img


class AlbumArtHelper:
	"""
	Create album art for a radio stations.

	:param logo_atlas: PIL image with the radio station images. From the file ``base/gameplay/gui/common/icons/radiostations_icons.xbm``.
	:param bottom_left_text_img: PIL image giving the text to place in the bottom left of the album art.
	:param background_colour: The background colour of the album art.
	:param graphic_colour: The colour of the station logo.
	"""

	def __init__(
			self,
			logo_atlas: Image.Image,
			bottom_left_text_img: Image.Image,
			background_colour: str = "#0e0204",
			graphic_colour: str = "#77ffff",
			):
		self.logo_atlas: Image.Image = logo_atlas
		self.background: Image.Image = Image.new("RGBA", image_size, background_colour)
		self.foreground: Image.Image = Image.new("RGBA", image_size, graphic_colour)

		album_art_base, album_art_base_mask = get_album_art_base(bottom_left_text_img, self.background)

		self.album_art_base: Image.Image = album_art_base
		self.album_art_base_mask: Image.Image = album_art_base_mask

		self.image_bounds: dict[str, tuple[int, int, int, int]] = {
				"96.1 Ritual FM": (0, 0, 346, 332),
				"99.9 Impulse": (0, 332, 345, 642),
				"89.7 Growl FM": (0, 642, 246, 971),
				"103.5 Radio PEBKAC": (0, 971, 357, logo_atlas.height),
				"107.3 Morro Rock Radio": (346, 0, 750, 196),
				"89.3 Radio Vexelstrom": (346, 196, 733, 328),
				"91.9 Royal Blue Radio": (346, 328, 713, 532),
				"98.7 Body Heat Radio": (346, 532, 702, 729),
				"101.9 The Dirge": (246, 725, 585, 912),
				"88.9 Pacific Dreams": (357, 907, 630, logo_atlas.height - 12),
				"95.2 Samizdat Radio": (750, 0, logo_atlas.width - 13, 298),
				"106.9 30 Principales": (713, 327, logo_atlas.width, 593),
				"107.5 Dark Star": (628, 809, logo_atlas.width - 25, 968),
				"92.9 Night FM": (628, 965, logo_atlas.width - 30, logo_atlas.height - 65),
				}

	def get_station_logo(self, station: str) -> Image.Image:
		"""
		Get the logo graphic for the given station.

		:param station:
		"""

		bounds = self.image_bounds[station]
		new_img = self.logo_atlas.crop(bounds)
		return self.expand_to_output_size(new_img)

	def expand_to_output_size(self, img: Image.Image) -> Image.Image:
		"""
		Expand the given image to the output image size (adding transparency evenly around all four sides).

		:param img:
		"""

		width, height = img.size

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

		new_img = ImageOps.expand(img, (add_left, add_top, add_right, add_bottom))
		return new_img

	def get_album_art(self, station: str) -> Image.Image:
		"""
		Returns the album art for the given station.

		:param station:
		"""

		station_logo = self.get_station_logo(station)
		return self.album_art_for_logo(station_logo)

	def album_art_for_logo(self, logo: Image.Image) -> Image.Image:
		"""
		Returns the album art with the given logo.

		:param station:
		"""

		album_art = Image.composite(self.foreground, self.background, logo)
		album_art = Image.composite(self.album_art_base, album_art, self.album_art_base_mask)
		return album_art


def image_to_png_bytes(image: Image.Image) -> bytes:
	"""
	Convert a PIL image to PNG, returning the raw PNG bytes.

	:param image:
	"""

	buffer = BytesIO()
	image.save(buffer, "png")
	return buffer.getvalue()


_station_names = {
		"96.1 Ritual FM",
		"99.9 Impulse",
		"89.7 Growl FM",
		"103.5 Radio PEBKAC",
		"107.3 Morro Rock Radio",
		"89.3 Radio Vexelstrom",
		"91.9 Royal Blue Radio",
		"98.7 Body Heat Radio",
		"101.9 The Dirge",
		"88.9 Pacific Dreams",
		"95.2 Samizdat Radio",
		"106.9 30 Principales",
		"107.5 Dark Star",
		"92.9 Night FM",
		}


def get_icons_atlas(archive: REDArchive, fp: IO) -> Image.Image:
	"""
	Get the radiostation icons atlas from the game files.

	:param archive: The ``basegame_1_engine.archive`` archive.
	:param fp: Open file handle to the archive.
	"""

	station_icons_file = "base/gameplay/gui/common/icons/radiostations_icons.xbm"
	file = archive.file_list.find_filename(station_icons_file)
	crw2_file = parse_cr2w_buffer(BytesIO(archive.extract_file(fp, file)))
	assert isinstance(crw2_file.root_chunk, CBitmapTexture)
	img: Image.Image = texture_to_image(crw2_file.root_chunk)
	return img


def get_cyberpunk_logo(archive: REDArchive, fp: IO, logo_filename: str = "cp77_logo_blue.xbm") -> Image.Image:
	"""
	Get the Cyberpunk logo artwork from the game files.

	:param archive: The ``basegame_4_gamedata.archive`` archive.
	:param fp: Open file handle to the archive.
	:param logo_filename: The filename (in ``base/environment/decoration/cp77_logo/textures``) of the logo. Either ``"cp77_logo_blue.xbm"`` or ``"cp77_logo_yellow.xbm"``.
	"""

	logo_file = f"base/environment/decoration/cp77_logo/textures/{logo_filename}"
	file = archive.file_list.find_filename(logo_file)
	crw2_file = parse_cr2w_buffer(BytesIO(archive.extract_file(fp, file)))
	assert isinstance(crw2_file.root_chunk, CBitmapTexture)
	img: Image.Image = texture_to_image(crw2_file.root_chunk)
	scale = (image_size[0] - 60) / img.width
	img = img.resize((round(img.width * scale), round(img.height * scale)))
	return img


class AlbumArt:
	"""
	Get album art for the game's music files.

	:param install_dir: Path to the Cyberpunk 2077 installation.
	"""

	archive_1_file: PathPlus
	archive_1: REDArchive
	archive_4_file: PathPlus
	archive_4: REDArchive

	def __init__(self, install_dir: PathLike) -> None:
		install_dir = PathPlus(install_dir)

		self.archive_1_file: PathPlus = install_dir / "archive/pc/content/basegame_1_engine.archive"
		assert self.archive_1_file.is_file()
		self.archive_1 = REDArchive.load_archive(self.archive_1_file)

		self.archive_4_file: PathPlus = install_dir / "archive/pc/content/basegame_4_gamedata.archive"
		assert self.archive_4_file.is_file()
		self.archive_4 = REDArchive.load_archive(self.archive_4_file)

	def get_album_art(self) -> dict[str, bytes]:
		"""
		Get album art for the game's radio stations.
		"""

		with open(self.archive_1_file, "rb") as fp:
			img = get_icons_atlas(self.archive_1, fp)
			bottom_left_text_img = get_bottom_left_text(self.archive_1, fp)

		album_art_data = {}
		album_art_helper = AlbumArtHelper(logo_atlas=img, bottom_left_text_img=bottom_left_text_img)

		for station in _station_names:
			album_art_data[station] = image_to_png_bytes(album_art_helper.get_album_art(station))

		return album_art_data

	def get_generic_album_art(self) -> bytes:
		"""
		Get generic album art for game's music files.
		"""

		with open(self.archive_4_file, "rb") as fp:
			logo_img = get_cyberpunk_logo(self.archive_4, fp)

		with open(self.archive_1_file, "rb") as fp:
			bottom_left_text_img = get_bottom_left_text(self.archive_1, fp)

		album_art_helper = AlbumArtHelper(logo_atlas=logo_img, bottom_left_text_img=bottom_left_text_img)
		logo_img = album_art_helper.expand_to_output_size(logo_img)
		return image_to_png_bytes(album_art_helper.album_art_for_logo(logo_img))

	def get_station_logos(self) -> dict[str, bytes]:
		"""
		Get the logos of the game's radio stations.
		"""

		with open(self.archive_1_file, "rb") as fp:
			img = get_icons_atlas(self.archive_1, fp)

		station_logos_data = {}
		album_art_helper = AlbumArtHelper(
				logo_atlas=img,
				bottom_left_text_img=Image.new("RGBA", image_size, "#00000000"),
				)

		for station in _station_names:
			station_logos_data[station] = image_to_png_bytes(album_art_helper.get_station_logo(station))

		return station_logos_data


def get_album_art(install_dir: PathLike) -> dict[str, bytes]:
	"""
	Get album art for the game's radio stations.

	:param install_dir: Path to the Cyberpunk 2077 installation.
	"""

	aa = AlbumArt(install_dir)
	return aa.get_album_art()


def get_generic_album_art(install_dir: PathLike) -> bytes:
	"""
	Get generic album art for game's music files.

	:param install_dir: Path to the Cyberpunk 2077 installation.
	"""

	aa = AlbumArt(install_dir)
	return aa.get_generic_album_art()


def get_station_logos(install_dir: PathLike) -> dict[str, bytes]:
	"""
	Get the logos of the game's radio stations.

	:param install_dir: Path to the Cyberpunk 2077 installation.
	"""

	aa = AlbumArt(install_dir)
	return aa.get_station_logos()
