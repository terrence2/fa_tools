#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the GNU General Public
# License, version 3. If a copy of the GPL was not distributed with this file,
# You can obtain one at https://www.gnu.org/licenses/gpl.txt.
import argparse
import os.path
import subprocess


def uncook_program(script_file: str) -> callable:
    def uncook_generic(input_filename, output_prefix):
        subprocess.check_call([script_file, '-i', input_filename, '-o', output_prefix])
    return uncook_generic


Uncookers = {
}


def select_uncooker(filename: str) -> callable:
    _, ext = os.path.splitext(filename)
    ext = ext.lstrip('.')

    if ext in Uncookers:
        return Uncookers[ext]

    helper = os.path.realpath(os.path.join('scripts', 'uncook_{}.py'.format(ext)))
    if os.path.exists(helper):
        return uncook_program(helper)

    print("No uncook program for {}".format(filename))


def main():
    parser = argparse.ArgumentParser(description='Find and uncook files.')
    parser.add_argument('--input-prefix', '-i', type=str, help='Where to find the cooked files.')
    parser.add_argument('--output-prefix', '-o', type=str, help='Where to store our uncooked output.')
    args = parser.parse_args()

    if not args.input_prefix or not args.output_prefix:
        return parser.print_help()

    output_prefix = os.path.realpath(args.output_prefix)
    if not os.path.isdir(output_prefix):
        print("The output prefix must exist and be a directory.")
        return

    for filename in os.listdir(os.path.realpath(args.input_prefix)):
        input_filename = os.path.realpath(os.path.join(args.input_prefix, filename))
        processor = select_uncooker(filename)
        if processor:
            processor(input_filename, output_prefix)


if __name__ == '__main__':
    main()
