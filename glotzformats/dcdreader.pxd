from libc.stdio cimport *

cimport numpy as np


cdef extern from "stdio.h":
    FILE *fdopen(int, const char *)


cdef struct _DCDFileHeader:
    unsigned int num_frames
    unsigned int m_start_timestep
    unsigned int m_period
    unsigned int timesteps
    unsigned int timestep
    unsigned int include_unitcell
    unsigned int charmm_version
    unsigned int n_particles


cdef struct _DCDFrameHeader:
    float box_a
    float box_gamma
    float box_b
    float box_beta
    float box_alpha
    float box_c


cdef inline unsigned int _read_int(FILE *fd):
    cdef unsigned int i
    assert fread(& i, sizeof(i), 1, fd) == 1
    return i


cdef inline unsigned long _read_long(FILE *fd):
    cdef unsigned long i
    assert fread(& i, sizeof(i), 1, fd) == 1
    return i


cdef inline double _read_double(FILE *fd):
    cdef double d
    assert fread(& d, sizeof(d), 1, fd) == 1
    return d



cdef inline float _read_float(FILE *fd):
    cdef float f
    assert fread(& f, sizeof(f), 1, fd) == 1
    return f


cdef inline _euler_to_quaternion(alpha):
    q = np.zeros((len(alpha), 4))
    q.T[0] = np.cos(alpha/2)
    q.T[1] = q.T[2] = q.T[3] = np.sin(alpha/2)
    return q
