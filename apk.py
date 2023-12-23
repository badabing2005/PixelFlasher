# This file is part of Androguard.
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

import io
from struct import pack, unpack
from xml.sax.saxutils import escape

from xml.dom import minidom

######################################################## AXML FORMAT ########################################################
# Translated from http://code.google.com/p/android4me/source/browse/src/android/content/res/AXmlResourceParser.java
# Ref: https://github.com/tracer0tong/axmlprinter/blob/master/apk.py

UTF8_FLAG = 0x00000100


class StringBlock:
    def __init__(self, buff):
        self.start = buff.get_idx()
        self._cache = {}
        self.header = unpack('<h', buff.read(2))[0]
        self.header_size = unpack('<h', buff.read(2))[0]

        self.chunkSize = unpack('<i', buff.read(4))[0]
        self.stringCount = unpack('<i', buff.read(4))[0]
        self.styleOffsetCount = unpack('<i', buff.read(4))[0]

        self.flags = unpack('<i', buff.read(4))[0]
        self.m_isUTF8 = ((self.flags & UTF8_FLAG) != 0)

        self.stringsOffset = unpack('<i', buff.read(4))[0]
        self.stylesOffset = unpack('<i', buff.read(4))[0]

        self.m_stringOffsets = []
        self.m_styleOffsets = []
        self.m_strings = []
        self.m_styles = []

        for _ in range(0, self.stringCount):
            self.m_stringOffsets.append(unpack('<i', buff.read(4))[0])

        for _ in range(0, self.styleOffsetCount):
            self.m_styleOffsets.append(unpack('<i', buff.read(4))[0])

        size = self.chunkSize - self.stringsOffset
        if self.stylesOffset != 0:
            size = self.stylesOffset - self.stringsOffset

        # FIXME
        if (size % 4) != 0:
            print("ooo")

        for _ in range(0, size):
            self.m_strings.append(unpack('=b', buff.read(1))[0])

        if self.stylesOffset != 0:
            size = self.chunkSize - self.stylesOffset

            # FIXME
            if (size % 4) != 0:
                print("ooo")

            for _ in range(0, size / 4):
                self.m_styles.append(unpack('<i', buff.read(4))[0])

    def getRaw(self, idx):
        if idx in self._cache:
            return self._cache[idx]

        if idx < 0 or not self.m_stringOffsets or idx >= len(self.m_stringOffsets):
            return ""

        offset = self.m_stringOffsets[idx]

        if not self.m_isUTF8:
            length = self.getShort2(self.m_strings, offset)
            offset += 2
            self._cache[idx] = self.decode(self.m_strings, offset, length)
        else:
            offset += self.getVarint(self.m_strings, offset)[1]
            varint = self.getVarint(self.m_strings, offset)

            offset += varint[1]
            length = varint[0]

            self._cache[idx] = self.decode2(self.m_strings, offset, length)

        return self._cache[idx]

    def decode(self, array, offset, length):
        length = length * 2
        length = length + length % 2

        data = bytes()

        for i in range(0, length):
            t_data = pack("=b", self.m_strings[offset + i])
            data += t_data
            if data[-2:] == b"\x00\x00":
                break

        end_zero = data.find(b"\x00\x00")
        if end_zero != -1:
            data = data[:end_zero]
        return data.decode('utf-16')

    def decode2(self, array, offset, length):
        data = bytes()

        for i in range(0, length):
            t_data = pack("=b", self.m_strings[offset + i])
            data += t_data
        return data.decode('utf-8')

    def getVarint(self, array, offset):
        val = array[offset]
        more = (val & 0x80) != 0
        val &= 0x7f

        if not more:
            return val, 1
        return val << 8 | array[offset + 1] & 0xff, 2

    def getShort(self, array, offset):
        value = array[offset / 4]
        # if ((offset % 4) / 2) == 0:
        if offset % 4 == 0:
            return value & 0xFFFF
        else:
            return value >> 16

    def getShort2(self, array, offset):
        return (array[offset + 1] & 0xff) << 8 | array[offset] & 0xff

    def show(self):
        print("StringBlock", hex(self.start), hex(self.header), hex(self.header_size), hex(self.chunkSize), hex(self.stringsOffset), self.m_stringOffsets)
        for i in range(0, len(self.m_stringOffsets)):
            print(i, repr(self.getRaw(i)))

class SV :
    def __init__(self, size, buff) :
        self.__size = size
        self.__value = unpack(self.__size, buff)[0]

    def _get(self) :
        return pack(self.__size, self.__value)

    def __str__(self) :
        return "0x%x" % self.__value

    def __int__(self) :
        return self.__value

    def get_value_buff(self) :
        return self._get()

    def get_value(self) :
        return self.__value

    def set_value(self, attr) :
        self.__value = attr

class BuffHandle:
    def __init__(self, buff):
        self.__buff = buff
        self.__idx = 0

    def size(self):
        return len(self.__buff)

    def set_idx(self, idx):
        self.__idx = idx

    def get_idx(self):
        return self.__idx

    def readNullString(self, size):
        return self.read(size)

    def read_b(self, size) :
        return self.__buff[ self.__idx : self.__idx + size ]

    def read_at(self, offset, size):
        return self.__buff[ offset : offset + size ]

    def read(self, size) :
        if isinstance(size, SV) :
            size = size.value

        buff = self.__buff[ self.__idx : self.__idx + size ]
        self.__idx += size

        return buff

    def end(self) :
        return self.__idx == len(self.__buff)

ATTRIBUTE_IX_NAMESPACE_URI  = 0
ATTRIBUTE_IX_NAME           = 1
ATTRIBUTE_IX_VALUE_STRING   = 2
ATTRIBUTE_IX_VALUE_TYPE     = 3
ATTRIBUTE_IX_VALUE_DATA     = 4
ATTRIBUTE_LENGHT            = 5

CHUNK_AXML_FILE             = 0x00080003
CHUNK_RESOURCEIDS           = 0x00080180
CHUNK_XML_FIRST             = 0x00100100
CHUNK_XML_START_NAMESPACE   = 0x00100100
CHUNK_XML_END_NAMESPACE     = 0x00100101
CHUNK_XML_START_TAG         = 0x00100102
CHUNK_XML_END_TAG           = 0x00100103
CHUNK_XML_TEXT              = 0x00100104
CHUNK_XML_LAST              = 0x00100104

START_DOCUMENT              = 0
END_DOCUMENT                = 1
START_TAG                   = 2
END_TAG                     = 3
TEXT                        = 4


class AXMLParser:
    def __init__(self, raw_buff):
        self.reset()

        self.buff = BuffHandle(raw_buff)

        self.buff.read(4)
        self.buff.read(4)

        self.sb = StringBlock(self.buff)

        self.m_resourceIDs = []
        self.m_prefixuri = {}
        self.m_uriprefix = {}
        self.m_prefixuriL = []

        self.visited_ns = []

    def reset(self):
        self.m_event = -1
        self.m_lineNumber = -1
        self.m_name = -1
        self.m_namespaceUri = -1
        self.m_attributes = []
        self.m_idAttribute = -1
        self.m_classAttribute = -1
        self.m_styleAttribute = -1

    def next(self):
        self.doNext()
        return self.m_event

    def doNext(self):  # sourcery skip: remove-redundant-if, split-or-ifs
        if self.m_event == END_DOCUMENT:
            return

        event = self.m_event

        self.reset()
        while True:
            chunkType = -1

            # Fake END_DOCUMENT event.
            # if event == END_TAG:
            #     pass

            # START_DOCUMENT
            if event == START_DOCUMENT:
                chunkType = CHUNK_XML_START_TAG
            else:
                if self.buff.end():
                    self.m_event = END_DOCUMENT
                    break
                chunkType = unpack('<L', self.buff.read(4))[0]

            if chunkType == CHUNK_RESOURCEIDS:
                chunkSize = unpack('<L', self.buff.read(4))[0]
                # FIXME
                if chunkSize < 8 or chunkSize % 4 != 0:
                    print("ooo")

                for _ in range(0, int(chunkSize / 4) - 2):
                    self.m_resourceIDs.append(unpack('<L', self.buff.read(4))[0])

                continue

            # FIXME
            if chunkType < CHUNK_XML_FIRST or chunkType > CHUNK_XML_LAST:
                print("ooo")

            # Fake START_DOCUMENT event.
            if chunkType == CHUNK_XML_START_TAG and event == -1:
                self.m_event = START_DOCUMENT
                break

            self.buff.read(4)  # /*chunkSize*/
            lineNumber = unpack('<L', self.buff.read(4))[0]
            self.buff.read(4)  # 0xFFFFFFFF

            if chunkType in [CHUNK_XML_START_NAMESPACE, CHUNK_XML_END_NAMESPACE]:
                if chunkType == CHUNK_XML_START_NAMESPACE:
                    prefix = unpack('<L', self.buff.read(4))[0]
                    uri = unpack('<L', self.buff.read(4))[0]

                    self.m_prefixuri[prefix] = uri
                    self.m_uriprefix[uri] = prefix
                    self.m_prefixuriL.append((prefix, uri))
                    self.ns = uri
                else:
                    self.ns = -1
                    self.buff.read(4)
                    self.buff.read(4)
                    (prefix, uri) = self.m_prefixuriL.pop()
                    #del self.m_prefixuri[ prefix ]
                    #del self.m_uriprefix[ uri ]

                continue

            self.m_lineNumber = lineNumber

            if chunkType == CHUNK_XML_START_TAG:
                self.m_namespaceUri = unpack('<L', self.buff.read(4))[0]
                self.m_name = unpack('<L', self.buff.read(4))[0]

                # FIXME
                self.buff.read(4)  # flags

                attributeCount = unpack('<L', self.buff.read(4))[0]
                self.m_idAttribute = (attributeCount >> 16) - 1
                attributeCount = attributeCount & 0xFFFF
                self.m_classAttribute = unpack('<L', self.buff.read(4))[0]
                self.m_styleAttribute = (self.m_classAttribute >> 16) - 1

                self.m_classAttribute = (self.m_classAttribute & 0xFFFF) - 1

                for _ in range(0, attributeCount * ATTRIBUTE_LENGHT):
                    self.m_attributes.append(unpack('<L', self.buff.read(4))[0])

                for i in range(ATTRIBUTE_IX_VALUE_TYPE, len(self.m_attributes), ATTRIBUTE_LENGHT):
                    self.m_attributes[i] = self.m_attributes[i] >> 24

                self.m_event = START_TAG
                break

            if chunkType == CHUNK_XML_END_TAG:
                self.m_namespaceUri = unpack('<L', self.buff.read(4))[0]
                self.m_name = unpack('<L', self.buff.read(4))[0]
                self.m_event = END_TAG
                break

            if chunkType == CHUNK_XML_TEXT:
                self.m_name = unpack('<L', self.buff.read(4))[0]

                # FIXME
                self.buff.read(4)
                self.buff.read(4)

                self.m_event = TEXT
                break

    def getPrefixByUri(self, uri):
        try:
            return self.m_uriprefix[uri]
        except KeyError:
            return -1

    def getPrefix(self):
        try:
            return self.sb.getRaw(self.m_uriprefix[self.m_namespaceUri])
        except KeyError:
            return ''

    def getName(self):
        if self.m_name == -1 or self.m_event not in [START_TAG, END_TAG]:
            return ''

        return self.sb.getRaw(self.m_name)

    def getText(self) :
        if self.m_name == -1 or self.m_event != TEXT :
            return ''

        return self.sb.getRaw(self.m_name)

    def getNamespacePrefix(self, pos):
        prefix = self.m_prefixuriL[pos][0]
        return self.sb.getRaw(prefix)

    def getNamespaceUri(self, pos):
        uri = self.m_prefixuriL[pos][1]
        return self.sb.getRaw(uri)

    def getXMLNS(self):
        buff = ""
        for i in self.m_uriprefix:
            if i not in self.visited_ns:
                buff += "xmlns:%s=\"%s\"\n" % (self.sb.getRaw(self.m_uriprefix[i]), self.sb.getRaw(self.m_prefixuri[self.m_uriprefix[i]]))
                self.visited_ns.append(i)
        return buff

    def getNamespaceCount(self, pos) :
        pass

    def getAttributeOffset(self, index):
        # FIXME
        if self.m_event != START_TAG:
            print("Current event is not START_TAG.")

        offset = index * 5
        # FIXME
        if offset >= len(self.m_attributes):
            print("Invalid attribute index")

        return offset

    def getAttributeCount(self):
        if self.m_event != START_TAG:
            return -1

        return len(self.m_attributes) / ATTRIBUTE_LENGHT

    def getAttributePrefix(self, index):
        offset = self.getAttributeOffset(index)
        uri = self.m_attributes[offset + ATTRIBUTE_IX_NAMESPACE_URI]

        prefix = self.getPrefixByUri(uri)

        if prefix == -1:
            return ""

        return self.sb.getRaw(prefix)

    def getAttributeName(self, index) :
        offset = self.getAttributeOffset(index)
        name = self.m_attributes[offset+ATTRIBUTE_IX_NAME]

        if name == -1 :
            return ""

        return self.sb.getRaw( name )

    def getAttributeValueType(self, index) :
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset+ATTRIBUTE_IX_VALUE_TYPE]

    def getAttributeValueData(self, index) :
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset+ATTRIBUTE_IX_VALUE_DATA]

    def getAttributeValue(self, index) :
        offset = self.getAttributeOffset(index)
        valueType = self.m_attributes[offset+ATTRIBUTE_IX_VALUE_TYPE]
        if valueType == TYPE_STRING :
            valueString = self.m_attributes[offset+ATTRIBUTE_IX_VALUE_STRING]
            return self.sb.getRaw( valueString )
        # WIP
        return ""
        #int valueData=m_attributes[offset+ATTRIBUTE_IX_VALUE_DATA];
        #return TypedValue.coerceToString(valueType,valueData);

TYPE_ATTRIBUTE          = 2
TYPE_DIMENSION          = 5
TYPE_FIRST_COLOR_INT    = 28
TYPE_FIRST_INT          = 16
TYPE_FLOAT              = 4
TYPE_FRACTION           = 6
TYPE_INT_BOOLEAN        = 18
TYPE_INT_COLOR_ARGB4    = 30
TYPE_INT_COLOR_ARGB8    = 28
TYPE_INT_COLOR_RGB4     = 31
TYPE_INT_COLOR_RGB8     = 29
TYPE_INT_DEC            = 16
TYPE_INT_HEX            = 17
TYPE_LAST_COLOR_INT     = 31
TYPE_LAST_INT           = 31
TYPE_NULL               = 0
TYPE_REFERENCE          = 1
TYPE_STRING             = 3

RADIX_MULTS             =   [ 0.00390625, 3.051758E-005, 1.192093E-007, 4.656613E-010 ]
DIMENSION_UNITS         =   [ "px","dip","sp","pt","in","mm","","" ]
FRACTION_UNITS          =   [ "%","%p","","","","","","" ]

COMPLEX_UNIT_MASK        =   15


class AXMLPrinter:
    def __init__(self, raw_buff):
        self.axml = AXMLParser(raw_buff)
        self.xmlns = False

        self.buff = ''

        while True:
            _type = self.axml.next()
#           print "tagtype = ", _type

            if _type == START_DOCUMENT:
                self.buff += '<?xml version="1.0" encoding="utf-8"?>\n'
            elif _type == START_TAG:
                # self.buff += '<' + self.getPrefix(self.axml.getPrefix()) + self.axml.getName() + '\n'
                self.buff += f'<{self.getPrefix(self.axml.getPrefix())}{self.axml.getName()}\n'
                self.buff += self.axml.getXMLNS()

                for i in range(0, int(self.axml.getAttributeCount())):
                    self.buff += "%s%s=\"%s\"\n" % ( self.getPrefix(
                        self.axml.getAttributePrefix(i) ), self.axml.getAttributeName(i), self._escape( self.getAttributeValue( i ) ) )

                # Modify by liyansong2018
                # self.buff += '>\n'
                self.buff += '>'

            elif _type == END_TAG :
                # self.buff += "</%s%s>\n" % ( self.getPrefix( self.axml.getPrefix() ), self.axml.getName() )
                # self.buff += "</%s%s>" % ( self.getPrefix( self.axml.getPrefix() ), self.axml.getName() )
                self.buff += f"</{self.getPrefix(self.axml.getPrefix())}{self.axml.getName()}>"

            elif _type == TEXT :
                # self.buff += "%s\n" % self.axml.getText()
                # self.buff += "%s" % self.axml.getText()
                self.buff += f"{self.axml.getText()}"

            elif _type == END_DOCUMENT :
                break

    # pleed patch
    def _escape(self, s):
        s = s.replace("&", "&amp;")
        s = s.replace('"', "&quot;")
        s = s.replace("'", "&apos;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        return escape(s)

    def get_buff(self):
        return self.buff

    def get_xml(self):
        return minidom.parseString(self.get_buff()).toprettyxml()

    def get_xml_obj(self):
        return minidom.parseString(self.get_buff())

    def getPrefix(self, prefix):
        if prefix is None or len(prefix) == 0:
            return ''

        return f'{prefix}:'

    def getAttributeValue(self, index):
        _type = self.axml.getAttributeValueType(index)
        _data = self.axml.getAttributeValueData(index)

        if _type == TYPE_STRING:
            return self.axml.getAttributeValue(index)

        elif _type == TYPE_ATTRIBUTE:
            return "?%s%08X" % (self.getPackage(_data), _data)

        elif _type == TYPE_REFERENCE:
            return "@%s%08X" % (self.getPackage(_data), _data)

        elif _type == TYPE_FLOAT:
            return "%f" % unpack("=f", pack("=L", _data))[0]

        elif _type == TYPE_INT_HEX:
            return "0x%08X" % _data

        elif _type == TYPE_INT_BOOLEAN:
            if _data == 0:
                return "false"
            return "true"

        elif _type == TYPE_DIMENSION:
            return "%f%s" % (self.complexToFloat(_data), DIMENSION_UNITS[_data & COMPLEX_UNIT_MASK])

        elif _type == TYPE_FRACTION:
            return "%f%s" % (self.complexToFloat(_data), FRACTION_UNITS[_data & COMPLEX_UNIT_MASK])

        elif _type >= TYPE_FIRST_COLOR_INT and _type <= TYPE_LAST_COLOR_INT:
            return "#%08X" % _data

        elif _type >= TYPE_FIRST_INT and _type <= TYPE_LAST_INT:
            return "%d" % int(_data)

        return "<0x%X, type 0x%02X>" % (_data, _type)

    def complexToFloat(self, xcomplex):
        return (float)(xcomplex & 0xFFFFFF00) * RADIX_MULTS[(xcomplex >> 4) & 3]

    def getPackage(self, id):
        if id >> 24 == 1:
            return "android:"
        return ""
