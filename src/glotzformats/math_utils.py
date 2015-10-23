"""Collection of math functions.

Author: Richmond Newmann, newmanrs@umich.edu, University of Michigan
"""

import math
import numpy

# Obtain quaternion conjugate


def quaternionConjugate(q):
    return numpy.array([q[0], -q[1], -q[2], -q[3]])

# quaternion multplication a,b.


def quaternionMultiply(a, b):
    c1 = (a[0] * b[0]) - (a[1] * b[1]) - (a[2] * b[2]) - (a[3] * b[3])
    c2 = (a[0] * b[1]) + (a[1] * b[0]) + (a[2] * b[3]) - (a[3] * b[2])
    c3 = (a[0] * b[2]) - (a[1] * b[3]) + (a[2] * b[0]) + (a[3] * b[1])
    c4 = (a[0] * b[3]) + (a[1] * b[2]) - (a[2] * b[1]) + (a[3] * b[0])
    c = numpy.array([c1, c2, c3, c4])
    return c

# Generate a quaternion corresponding to a rotation by theta around an axis v.


def quaternionAxisAngle(v, theta):
    ha = theta / 2.0  # Half Angle
    q0 = numpy.cos(ha)
    vn = normalize(v)
    q1 = vn[0] * numpy.sin(ha)
    q2 = vn[1] * numpy.sin(ha)
    q3 = vn[2] * numpy.sin(ha)
    return numpy.array([q0, q1, q2, q3])
    # return normalize(arr)

# Rotate a vector v by quaternion q


def rotateVector(v, q):
    qc = quaternionConjugate(q)
    vq = numpy.array([0, v[0], v[1], v[2]])  # v as a 'pure' quaternion
    # vrotq = q vq qc, vrotq as a quaternion (with 0 first comp)
    vrotq = quaternionMultiply(q, quaternionMultiply(vq, qc))

    return numpy.array([vrotq[1], vrotq[2], vrotq[3]])


def norm(a):
    magsq = 0
    for component in a:
        magsq += component * component
    return math.sqrt(magsq)


def normalize(a):
    magsq = 0
    for component in a:
        magsq += component * component
    return a / math.sqrt(magsq)

# Calculate unit bisector vector


def unitBisector(v1, v2):
    if len(v1) != len(v2):
        raise Exception("Bisector inputs must have same length")
    return normalize(normalize(v1) + normalize(v2))

# Find the quaternion that would rotate v1 to v2
# that is return q that satisifes v2 = q v1 qc
# Just rotate around bisector by Pi.


def quaternionRotateVectorOntoVector(v1, v2):
    bis = unitBisector(v1, v2)
    return quaternionAxisAngle(bis, math.pi)
