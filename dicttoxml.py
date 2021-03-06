#!/usr/bin/env python
# coding: utf-8

"""
Converts a native Python dictionary into an XML string. Supports int, float, str, unicode, list, dict and arbitrary nesting.
"""

from __future__ import unicode_literals

__version__ = '1.3.7'
version = __version__

from random import randint
import collections
import logging
import sys
from xml.dom.minidom import parseString

# python 3 doesn't have a unicode type
try:
    unicode
except:
    unicode = str

def set_debug(debug=True, filename='dicttoxml.log'):
    if debug:
        print('Debug mode is on. Events are logged at: %s' % (filename))
        logging.basicConfig(filename=filename, level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
        print('Debug mode is off.')

ids = [] # initialize list of unique ids

def make_id(element, start=100000, end=999999):
    """Returns a random integer"""
    return '%s_%s' % (element, randint(start, end))

def get_unique_id(element):
    """Returns a unique id for a given element"""
    this_id = make_id(element)
    dup = True
    while dup == True:
        if this_id not in ids:
            dup = False
            ids.append(this_id)
        else:
            this_id = make_id(element)
    return ids[-1]


def xml_escape(s):
    if type(s) in (str, unicode):
        s = s.replace('&',  '&amp;')
        s = s.replace('"',  '&quot;')
        s = s.replace('\'', '&apos;')
        s = s.replace('<',  '&lt;')
        s = s.replace('>',  '&gt;')
    return s

def make_attrstring(attr):
    """Returns an attribute string in the form key="val" """
    attrstring = ' '.join(['%s="%s"' % (k, v) for k, v in attr.items()])
    return '%s%s' % (' ' if attrstring != '' else '', attrstring)

def key_is_valid_xml(key):
    """Checks that a key is a valid XML name"""
    test_xml = '<?xml version="1.0" encoding="UTF-8" ?><%s>foo</%s>' % (key, key)
    try: 
        parseString(test_xml)
        return True
    except Exception: #minidom does not implement exceptions well
        return False

def convert(obj, ids, parent='root',attr_type=True):
    """Routes the elements of an object to the right function to convert them based on their data type"""
    logging.info('Inside convert(). obj type is: %s' % (type(obj).__name__))
    if type(obj) in (int, float, str, unicode):
        return convert_kv('item', obj,attr_type)
    if hasattr(obj, 'isoformat'):
        return convert_kv('item', obj.isoformat(),attr_type)
    if type(obj) == bool:
        return convert_bool('item', obj,attr_type)
    if obj == None:
        return convert_none('item', '',attr_type)
    if isinstance(obj, dict):
        return convert_dict(obj, ids, parent,attr_type)
    if type(obj) in (list, set, tuple) or isinstance(obj, collections.Iterable):
        return convert_list(obj, ids, parent,attr_type)
    raise TypeError('Unsupported data type: %s (%s)' % (obj, type(obj).__name__))
    
def convert_dict(obj, ids, parent,attr_type=True):
    """Converts a dict into an XML string."""
    logging.info('Inside convert_dict(): obj type is: %s' % (type(obj).__name__))
    output = []
    addline = output.append
        
    for k, v in obj.items():
        logging.info('Looping inside convert_dict(): k=%s, type(v)=%s' % (k, type(v).__name__))
        try:
            if k.isdigit():
                k = 'n%s' % (k)
        except:
            if type(k) in (int, float):
                k = 'n%s' % (k)
        this_id = get_unique_id(parent)
        attr = {} if ids == False else {'id': '%s' % (this_id) }
        
        if type(v) in (int, float, str, unicode):
            addline(convert_kv(k, v, attr,attr_type))
        elif hasattr(v, 'isoformat'): # datetime
            addline(convert_kv(k, v.isoformat(), attr,attr_type))
        elif type(v) == bool:
            addline(convert_bool(k, v, attr,attr_type))
        elif isinstance(v, dict):
            if not attr_type:
                addline('<%s %s>%s</%s>' % (
                    k, make_attrstring(attr), convert_dict(v, ids, k,attr_type), k)
                )
            else:
                addline('<%s type="dict"%s>%s</%s>' % (
                    k, make_attrstring(attr), convert_dict(v, ids, k,attr_type), k)
                )
        elif type(v) in (list, set, tuple) or isinstance(v, collections.Iterable):
            if not attr_type:
                addline('<%s %s>%s</%s>' % (
                    k, make_attrstring(attr), convert_list(v, ids, k,attr_type), k)
                )
            else:
                addline('<%s type="list"%s>%s</%s>' % (
                    k, make_attrstring(attr), convert_list(v, ids, k,attr_type), k)
                )
        elif v is None:
            addline(convert_none(k, v, attr,attr_type))
        else:
            raise TypeError('Unsupported data type: %s (%s)' % (obj, type(obj).__name__))
    return ''.join(output)

def convert_list(items, ids, parent,attr_type=True):
    """Converts a list into an XML string."""
    logging.info('Inside convert_list()')
    output = []
    addline = output.append
    this_id = get_unique_id(parent)
    for i, item in enumerate(items):
        logging.info('Looping inside convert_list(): item=%s, type=%s' % (item, type(item).__name__))
        attr = {} if ids == False else {
            'id': '%s_%s' % (this_id, i+1) 
        }
        if type(item) in (int, float, str, unicode):
            addline(convert_kv('item', item, attr,attr_type))
        elif hasattr(item, 'isoformat'): # datetime
            addline(convert_kv('item', item.isoformat(), attr,attr_type))
        elif type(item) == bool:
            addline(convert_bool('item', item, attr,attr_type))
        elif isinstance(item, dict):
            if not attr_type:
                addline('<item>%s</item>' % (convert_dict(item, ids, parent,attr_type)))
            else:
                addline('<item type="dict">%s</item>' % (convert_dict(item, ids, parent,attr_type)))
        elif type(item) in (list, set, tuple) or isinstance(item, collections.Iterable):
            if not attr_type:
                addline('<item %s>%s</item>' % (make_attrstring(attr), convert_list(item, ids, 'item',attr_type)))
            else:
                addline('<item type="list"%s>%s</item>' % (make_attrstring(attr), convert_list(item, ids, 'item',attr_type)))
        elif item == None:
            addline(convert_none('item', None, attr,attr_type))
        else:
            raise TypeError('Unsupported data type: %s (%s)' % (item, type(item).__name__))
    return ''.join(output)

def convert_kv(key, val, attr={},attr_type=True):
    """Converts an int, float or string into an XML element"""
    logging.info('Inside convert_kv(): k=%s, type(v) is: %s' % (key, type(val).__name__))
    key = key.replace(' ', '_') # replace spaces with underscores
    if key_is_valid_xml(key) == False:
        attr['name'] = key
        key = "key"
    attrstring = make_attrstring(attr)
    if not attr_type:
        return '<%s %s>%s</%s>' % (
            key, attrstring, xml_escape(val), key
        )
    else:
        return '<%s type="%s"%s>%s</%s>' % (
            key, type(val).__name__ if type(val).__name__ != 'unicode' else 'str',
            attrstring, xml_escape(val), key
        )



def convert_bool(key, val, attr={},attr_type=True):
    """Converts a boolean into an XML element"""
    logging.info('Inside convert_bool(): key=%s, type(val) is: %s' % (key, type(val).__name__))
    key = key.replace(' ', '_') # replace spaces with underscores
    if key_is_valid_xml(key) == False:
        attr['name'] = key
        key = "key"
    attrstring = make_attrstring(attr)
    if not attr_type:
        return '<%s %s>%s</%s>' % (key, attrstring, unicode(val).lower(), key)
    else:
        return '<%s type="bool"%s>%s</%s>' % (key, attrstring, unicode(val).lower(), key)

def convert_none(key, val, attr={},attr_type=True):
    """Converts a null value into an XML element"""
    logging.info('Inside convert_none(): key=%s' % (key))
    key = key.replace(' ', '_') # replace spaces with underscores
    if key_is_valid_xml(key) == False:
        attr['name'] = key
        key = "key"
    attrstring = make_attrstring(attr)
    if not attr_type:
        return '<%s %s></%s>' % (key, attrstring, key)
    else:
        return '<%s type="null"%s></%s>' % (key, attrstring, key)

def dicttoxml(obj, root=True, ids=False,attr_type=True):
    """Converts a python object into XML
    attr_type is used to specify if data type for each element should be included in the resulting xml.
    By default, it is set to True.
    """
    logging.info('Inside dicttoxml(): type(obj) is: %s' % (type(obj).__name__))
    output = []
    addline = output.append
    if root == True:
        if not attr_type:
            addline('<?xml version="1.0" encoding="UTF-8" ?>')
            addline('<root>%s</root>' % (convert(obj, ids, parent='root',attr_type=False)))
        else:
            addline('<?xml version="1.0" encoding="UTF-8" ?>')
            addline('<root>%s</root>' % (convert(obj, ids, parent='root',attr_type=True)))
    else:
        if not attr_type:
            addline(convert(obj, ids, parent='',attr_type=False))
        else:
            addline(convert(obj, ids, parent='',attr_type=True))
    return ''.join(output)
