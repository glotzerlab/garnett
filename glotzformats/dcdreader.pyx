import numpy as np
cimport numpy as np

DTYPE = np.float
ctypedef np.float DTYPE_t

cdef _DCDFileHeader _read_file_header(FILE *cfile):
    cdef _DCDFileHeader file_header
    assert _read_int(cfile) == 84
    cdef char c[4]
    assert fread(c, len('CORD'), 1, cfile) == 1
    assert c.startswith(b'CORD')
    file_header.num_frames = _read_int(cfile)
    file_header.m_start_timestep = _read_int(cfile)
    file_header.m_period = _read_int(cfile)
    file_header.timesteps = _read_int(cfile)
    for i in range(5):
        _read_int(cfile)
    file_header.timestep = _read_int(cfile)
    file_header.include_unitcell = _read_int(cfile)
    for i in range(8):
        assert _read_int(cfile) == 0
    file_header.charmm_version = _read_int(cfile)
    assert _read_int(cfile) == 84
    title_section_size = _read_int(cfile)
    n_titles = _read_int(cfile)
    len_title = int((title_section_size - 4) / 2)
    for i in range(n_titles):
        fseek(cfile, len_title, SEEK_CUR)
    assert _read_int(cfile) == title_section_size
    assert _read_int(cfile) == 4
    file_header.n_particles = _read_int(cfile)
    assert _read_int(cfile) == 4

    fflush(cfile)
    return file_header


cdef _DCDFrameHeader _read_frame_header(FILE *cfile):
    cdef _DCDFrameHeader frame_header
    frame_header_size = _read_int(cfile)
    frame_header.box_a = _read_double(cfile)
    frame_header.box_gamma = _read_double(cfile)
    frame_header.box_b = _read_double(cfile)
    frame_header.box_beta = _read_double(cfile)
    frame_header.box_alpha = _read_double(cfile)
    frame_header.box_c = _read_double(cfile)
    assert _read_int(cfile) == frame_header_size

    fflush(cfile)
    return frame_header


cdef void _skip_frame(FILE * cfile):
    for i in range(3):
        len_section = _read_int(cfile)
        fseek(cfile, len_section, SEEK_CUR)
        assert _read_int(cfile) == len_section
    fflush(cfile)


cdef _scan(FILE *cfile):
    file_header = _read_file_header(cfile)
    n_frames = int(file_header.num_frames)
    offsets = []
    for i in range(n_frames):
        offsets.append(ftell(cfile))
        _read_frame_header(cfile)
        _skip_frame(cfile)
    return file_header, offsets

cdef _read_frame_body(FILE * cfile, np.ndarray xyz):
    N = len(xyz)
    for i in range(3):
        len_section = _read_int(cfile)
        for j in range(N):
            xyz[j][i] = _read_float(cfile)
        assert _read_int(cfile) == len_section
    fflush(cfile)


def scan(stream):
    cdef FILE* cfile
    cfile = fdopen(stream.fileno(), 'rb')
    return _scan(cfile)


def read_frame(stream, xyz, offset=None):
    cdef FILE* cfile
    cfile = fdopen(stream.fileno(), 'rb')
    if offset is not None:
        fseek(cfile, offset, SEEK_SET)
    frame_header = _read_frame_header(cfile)
    _read_frame_body(cfile, xyz)
    return frame_header
