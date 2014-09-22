#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the GNU General Public
# License, version 3. If a copy of the GPL was not distributed with this file,
# You can obtain one at https://www.gnu.org/licenses/gpl.txt.
import argparse
import os.path
import struct


def uncook_11k(input_filename: str, output_filename: str):
    with open(input_filename, 'rb') as fp:
        raw_data = fp.read()

    parts = [
        # RIFF Descriptor.
        ('4s', b'RIFF'),
        ('i', 36 + len(raw_data)),
        ('4s', b'WAVE'),
        # fmt chunk
        ('4s', b'fmt '),
        ('i', 16),     # size of remainder of chunk
        ('h', 1),      # AudioFormat
        ('h', 1),      # NumChannels
        ('i', 11025),  # SampleRate
        ('i', 11025),  # ByteRate
        ('h', 1),      # BlockAlign (bytes per sample)
        ('h', 8),      # BitsPerSample
        # Data chunk.
        ('4s', b'data'),
        ('i', len(raw_data))
    ]
    fmt = '<' + ''.join([fst for fst, _ in parts])
    args = [snd for _, snd in parts]
    with open(output_filename, 'wb') as fp:
        fp.write(struct.pack(fmt, *args))
        fp.write(raw_data)


def get_output_filename(input_filename, output_prefix):
    base = os.path.basename(input_filename)
    base_no_ext, _ = os.path.splitext(base)
    return os.path.join(output_prefix, base_no_ext + '.wav')


def main():
    parser = argparse.ArgumentParser(description='11K -> WAV')
    parser.add_argument('--input', '-i', type=str, help='What to uncook.')
    parser.add_argument('--output-prefix', '-o', type=str, help='Where to store the output.')
    args = parser.parse_args()

    if not args.input or not args.output_prefix:
        return parser.print_help()

    uncook_11k(os.path.realpath(args.input), os.path.realpath(get_output_filename(args.input, args.output_prefix)))


if __name__ == '__main__':
    main()
