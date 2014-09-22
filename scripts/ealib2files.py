#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the GNU General Public
# License, version 3. If a copy of the GPL was not distributed with this file,
# You can obtain one at https://www.gnu.org/licenses/gpl.txt.
import argparse
import os.path
import mmap
import struct
import subprocess
import tempfile


class FileEntry:
    def __init__(self, filename: str, start_offset: int, flags: int):
        self.filename = filename
        self.start_offset = start_offset
        self.flags = flags
        self.length = None


def extract_lib(library_file: str, output_prefix: str):
    print("Extracting {} -> {}".format(library_file, output_prefix))
    header_format = '<5sH'
    entry_format = '<13sBI'
    header_size = struct.calcsize(header_format)
    entry_size = struct.calcsize(entry_format)

    with open(library_file, 'r+b') as fp_input:
        raw_map = mmap.mmap(fp_input.fileno(), 0)

        # Check header bits.
        magic, count = struct.unpack_from(header_format, raw_map)
        if magic != b'EALIB':
            raise Exception("Not an EALIB file.")

        # Read directory.
        entries = []
        offset = header_size
        for i in range(count):
            name, flags, start_offset = struct.unpack_from(entry_format, raw_map, offset)
            offset += entry_size
            name = name.decode('ASCII').strip('\0')
            entries.append(FileEntry(name, start_offset, flags))
        assert entries[0].start_offset > header_size + count * entry_size

        # Infer file blob lengths.
        for entry, next_entry in zip(entries[:-1], entries[1:]):
            entry.length = next_entry.start_offset - entry.start_offset
        entries[-1].length = len(raw_map) - entries[-1].start_offset

        for entry in entries:
            output_filename = os.path.join(output_prefix, entry.filename)
            assert not os.path.exists(output_filename)
            raw_map.seek(entry.start_offset)
            raw_data = raw_map.read(entry.length)

            print("{: >13s} sz: {: >5d} flags: {: >2d} @ {: >9d}".format(entry.filename, entry.length, entry.flags,
                                                                         entry.start_offset))

            assert entry.flags in (0, 4)
            if entry.flags == 0:
                with open(os.path.join(output_prefix, entry.filename), 'wb') as fp:
                    fp.write(raw_data)
            else:
                assert entry.flags == 4
                expected_size = struct.unpack('<I', raw_data[0:4])[0]

                blast = os.path.realpath(os.path.join(os.getcwd(), 'vendor', 'blast'))
                if not os.path.exists(blast):
                    raise Exception("Please ensure blast exists in ./vendor")

                with open(os.path.join(output_prefix, entry.filename), 'wb') as output_file:
                    # Note: BytesIO does not work because it does not have a dup'able fileno().
                    input_file = tempfile.TemporaryFile(mode='w+b')
                    input_file.write(raw_data[4:])
                    input_file.seek(0)

                    subprocess.check_call([blast], stdin=input_file, stdout=output_file)
                    output_file.seek(0, os.SEEK_END)
                    assert output_file.tell() == expected_size


def extract_libs(library_files: [str], output_prefix: str):
    assert os.path.isdir(output_prefix)
    output_prefix = os.path.realpath(output_prefix)
    assert os.path.isdir(output_prefix)

    for file_name in library_files:
        library_file = os.path.realpath(file_name)
        assert os.path.isfile(library_file)
        output_dir = os.path.join(output_prefix, os.path.basename(library_file))
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        extract_lib(library_file, output_dir)


def main():
    parser = argparse.ArgumentParser(description='EALIB -> Files')
    parser.add_argument('--output-prefix', '-o', type=str, metavar="DIR", help='Where to store our data.')
    parser.add_argument('lib_files', nargs='+', help="Input files to unpack.")
    args = parser.parse_args()

    if args.output_prefix is None:
        parser.print_help()
        print("\nNo output directory specified.")
        return

    print(args.output_prefix)
    extract_libs(args.lib_files, args.output_prefix)


if __name__ == '__main__':
    main()
