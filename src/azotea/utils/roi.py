# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import re
import gettext

# -------------------
# Third party imports
# -------------------

import exifread
import rawpy

#--------------
# local imports
# -------------

# Support for internationalization
_ = gettext.gettext

# ----------------------
# Module utility classes
# ----------------------

class Point:
    """ Point class represents and manipulates x,y coords. """

    PATTERN = r'\((\d+),(\d+)\)'

    @classmethod
    def from_string(cls, point_str):
        pattern = re.compile(Point.PATTERN)
        matchobj = pattern.search(Rect_str)
        if matchobj:
            x = int(matchobj.group(1))
            y = int(matchobj.group(2))
            return cls(x,y)
        else:
            return None

    def __init__(self, x=0, y=0):
        """ Create a new point at the origin """
        self.x = x
        self.y = y

    def __add__(self, rect):
        return NotImplementedError

    def __repr__(self):
        return f"({self.x},{self.y})"

class Rect:
    """ Region of interest  """

    PATTERN = r'\[(\d+):(\d+),(\d+):(\d+)\]'

    @classmethod
    def from_string(cls, Rect_str):
        '''numpy sections style'''
        pattern = re.compile(Rect.PATTERN)
        matchobj = pattern.search(Rect_str)
        if matchobj:
            y1 = int(matchobj.group(1))
            y2 = int(matchobj.group(2))
            x1 = int(matchobj.group(3))
            x2 = int(matchobj.group(4))
            return cls(x1,x2,y1,y2)
        else:
            return None

    @classmethod
    def from_dict(cls, Rect_dict):
        return cls(Rect_dict['x1'], Rect_dict['x2'],Rect_dict['y1'], Rect_dict['y2'])
        

    def __init__(self, x1 ,x2, y1, y2):        
        self.x1 = min(x1,x2)
        self.y1 = min(y1,y2)
        self.x2 = max(x1,x2)
        self.y2 = max(y1,y2)


    def to_dict(self):
        return {'x1':self.x1, 'y1':self.y1, 'x2':self.x2, 'y2':self.y2}
        
    def dimensions(self):
        '''returns width and height'''
        return abs(self.x2 - self.x1), abs(self.y2 - self.y1)

    def __add__(self, point):
        return Rect(self.x1 + point.x, self.x2 + point.x, self.y1 + point.y, self.y2 + point.y)

    def __radd__(self, point):
        return self.__add__(point)
        
    def __repr__(self):
        '''string in NumPy section notation'''
        return f"[{self.y1}:{self.y2},{self.x1}:{self.x2}]"
  
def reshape_rect(filename, rect):
    with open(filename, 'rb') as f:
        exif = exifread.process_file(f, details=False)
        if not exif:
            raise ValueError("Could not open EXIF metadata")
    # Get the real RAW dimensions instead
    with rawpy.imread(filename) as img:
        imageHeight, imageWidth = img.raw_image.shape
    imageHeight = imageHeight //2 # From raw dimensions without debayering
    imageWidth =  imageWidth  //2  # to dimensions we actually handle
    width, height = rect.dimensions()
    center=Point(imageWidth//2,imageHeight//2)
    x1 = (imageWidth  -  width)//2
    y1 = (imageHeight - height)//2
    rect += Point(x1,y1)  # Shift ROI using this (x1,y1) point
    result = rect.to_dict()
    result['display_name'] = str(rect)
    result['comment'] = _("ROI for {0}, centered at P={1}, width={2}, height={3}").format(str(exif.get('Image Model')),center,width,height)
    return result

