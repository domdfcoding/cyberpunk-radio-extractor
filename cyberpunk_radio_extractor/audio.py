#!/usr/bin/env python3
#
#  audio.py
"""
Audio extraction functions.
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
from typing import IO

# 3rd party
from cp2077_extractor.audio_data.radio_stations import Track
from cp2077_extractor.redarchive_reader import REDArchive
from cp2077_extractor.utils import transcode_file
from domdf_python_tools.paths import PathPlus, TemporaryPathPlus

__all__ = ["extract_track"]


def extract_track(
		track: Track,
		station: str,
		mp3_filename: PathPlus,
		archive: REDArchive,
		fp: IO,
		album_art: bytes | None,
		) -> None:
	"""
	Extract the given track and convert to MP3.

	:param track:
	:param station: The radio station to include the track with.
	:param mp3_filename: The output filename.
	:param archive: The ``audio_2_soundbanks.archive`` archive.
	:param fp: An open file handle to the ``audio_2_soundbanks.archive`` archive.
	:param album_art: Optional album art.
	"""
	if not mp3_filename.is_file():
		with TemporaryPathPlus() as tmpdir:
			wem_filename = tmpdir.joinpath(mp3_filename.with_suffix(".wem").name)
			file = archive.file_list.find_filename(fr"base\sound\soundbanks\media\{track.wem_name}.wem")
			contents = archive.extract_file(fp, file)
			wem_filename.write_bytes(contents)
			transcode_file(wem_filename, mp3_filename)

	track.set_id3_metadata(mp3_filename, station, album_art=album_art)
