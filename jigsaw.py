#!/usr/bin/python

"""Generate a jigsaw puzzle pattern for laser cutting."""

#    Copyright 2019 Lawrence Kesteloot
# 
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
# 
#        http://www.apache.org/licenses/LICENSE-2.0
# 
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import random
import math
import optparse

tau = 2*math.pi

# Number of pieces.
COLUMN_COUNT = 8
ROW_COUNT = 10

# This doesn't matter so much -- you can scale it after importing it into the
# drawing package.
DPI = 96
WIDTH = COLUMN_COUNT*DPI
HEIGHT = ROW_COUNT*DPI

COLOR = "#000000"
CORNER_RADIUS = WIDTH/ROW_COUNT/3.0

class Vector:
    """2D vector class."""

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __str__(self):
        return "(%g,%g)" % (self.x, self.y)

    def __repr__(self):
        return str(self)

    def __neg__(self):
        return Vector(-self.x, -self.y)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vector(self.x*other, self.y*other)

    def __div__(self, other):
        return Vector(self.x/other, self.y/other)

    # Some installations of Python2 auto-import "division" from future,
    # so we must handle that too.
    def __truediv__(self, other):
        return Vector(self.x/other, self.y/other)

    def length(self):
        return math.sqrt(self.x**2 + self.y**2)

    def normalized(self):
        return self/self.length()

    def reciprocal(self):
        """Rotated 90 counter-clockwise."""
        return Vector(-self.y, self.x)

def write_header(out):
    """Write the SVG header to file object "out"."""

    out.write("""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd" [
<!ENTITY ns_svg "http://www.w3.org/2000/svg">
]>
<svg xmlns="&ns_svg;" width="%d" height="%d" overflow="visible">
    <g id="Layer_1">
""" % (WIDTH, HEIGHT))

def polyline(out, p, color):
    """Write a polyline object to SVG file "out". "p" is a list of Vector objects, and
    "color" is a string representing any SVG-legal color."""

    points = " ".join("%g,%g" % (v.x, v.y) for v in p)
    out.write('        <polyline fill="none" stroke="%s" stroke-width="1" points="%s"/>\n' %
            (color, points))

def write_footer(out):
    """Write the SVG footer to the file object "out"."""

    out.write("""    </g>
</svg>
""")

def append_circle(p, v, n, center, radius, start_angle, end_angle):
    """Append a circle to list of Vector points "p". The orthonormal "v" and
    "n" vectors represent the basis vectors for the circle. The "center"
    vector is the circle's center, and the start and end angle are relative
    to the basis vectors. An angle of 0 means all "v", tau/4 means all "n"."""

    # Fraction of the circle we're covering, in radians.
    angle_span = end_angle - start_angle

    # The number of segments we want to use for this span. Use 20 for a full circle.
    segment_count = int(math.ceil(20*math.fabs(angle_span)/tau))

    for i in range(segment_count + 1):
        th = start_angle + angle_span*i/segment_count
        point = center + v*math.cos(th)*radius + n*math.sin(th)*radius
        p.append(point)

def make_knob(outs, start, end, color):
    """Make a knob (the part that sticks out from one piece into another).
    This includes the entire segment on the side of a square.  "start" and
    "end" are points that represent the ends of the line segment. In other
    words, if we have a puzzle piece with four corners, then call this
    function four times with the four corners in succession."""

    # Length of the line on the side of the puzzle piece.
    line_length = (end - start).length()

    # Choose the base of the knob. Pick the midpoint of the line
    # and perturb it a bit.
    mid = start + (end - start)*(0.4 + random.random()*0.2)

    # The first part of our basis vector. This points down the edge.
    v = (end - start).normalized()

    # Pick a random direction for the knob (1 or -1).
    direction = random.randint(0, 1)*2 - 1

    # Find the other axis, normal to the line.
    n = v.reciprocal()*direction

    # Where the knob starts and ends, along the line.
    knob_start = mid - v*line_length*0.1
    knob_end = mid + v*line_length*0.1

    # Radius of the small circle that comes off the edge.
    small_radius = line_length*(0.05 + random.random()*0.01)

    # Radius of the larger circle that makes the actual knob.
    large_radius = small_radius*1.8

    # Magic happens here. See this page for an explanation:
    # http://www.teamten.com/lawrence/projects/jigsaw-puzzle-on-laser-cutter/
    tri_base = (knob_end - knob_start).length()/2
    tri_hyp = small_radius + large_radius
    tri_height = math.sqrt(tri_hyp**2 - tri_base**2)
    large_center_distance = small_radius + tri_height
    small_start_angle = -tau/4
    small_end_angle = math.asin(tri_height/tri_hyp)
    large_slice_angle = math.asin(tri_base/tri_hyp)
    large_start_angle = tau*3/4 - large_slice_angle
    large_end_angle = -tau/4 + large_slice_angle

    # Make our polyline.
    p = []
    p.append(start)
    p.append(knob_start)
    append_circle(p, v, n, knob_start + n*small_radius, small_radius,
            small_start_angle, small_end_angle)
    append_circle(p, v, n, mid + n*large_center_distance, large_radius,
            large_start_angle, large_end_angle)
    append_circle(p, -v, n, knob_end + n*small_radius, small_radius,
            small_end_angle, small_start_angle)
    p.append(knob_end)
    p.append(end)

    for out in outs:
        polyline(out, p, color)

# Generate a single SVG file for the puzzle.
def generate_single():
    out = open("jigsaw.svg", "w")

    write_header(out)

    # The rounded-corner rectangle on the outside of the puzzle.
    out.write('        <rect x="0" y="0" rx="%g" ry="%g" width="%g" height="%g" fill="none" stroke="%s"/>\n' %
            (CORNER_RADIUS, CORNER_RADIUS, WIDTH, HEIGHT, COLOR))

    # Horizontal lines.
    for row in range(ROW_COUNT - 1):
        for column in range(COLUMN_COUNT):
            start = Vector(column*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT)
            end = Vector((column + 1)*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT)
            make_knob([out], start, end, COLOR)

    # Vertical lines.
    for row in range(ROW_COUNT):
        for column in range(COLUMN_COUNT - 1):
            start = Vector((column + 1)*WIDTH/COLUMN_COUNT, row*HEIGHT/ROW_COUNT)
            end = Vector((column + 1)*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT)
            make_knob([out], start, end, COLOR)

    write_footer(out)

# Generate one SVG file for each piece of the puzzle.
def generate_separate():
    # Row-major files.
    outs = []
    def get_out(row, column):
        assert row >= 0 and row < ROW_COUNT and column >= 0 and column < COLUMN_COUNT
        return outs[row*COLUMN_COUNT + column]

    for row in range(ROW_COUNT):
        for column in range(COLUMN_COUNT):
            out = open("jigsaw_%d_%d.svg" % (row, column), "w")
            outs.append(out)

    for out in outs:
        write_header(out)

    # Horizontal lines.
    for row in range(ROW_COUNT - 1):
        for column in range(COLUMN_COUNT):
            start = Vector(column*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT)
            end = Vector((column + 1)*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT)
            neighbors = [get_out(row, column), get_out(row + 1, column)]
            make_knob(neighbors, start, end, COLOR)

    # Vertical lines.
    for row in range(ROW_COUNT):
        for column in range(COLUMN_COUNT - 1):
            start = Vector((column + 1)*WIDTH/COLUMN_COUNT, row*HEIGHT/ROW_COUNT)
            end = Vector((column + 1)*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT)
            neighbors = [get_out(row, column), get_out(row, column + 1)]
            make_knob(neighbors, start, end, COLOR)

    # Left border.
    for row in range(ROW_COUNT):
        column = 0
        p = []
        p.append(Vector(column*WIDTH/COLUMN_COUNT, row*HEIGHT/ROW_COUNT))
        p.append(Vector(column*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT))
        polyline(get_out(row, column), p, COLOR)

    # Right border.
    for row in range(ROW_COUNT):
        column = COLUMN_COUNT - 1
        p = []
        p.append(Vector((column + 1)*WIDTH/COLUMN_COUNT, row*HEIGHT/ROW_COUNT))
        p.append(Vector((column + 1)*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT))
        polyline(get_out(row, column), p, COLOR)

    # Top border.
    for column in range(COLUMN_COUNT):
        row = 0
        p = []
        p.append(Vector(column*WIDTH/COLUMN_COUNT, row*HEIGHT/ROW_COUNT))
        p.append(Vector((column + 1)*WIDTH/COLUMN_COUNT, row*HEIGHT/ROW_COUNT))
        polyline(get_out(row, column), p, COLOR)

    # Bottom border.
    for column in range(COLUMN_COUNT):
        row = ROW_COUNT - 1
        p = []
        p.append(Vector(column*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT))
        p.append(Vector((column + 1)*WIDTH/COLUMN_COUNT, (row + 1)*HEIGHT/ROW_COUNT))
        polyline(get_out(row, column), p, COLOR)

    for out in outs:
        write_footer(out)

def main():
    parser = optparse.OptionParser()
    parser.add_option("--separate",
            action="store_true", dest="separate", default=False,
            help="generate a separate file for each piece")

    (options, args) = parser.parse_args()

    if options.separate:
        generate_separate()
    else:
        generate_single()

if __name__ == "__main__":
    main()
