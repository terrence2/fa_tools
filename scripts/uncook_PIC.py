#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the GNU General Public
# License, version 3. If a copy of the GPL was not distributed with this file,
# You can obtain one at https://www.gnu.org/licenses/gpl.txt.
import argparse
import os.path
import struct

from PIL import Image


def discover(fn):
    with open(fn, 'rb') as fp:
        data = fp.read()

    header = data[0:0x40]
    body = data[0x40:]

    (fmt, width, height, always64, pixels_size,
     palette_offset, palette_size,
     unk0, unk1,
     rowheads_offset, rowheads_size) = (
        struct.unpack_from('<HIIIIIIIIIH', header))


    """
    00000000  00 00           ; fmt
              80 02 00 00     ; width
              e0 01 00 00     ; height
              40 00 00 00     ; 64
              00 b0
    00000010  04 00           ; pixels_size
              c0 b7 04 00     ; palette_offset
              00 03 00 00     ; palette_size
              00 00 00 00     ; unk0
              ca 12
    00000020  00 00           ; unk1
              40 b0 04 00     ; rowheads_offset
              80 07 00 00     ; rowheads_size
              00 00 00 00 00 00
    00000030  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
    """

    print("{:13s} sz: 0x{:x}".format(os.path.basename(fn), len(data)))
    print("fmt:{}, {: >4} x{: >4}, npix: 0x{:x}, nbytes: 0x{:x}".format(fmt, width, height, width * height, pixels_size))
    print("palette @: 0x{:x}, sz: 0x{:x}".format(palette_offset, palette_size))
    print("Unk: 0: 0x{:x}, 1: 0x{:x}".format(unk0, unk1))
    print("rowheads @: 0x{:x}, sz: 0x{:x}".format(rowheads_offset, rowheads_size))

    b2A, b2B,   b2C, b2D, b2E, b2F = struct.unpack_from('<6B', header, 0x20)
    b30, b31, b32, b33,   b34, b35, b36, b37,   b38, b39, b3A, b3B,   b3C, b3D, b3E, b3F = struct.unpack_from('<16B', header, 0x30)
    print("                                  {:02x} {:02x}   {:02x} {:02x} {:02x} {:02x}".format(b2A, b2B,   b2C, b2D, b2E, b2F))
    print("{:02x} {:02x} {:02x} {:02x}   {:02x} {:02x} {:02x} {:02x}   {:02x} {:02x} {:02x} {:02x}   {:02x} {:02x} {:02x} {:02x}".format(b30, b31, b32, b33,   b34, b35, b36, b37,   b38, b39, b3A, b3B,   b3C, b3D, b3E, b3F))

    assert always64 == 64
    pixel_data = body[0:pixels_size]

    #print("{} - pixels in {}:{} with {} colors".format(fn, min(pixel_data), max(pixel_data), len(palette_data) // 3))
    rowheads_data = data[rowheads_offset:rowheads_offset + rowheads_size]

    palette = b''
    if palette_offset and palette_size:
        palette = data[palette_offset:]

    print("header: 0x40")
    print("pixeldata: 0x{:x}".format(len(pixel_data)))
    print("rowheaddata: 0x{:x}".format(len(rowheads_data)))
    print("palette: 0x{:x}".format(len(palette)))
    extracted_size = 0x40 + len(pixel_data) + len(rowheads_data) + len(palette)
    print("sum: 0x{:x}".format(extracted_size))
    print("full file: 0x{:x}".format(len(data)))
    #assert extracted_size == len(data)
    print("min pixel: 0x{:x}".format(min(pixel_data)))
    print("max pixel: 0x{:x}".format(max(pixel_data)))
    if rowheads_data:
        print("rowhead count: 0x{:x}".format(len(rowheads_data) // 4))
    if palette:
        print("min color: 0x{:x}".format(min(palette)))
        print("max color: 0x{:x}".format(max(palette)))
        print("color count: 0x{:x}".format(len(palette) // 3))
    print("excess: 0x{:x}".format(len(data) - (len(pixel_data) + len(header))))
    print("====================")


def find_palette(filename: str) -> str:
    own_dir = os.path.dirname(filename)
    if os.path.isfile(os.path.join(own_dir, 'PALETTE.PAL')):
        return os.path.join(own_dir, 'PALETTE.PAL')

    own_dir_name = os.path.basename(own_dir)
    parent_dir = os.path.dirname(own_dir)
    sibling_dirs = []
    for name in os.listdir(parent_dir):
        if name == own_dir_name:
            continue
        sibling_dirs.append(os.path.join(parent_dir, name))

    for sibling_dir in sibling_dirs:
        if os.path.isfile(os.path.join(sibling_dir, 'PALETTE.PAL')):
            return os.path.join(sibling_dir, 'PALETTE.PAL')

    raise FileNotFoundError('PALETTE.PAL')


def contruct_palette(raw_palette_data: bytes) -> [bytes(3)]:
    #assert len(raw_palette_data) == 0x300
    palette = []
    for i in range(0, len(raw_palette_data), 3):
        r, g, b = raw_palette_data[i:i + 3]
        r *= 3
        g *= 3
        b *= 3
        assert r <= 0xff
        assert g <= 0xff
        assert b <= 0xff
        palette.append(bytes([r, g, b]))
    return palette


def build_color_image(indexes: bytes, palette: [bytes(3)]):
    pixels = []
    for index in indexes:
        if index < len(palette):
            pixels.append(palette[index])
        else:
            pixels.append(palette[0])
    return b''.join(pixels)


def save_image(filename: str, color_pixels: bytes, width: int, height: int):
    img = Image.frombytes('RGB', (width, height), color_pixels)
    with open(filename, 'wb') as fp:
        img.save(fp, 'png')


def decode_fmt0_internal_palette(fn, output_filename, data, width, height, pixels_size, palette_offset, palette_size):
    pixel_data = data[0x40:0x40 + pixels_size]
    palette_data = data[palette_offset:palette_offset + palette_size]

    palette = contruct_palette(palette_data)
    color_pixels = build_color_image(pixel_data, palette)
    save_image(output_filename, color_pixels, width, height)


def decode_fmt0_external_palette(fn, output_filename, data, width, height, pixels_size):
    pixel_data = data[0x40:0x40 + pixels_size]

    with open(find_palette(fn), 'rb') as fp:
        palette_data = fp.read()

    palette = contruct_palette(palette_data)
    color_pixels = build_color_image(pixel_data, palette)
    save_image(output_filename, color_pixels, width, height)


def decode_fmt0(fn, output_filename, data):
    header = data[0:0x40]

    (fmt, width, height, pixels_offset, pixels_size,
     palette_offset, palette_size,
     unk0, unk1,
     rowheads_offset, rowheads_size) = (
        struct.unpack_from('<HIIIIIIIIIH', header))

    if palette_offset != 0:
        assert palette_size > 0
        decode_fmt0_internal_palette(fn, output_filename, data, width, height, pixels_size, palette_offset, palette_size)
    else:
        decode_fmt0_external_palette(fn, output_filename, data, width, height, pixels_size)


def get_output_filename(input_filename, output_prefix):
    base = os.path.basename(input_filename)
    base_no_ext, _ = os.path.splitext(base)
    return os.path.join(output_prefix, base_no_ext + '.png')


def main():
    parser = argparse.ArgumentParser(description='11K -> WAV')
    parser.add_argument('--input', '-i', type=str, help='What to uncook.')
    parser.add_argument('--output-prefix', '-o', type=str, help='Where to store the output.')
    parser.add_argument('--discover', action='store_true', help='Print the image header.')
    args = parser.parse_args()

    if args.discover:
        return discover(args.input)

    if not args.input or not args.output_prefix:
        return parser.print_help()

    output_filename = get_output_filename(args.input, args.output_prefix)

    with open(args.input, 'rb') as fp:
        data = fp.read()

    if data[0] == 0:
        decode_fmt0(args.input, output_filename, data)
    else:
        print("unknown format: {} in {}".format(data[0], args.input))


if __name__ == '__main__':
    main()


