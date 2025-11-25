# stdlib
from io import BytesIO
from typing import IO

# 3rd party
import dom_toml
from cp2077_extractor.audio_data.radio_stations import Track, radio_jingle_ids, radio_stations
from cp2077_extractor.cr2w.io import parse_cr2w_buffer
from cp2077_extractor.cr2w.textures import texture_to_image
from cp2077_extractor.redarchive_reader import REDArchive
from cp2077_extractor.utils import transcode_file
from domdf_python_tools.paths import PathPlus, TemporaryPathPlus
from PIL import Image, ImageDraw, ImageOps


def get_album_art(install_dir: PathPlus) -> dict[str, bytes]:
	archive_file = install_dir / "archive/pc/content" / "basegame_1_engine.archive"
	assert archive_file.is_file()

	archive = REDArchive.load_archive(archive_file)

	station_icons_file = "base/gameplay/gui/common/icons/radiostations_icons.xbm"
	with open(archive_file, "rb") as fp:
		file = archive.file_list.find_filename(station_icons_file)
		crw2_file = parse_cr2w_buffer(BytesIO(archive.extract_file(fp, file)))
		img: Image.Image = texture_to_image(crw2_file.root_chunk)

	image_size = 512, 512

	image_bounds = {
			"96.1 Ritual FM": (0, 0, 346, 332),  # "99.9 Impulse": (0, 332, 345, 642),
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

		background = Image.new("RGBA", image_size, "#0e0204")
		foreground = Image.new("RGBA", image_size, "#77ffff")
		new_img = ImageOps.expand(new_img, (add_left, add_top, add_right, add_bottom))
		album_art = Image.composite(foreground, background, new_img)

		border_colour = "#913232"

		draw = ImageDraw.Draw(album_art)
		draw.line([(17, 17), (17, album_art.height - 17), (album_art.width - 17 - 20, album_art.height - 17),
					(album_art.width - 17, album_art.height - 17 - 20), (album_art.width - 17, 17), (17, 17)],
					width=4,
					fill=border_colour)
		draw.line([(17, 17 - 2), (17, album_art.height - 17 + 2)], width=4, fill=border_colour)
		draw.line([(17, 15), (album_art.width - 17 + 1, 15)], width=2, fill=border_colour)

		buffer = BytesIO()
		album_art.save(buffer, "png")
		album_art_data[station] = buffer.getvalue()

	return album_art_data


def main():
	config = dom_toml.load("config.toml")

	install_dir = PathPlus(config["config"]["install_dir"])

	archive_file = install_dir / "archive/pc/content" / "audio_2_soundbanks.archive"
	assert archive_file.is_file()

	output_dir = PathPlus("radio")
	output_dir.maybe_make()

	album_art_data = get_album_art(install_dir)

	archive = REDArchive.load_archive(archive_file)

	with open(archive_file, "rb") as fp:
		for station, station_data in radio_stations.items():
			station_dir = output_dir / station
			station_dir.maybe_make()

			for track in station_data:
				mp3_filename = station_dir / (track.filename_stub + ".mp3")
				extract_track(track, station, mp3_filename, archive, fp, album_art_data)

			if station in radio_jingle_ids:
				for wem_name in radio_jingle_ids[station]:
					mp3_filename = station_dir / f"jingle_{wem_name}.mp3"
					track = Track(station, "Jingle", wem_name)
					extract_track(track, station, mp3_filename, archive, fp, album_art_data)


def extract_track(
		track: Track,
		station: str,
		mp3_filename: PathPlus,
		archive: REDArchive,
		fp: IO,
		album_art_data: dict[str, bytes],
		):
	if not mp3_filename.is_file():
		with TemporaryPathPlus() as tmpdir:
			wem_filename = tmpdir.joinpath(mp3_filename.with_suffix(".wem").name)
			file = archive.file_list.find_filename(fr"base\sound\soundbanks\media\{track.wem_name}.wem")
			contents = archive.extract_file(fp, file)
			wem_filename.write_bytes(contents)
			transcode_file(wem_filename, mp3_filename)

	track.set_id3_metadata(mp3_filename, station, album_art=album_art_data.get(station))


if __name__ == "__main__":
	main()
