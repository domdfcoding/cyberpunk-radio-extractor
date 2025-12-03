#!/usr/bin/env python3
#
#  __main__.py
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

# 3rd party
import click
from consolekit.options import version_option
from consolekit.versions import get_version_callback

# this package
from cyberpunk_radio_extractor import __version__, extract_track, get_album_art

__all__ = ["main"]


@version_option(
		get_version_callback(__version__, "cyberpunk-song-extractor", dependencies=("click", "cp2077-extractor"))
		)
@click.option("-i", "--install-dir", default=None)
@click.option("-j/-J", "--jingles/--no-jingles", is_flag=True, default=True)
@click.command()
def main(jingles: bool = True, install_dir: str | None = None) -> None:
	# 3rd party
	from cp2077_extractor.audio_data.radio_stations import Track, radio_jingle_ids, radio_stations
	from cp2077_extractor.redarchive_reader import REDArchive
	from domdf_python_tools.paths import PathPlus

	if not install_dir:
		# 3rd party
		import dom_toml
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

			if jingles and station in radio_jingle_ids:
				for wem_name in radio_jingle_ids[station]:
					mp3_filename = station_dir / f"jingle_{wem_name}.mp3"
					track = Track(station, "Jingle", wem_name)
					extract_track(track, station, mp3_filename, archive, fp, album_art_data)


if __name__ == "__main__":
	main()
