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
from os import PathLike

# 3rd party
import tqdm
from cp2077_extractor.audio_data.radio_stations import Track, radio_jingle_ids, radio_stations
from cp2077_extractor.redarchive_reader import REDArchive
from domdf_python_tools.paths import PathPlus

# this package
from cyberpunk_radio_extractor.album_art import get_album_art
from cyberpunk_radio_extractor.audio import extract_track

__all__ = ["extract_radio_songs"]

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2025 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.0.0"
__email__: str = "dominic@davis-foster.co.uk"


def extract_radio_songs(
		install_dir: PathLike,
		output_dir: PathLike,
		jingles: bool = True,
		verbose: bool = False,
		) -> None:
	"""
	Extract Cyberpunk 2077 radios (and jingles) as MP3 files with album art.

	:param jingles: Also extract jingles.
	:param install_dir: Path to the Cyberpunk 2077 installation.
	:param output_dir:
	:param verbose:
	"""

	install_dir_p = PathPlus(install_dir)

	output_dir_p = PathPlus(output_dir)
	output_dir_p.maybe_make()

	archive_file = install_dir_p / "archive/pc/content" / "audio_2_soundbanks.archive"
	assert archive_file.is_file()

	album_art_data = get_album_art(install_dir_p)
	archive = REDArchive.load_archive(archive_file)
	total_tracks = sum(len(sd) for sd in radio_stations.values())

	with open(archive_file, "rb") as fp, tqdm.tqdm(total=total_tracks) as progbar:
		for station, station_data in radio_stations.items():
			if verbose:
				progbar.write(f"===== {station} =====")

			station_dir = output_dir_p / station
			station_dir.maybe_make()

			for track in station_data:
				mp3_filename = station_dir / (track.filename_stub + ".mp3")
				if verbose:
					progbar.write(f"    {track.filename_stub} -> {mp3_filename}")
				extract_track(track, station, mp3_filename, archive, fp, album_art_data.get(station))
				progbar.update()

			if jingles and station in radio_jingle_ids:
				for wem_name in radio_jingle_ids[station]:
					mp3_filename = station_dir / f"jingle_{wem_name}.mp3"
					track = Track(station, "Jingle", wem_name)
					extract_track(track, station, mp3_filename, archive, fp, album_art_data.get(station))
