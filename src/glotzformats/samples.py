POS_HPMC = """boxMatrix 10 0 0 0 10 0 0 0 10
def A "poly3d 4 1.0 0.0 -0.707106 -1.0 0.0 -0.707106 0.0 1.0 0.707106 0.0 -1.0 0.707106"
A 1.82294440269 15.4535045624 14.8948659897 1 0 0 0
A -7.82164478302 10.8672037125 -2.95065999031 1 0 0 0
A -6.71628189087 -14.6842060089 -8.78729343414 1 0 0 0
eof
boxMatrix 10 0 0 0 10 0 0 0 10
def A "poly3d 4 1.0 0.0 -0.707106 -1.0 0.0 -0.707106 0.0 1.0 0.707106 0.0 -1.0 0.707106"
A 1.82294440269 15.4535045624 14.8948659897 1 0 0 0
A -7.82164478302 10.8672037125 -2.95065999031 1 0 0 0
A -6.764575947059 -14.8567379768 -8.685973902168 0.9805919875544 0.1852591352614 0.06382813748332 0.006661502213598
eof
boxMatrix 10 0 0 0 10 0 0 0 10
def A "poly3d 4 1.0 0.0 -0.707106 -1.0 0.0 -0.707106 0.0 1.0 0.707106 0.0 -1.0 0.707106"
A 1.82294440269 15.4535045624 14.8948659897 1 0 0 0
A -7.82164478302 10.8672037125 -2.95065999031 1 0 0 0
A -6.764575947059 -14.8567379768 -8.685973902168 0.9805919875544 0.1852591352614 0.06382813748332 0.006661502213598
eof"""

POS_INCSIM = """#[data] Steps X-Length Y-Length Z-Length
000000  10.000  10.000  10.000
000001  10.000  10.000  10.000
000002  10.000  10.000  10.000
#[done]
boxMatrix 10.0 0 0 0 10.0 0 0 0 10.0
def A "poly3d 4 1.0 0.0 -0.707106 -1.0 0.0 -0.707106 0.0 1.0 0.707106 0.0 -1.0 0.707106"
A 0 1.82294440269 15.4535045624 14.8948659897 1 0 0 0
A 0 -7.82164478302 10.8672037125 -2.95065999031 1 0 0 0
A 0 -6.71628189087 -14.6842060089 -8.78729343414 1 0 0 0
eof
#[data] Steps X-Length Y-Length Z-Length
000003  10.000  10.000  10.000
000004  10.000  10.000  10.000
000005  10.000  10.000  10.000"""

POS_MONOTYPE = """#[data] Steps           Time            Vol             Packing         Press           MSD             DeltaX          DeltaQ          DeltaV          AcceptX         AcceptQ         AcceptV         Ensemble        Shear           Overlaps        X-Length        Y-Length        Z-Length        XY-Angle        XZ-Angle        YZ-Angle        RNGstate        RNGstatew
5683290 0       13854.542584873 0.553368299     11      2.219808854     0.089573664     0.060274335     0.749136778     0.296100599     0.27948962      0.285714286     2       0       0       24.017662106    24.017662106    24.017662106    90      90      90      3728705625      1305200346
#[done]
boxMatrix 10.0 0 0 0 10.0 0 0 0 10.0
shape "poly3d 12 0.333333 1 0.333333 1 0.333333 0.333333 0.333333 0.333333 1 -1 -0.333333 0.333333 -0.333333 -1 0.333333 -0.333333 -0.333333 1 -0.333333 0.333333 -1 -0.333333 1 -0.333333 -1 0.333333 -0.333333 0.333333 -0.333333 -1 1 -0.333333 -0.333333 0.333333 -1 -0.333333"
ff0000 -11.320217528 -8.749537435 -8.011389974 -0.015480238 -0.664626252 0.724293168 -0.182843416
ff0000 -8.199472831 -9.791602851 10.203158041 0.250075053 -0.547617436 0.316252355 -0.733186238
eof"""

POS_INJAVIS = """//date: Thursday, July 23, 2015 2:50:06 PM
#[data] Steps   Time    Vol     Packing Press   MSD     DeltaX  DeltaQ  DeltaV  AcceptX AcceptQ AcceptV Ensemble        Shear   Overlaps        X-Length        Y-Length        Z-Length        XY-Angle        XZ-Angle        YZ-Angle        RNGstate        RNGstatew       
5683290 0       13854.5426      0.553368299     11      2.21980885      0.089573664     0.060274335     0.749136778     0.296100599     0.27948962      0.285714286     2       0       0       24.0176621      24.0176621      24.0176621      90      90      90      3.7287056E9     1.3052003E9     
#[done]

rotation        11.884065       -19.36126781    -1.96424213
antiAliasing    true
box     10.0    10.0      10.0
shape   "poly3d 12 0.333333     1       0.333333        1       0.333333        0.333333        0.333333        0.333333        1       -1      -0.333333       0.333333        -0.333333       -1      0.333333        -0.333333       -0.333333       1       -0.333333       0.333333        -1      -0.333333       1       -0.333333       -1      0.333333        -0.333333       0.333333        -0.333333       -1      1       -0.333333       -0.333333       0.333333        -1      -0.333333 ffff0000"
-11.32021753    -8.74953744     -8.01138997     -0.01548024     -0.66462625     0.724293168     -0.18284342
-8.19947283     -9.79160285     10.203158       0.250075053     -0.54761744     0.316252355     -0.73318624
eof"""
