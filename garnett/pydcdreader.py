# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import struct


class _DCDFileHeader(object):
    pass


class _DCDFrameHeader(object):
    pass


def _read_int(stream):
    return struct.unpack('<L', stream.read(4))[0]


def _read_double(stream):
    return struct.unpack('<d', stream.read(8))[0]


def _read_float(stream):
    return struct.unpack('<f', stream.read(4))[0]


def _read_file_header(stream):
    file_header = _DCDFileHeader()
    assert _read_int(stream) == 84
    assert stream.read(4) == b'CORD'
    file_header.num_frames = _read_int(stream)
    file_header.m_start_timestep = _read_int(stream)
    file_header.m_period = _read_int(stream)
    file_header.timesteps = _read_int(stream)
    for i in range(5):
        _read_int(stream)
    file_header.timestep = _read_int(stream)
    file_header.include_unitcell = bool(_read_int(stream))
    for i in range(8):
        assert _read_int(stream) == 0
    file_header.charmm_version = _read_int(stream)
    assert _read_int(stream) == 84
    title_section_size = _read_int(stream)
    n_titles = _read_int(stream)
    len_title = int((title_section_size - 4) / 2)
    for i in range(n_titles):
        stream.read(len_title)
    assert _read_int(stream) == title_section_size
    assert _read_int(stream) == 4
    file_header.n_particles = _read_int(stream)
    assert _read_int(stream) == 4
    return file_header


def _skip_frame(stream):
    for i in range(3):
        len_section = _read_int(stream)
        stream.seek(len_section, 1)
        assert _read_int(stream) == len_section


def _read_frame_header(stream):
    frame_header = _DCDFrameHeader()
    frame_header_size = _read_int(stream)
    frame_header.box_a = _read_double(stream)
    frame_header.box_gamma = _read_double(stream)
    frame_header.box_b = _read_double(stream)
    frame_header.box_beta = _read_double(stream)
    frame_header.box_alpha = _read_double(stream)
    frame_header.box_c = _read_double(stream)
    assert _read_int(stream) == frame_header_size
    return frame_header


def _read_frame_body(stream, xyz):
    N = xyz.shape[1]
    for i in range(3):
        len_section = _read_int(stream)
        for j in range(N):
            xyz[i][j] = _read_float(stream)
        assert _read_int(stream) == len_section


def scan(stream):
    file_header = _read_file_header(stream)
    offsets = []
    for i in range(file_header.num_frames):
        offsets.append(stream.tell())
        _read_frame_header(stream)
        _skip_frame(stream)
    return file_header.__dict__, offsets


def read_frame(stream, xyz, offset=-1):
    if offset >= 0:
        stream.seek(offset)
    frame_header = _read_frame_header(stream)
    _read_frame_body(stream, xyz)
    return frame_header.__dict__
