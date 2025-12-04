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
from consolekit.options import flag_option, version_option
from consolekit.versions import get_version_callback

# this package
from cyberpunk_radio_extractor import __version__, extract_radio_songs

__all__ = ["main"]


@version_option(
		get_version_callback(__version__, "cyberpunk-song-extractor", dependencies=("click", "cp2077-extractor"))
		)
@click.option("-o", "--output-dir", default="radio", help="Path to write files to.")
@click.option("-i", "--install-dir", default=None, help="Path to the Cyberpunk 2077 installation.")
@flag_option("-j/-J", "--jingles/--no-jingles", default=True, help="Extract jingles for the radio stations.")
@flag_option("-v", "--verbose", help="Show individual tracks being processed.")
@click.command()
def main(
		jingles: bool = True,
		install_dir: str | None = None,
		output_dir: str = "radio",
		verbose: bool = False
		) -> None:
	"""
	Extract Cyberpunk 2077 radios (and jingles) as MP3 files with album art.
	"""

	# this package
	from cyberpunk_radio_extractor.album_art import get_album_art

	if not install_dir:
		# 3rd party
		import dom_toml
		config = dom_toml.load("config.toml")
		install_dir = config["config"]["install_dir"]

	album_art_data = get_album_art(install_dir)

	extract_radio_songs(install_dir, output_dir, album_art_data=album_art_data, jingles=jingles, verbose=verbose)


if __name__ == "__main__":
	main()
