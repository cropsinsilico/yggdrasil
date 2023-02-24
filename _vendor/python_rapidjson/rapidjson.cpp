// -*- coding: utf-8 -*-
// :Project:   python-rapidjson -- Python extension module
// :Author:    Ken Robbins <ken@kenrobbins.com>
// :License:   MIT License
// :Copyright: © 2015 Ken Robbins
// :Copyright: © 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022 Lele Gaifax
//

#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif

#include <locale.h>

#include <Python.h>
#include <datetime.h>
#include <structmember.h>

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

#define RAPIDJSON_FORCE_IMPORT_ARRAY
#include "rapidjson/pyrj.h"
#include "rapidjson/reader.h"
#include "rapidjson/schema.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/writer.h"
#include "rapidjson/prettywriter.h"
#include "rapidjson/error/en.h"
#include "units.cpp"
#include "geometry.cpp"


using namespace rapidjson;


/* On some MacOS combo, using Py_IS_XXX() macros does not work (see
   https://github.com/python-rapidjson/python-rapidjson/issues/78).
   OTOH, MSVC < 2015 does not have std::isxxx() (see
   https://stackoverflow.com/questions/38441740/where-is-isnan-in-msvc-2010).
   Oh well... */

#if defined (_MSC_VER) && (_MSC_VER < 1900)
#define IS_NAN(x) Py_IS_NAN(x)
#define IS_INF(x) Py_IS_INFINITY(x)
#else
#define IS_NAN(x) std::isnan(x)
#define IS_INF(x) std::isinf(x)
#endif


static PyObject* units_submodule = NULL;
static PyObject* geom_submodule = NULL;
static PyObject* decimal_type = NULL;
static PyObject* timezone_type = NULL;
static PyObject* timezone_utc = NULL;
static PyObject* uuid_type = NULL;
static PyObject* validation_error = NULL;
static PyObject* validation_warning = NULL;
static PyObject* normalization_error = NULL;
static PyObject* normalization_warning = NULL;
static PyObject* decode_error = NULL;
static PyObject* comparison_error = NULL;
static PyObject* generate_error = NULL;


/* These are the names of often used methods or literal values, interned in the module
   initialization function, to avoid repeated creation/destruction of PyUnicode values
   from plain C strings.

   We cannot use _Py_IDENTIFIER() because that upsets the GNU C++ compiler in -pedantic
   mode. */

static PyObject* astimezone_name = NULL;
static PyObject* hex_name = NULL;
static PyObject* timestamp_name = NULL;
static PyObject* total_seconds_name = NULL;
static PyObject* utcoffset_name = NULL;
static PyObject* is_infinite_name = NULL;
static PyObject* is_nan_name = NULL;
static PyObject* start_object_name = NULL;
static PyObject* end_object_name = NULL;
static PyObject* default_name = NULL;
static PyObject* end_array_name = NULL;
static PyObject* string_name = NULL;
static PyObject* read_name = NULL;
static PyObject* write_name = NULL;
static PyObject* encoding_name = NULL;

static PyObject* minus_inf_string_value = NULL;
static PyObject* nan_string_value = NULL;
static PyObject* plus_inf_string_value = NULL;


enum HandlerContextObjectFlag {
    HandlerContextObjectFlagFalse = 0,
    HandlerContextObjectFlagTrue = 1,
    HandlerContextObjectFlagInstance = 2
};


struct HandlerContext {
    PyObject* object;
    const char* key;
    SizeType keyLength;
    HandlerContextObjectFlag isObject;
    bool keyValuePairs;
    bool copiedKey;
};


enum DatetimeMode {
    DM_NONE = 0,
    // Formats
    DM_ISO8601 = 1<<0,      // Bidirectional ISO8601 for datetimes, dates and times
    DM_UNIX_TIME = 1<<1,    // Serialization only, "Unix epoch"-based number of seconds
    // Options
    DM_ONLY_SECONDS = 1<<4, // Truncate values to the whole second, ignoring micro seconds
    DM_IGNORE_TZ = 1<<5,    // Ignore timezones
    DM_NAIVE_IS_UTC = 1<<6, // Assume naive datetime are in UTC timezone
    DM_SHIFT_TO_UTC = 1<<7, // Shift to/from UTC
    DM_MAX = 1<<8
};


#define DATETIME_MODE_FORMATS_MASK 0x0f // 0b00001111 in C++14


static inline int
datetime_mode_format(unsigned mode) {
    return mode & DATETIME_MODE_FORMATS_MASK;
}


static inline bool
valid_datetime_mode(int mode) {
    int format = datetime_mode_format(mode);
    return (mode >= 0 && mode < DM_MAX
            && (format <= DM_UNIX_TIME)
            && (mode == 0 || format > 0));
}


static int
days_per_month(int year, int month) {
    assert(month >= 1);
    assert(month <= 12);
    if (month == 1 || month == 3 || month == 5 || month == 7
        || month == 8 || month == 10 || month == 12) {
        return 31;
    } else if (month == 4 || month == 6 || month == 9 || month == 11) {
        return 30;
    } else if (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) {
        return 29;
    } else {
        return 28;
    }
}


enum UuidMode {
    UM_NONE = 0,
    UM_CANONICAL = 1<<0, // 4-dashed 32 hex chars: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    UM_HEX = 1<<1,       // canonical OR 32 hex chars in a row
    UM_MAX = 1<<2
};


enum NumberMode {
    NM_NONE = 0,
    NM_NAN = 1<<0,     // allow "not-a-number" values
    NM_DECIMAL = 1<<1, // serialize Decimal instances, deserialize floats as Decimal
    NM_NATIVE = 1<<2,  // use faster native C library number handling
    NM_MAX = 1<<3
};


enum BytesMode {
    BM_NONE = 0,
    BM_UTF8 = 1<<0,             // try to convert to UTF-8
    BM_SCALAR = 1<<1,           // Encode as a yggdrasil scalar
    BM_MAX = 1<<2
};


enum ParseMode {
    PM_NONE = 0,
    PM_COMMENTS = 1<<0,         // Allow one-line // ... and multi-line /* ... */ comments
    PM_TRAILING_COMMAS = 1<<1,  // allow trailing commas at the end of objects and arrays
    PM_MAX = 1<<2
};


enum WriteMode {
    WM_COMPACT = 0,
    WM_PRETTY = 1<<0,            // Use PrettyWriter
    WM_SINGLE_LINE_ARRAY = 1<<1, // Format arrays on a single line
    WM_MAX = 1<<2
};


enum IterableMode {
    IM_ANY_ITERABLE = 0,        // Default, any iterable is dumped as JSON array
    IM_ONLY_LISTS = 1<<0,       // Only list instances are dumped as JSON arrays
    IM_MAX = 1<<1
};


enum MappingMode {
    MM_ANY_MAPPING = 0,                // Default, any mapping is dumped as JSON object
    MM_ONLY_DICTS = 1<<0,              // Only dict instances are dumped as JSON objects
    MM_COERCE_KEYS_TO_STRINGS = 1<<1,  // Convert keys to strings
    MM_SKIP_NON_STRING_KEYS = 1<<2,    // Ignore non-string keys
    MM_SORT_KEYS = 1<<3,               // Sort keys
    MM_MAX = 1<<4
};


enum YggdrasilMode {
    YM_BASE64 = 0,              // Default, yggdrasil extension types are base 64 encoded
    YM_READABLE = 1<<0,         // Encode yggdrasil extension types in a readable format
    YM_PICKLE = 1<<2,           // Pickle unsupported Python objects
    YM_MAX = 1<<3
};

static int SIZE_OF_SIZE_T = sizeof(size_t);


//////////////////////////
// Forward declarations //
//////////////////////////


static PyObject* do_decode(PyObject* decoder,
                           const char* jsonStr, Py_ssize_t jsonStrlen,
                           PyObject* jsonStream, size_t chunkSize,
                           PyObject* objectHook,
                           unsigned numberMode, unsigned datetimeMode,
                           unsigned uuidMode, unsigned parseMode);
static PyObject* decoder_call(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* decoder_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);


static PyObject* do_encode(PyObject* value, PyObject* defaultFn, bool ensureAscii,
                           unsigned writeMode, char indentChar, unsigned indentCount,
                           unsigned numberMode, unsigned datetimeMode,
                           unsigned uuidMode, unsigned bytesMode,
                           unsigned iterableMode, unsigned mappingMode,
			   unsigned yggdrasilMode);
static PyObject* do_stream_encode(PyObject* value, PyObject* stream, size_t chunkSize,
                                  PyObject* defaultFn, bool ensureAscii,
                                  unsigned writeMode, char indentChar,
                                  unsigned indentCount, unsigned numberMode,
                                  unsigned datetimeMode, unsigned uuidMode,
                                  unsigned bytesMode, unsigned iterableMode,
                                  unsigned mappingMode, unsigned yggdrasilMode);
static PyObject* encoder_call(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* encoder_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);


static PyObject* validator_call(PyObject* self, PyObject* args, PyObject* kwargs);
static void validator_dealloc(PyObject* self);
static PyObject* validator_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* validator_validate(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* validator_compare(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* validator_generate_data(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* validator_check_schema(PyObject* cls, PyObject* args, PyObject* kwargs);

static PyObject* normalizer_call(PyObject* self, PyObject* args, PyObject* kwargs);
static void normalizer_dealloc(PyObject* self);
static PyObject* normalizer_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* normalizer_validate(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* normalizer_compare(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* normalizer_generate_data(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* normalizer_check_schema(PyObject* cls, PyObject* args, PyObject* kwargs);
static PyObject* normalizer_normalize(PyObject* self, PyObject* args, PyObject* kwargs);

///////////////////////////////////////////////////
// Stream wrapper around Python file-like object //
///////////////////////////////////////////////////


class PyReadStreamWrapper {
public:
    typedef char Ch;

    PyReadStreamWrapper(PyObject* stream, size_t size)
        : stream(stream) {
        Py_INCREF(stream);
        chunkSize = PyLong_FromUnsignedLong(size);
        buffer = NULL;
        chunk = NULL;
        chunkLen = 0;
        pos = 0;
        offset = 0;
        eof = false;
    }

    ~PyReadStreamWrapper() {
        Py_CLEAR(stream);
        Py_CLEAR(chunkSize);
        Py_CLEAR(chunk);
    }

    Ch Peek() {
        if (!eof && pos == chunkLen) {
            Read();
        }
        return eof ? '\0' : buffer[pos];
    }

    Ch Take() {
        if (!eof && pos == chunkLen) {
            Read();
        }
        return eof ? '\0' : buffer[pos++];
    }

    size_t Tell() const {
        return offset + pos;
    }

    void Flush() {
        assert(false);
    }

    void Put(Ch c) {
        assert(false);
    }

    Ch* PutBegin() {
        assert(false);
        return 0;
    }

    size_t PutEnd(Ch* begin) {
        assert(false);
        return 0;
    }

private:
    void Read() {
        Py_CLEAR(chunk);

        chunk = PyObject_CallMethodObjArgs(stream, read_name, chunkSize, NULL);

        if (chunk == NULL) {
            eof = true;
        } else {
            Py_ssize_t len;

            if (PyBytes_Check(chunk)) {
                len = PyBytes_GET_SIZE(chunk);
                buffer = PyBytes_AS_STRING(chunk);
            } else {
                buffer = PyUnicode_AsUTF8AndSize(chunk, &len);
                if (buffer == NULL) {
                    len = 0;
                }
            }

            if (len == 0) {
                eof = true;
            } else {
                offset += chunkLen;
                chunkLen = len;
                pos = 0;
            }
        }
    }

    PyObject* stream;
    PyObject* chunkSize;
    PyObject* chunk;
    const Ch* buffer;
    size_t chunkLen;
    size_t pos;
    size_t offset;
    bool eof;
};


class PyWriteStreamWrapper {
public:
    typedef char Ch;

    PyWriteStreamWrapper(PyObject* stream, size_t size)
        : stream(stream) {
        Py_INCREF(stream);
        buffer = (char*) PyMem_Malloc(size);
        assert(buffer);
        bufferEnd = buffer + size;
        cursor = buffer;
        multiByteChar = NULL;
        isBinary = !PyObject_HasAttr(stream, encoding_name);
    }

    ~PyWriteStreamWrapper() {
        Py_CLEAR(stream);
        PyMem_Free(buffer);
    }

    Ch Peek() {
        assert(false);
        return 0;
    }

    Ch Take() {
        assert(false);
        return 0;
    }

    size_t Tell() const {
        assert(false);
        return 0;
    }

    void Flush() {
        PyObject* c;
        if (isBinary) {
            c = PyBytes_FromStringAndSize(buffer, (size_t)(cursor - buffer));
            cursor = buffer;
        } else {
            if (multiByteChar == NULL) {
                c = PyUnicode_FromStringAndSize(buffer, (size_t)(cursor - buffer));
                cursor = buffer;
            } else {
                size_t complete = (size_t)(multiByteChar - buffer);
                c = PyUnicode_FromStringAndSize(buffer, complete);
                size_t remaining = (size_t)(cursor - multiByteChar);
                if (RAPIDJSON_LIKELY(remaining < complete))
                    memcpy(buffer, multiByteChar, remaining);
                else
                    std::memmove(buffer, multiByteChar, remaining);
                cursor = buffer + remaining;
                multiByteChar = NULL;
            }
        }
        if (c == NULL) {
            // Propagate the error state, it will be caught by dumps_internal()
        } else {
            PyObject* res = PyObject_CallMethodObjArgs(stream, write_name, c, NULL);
            if (res == NULL) {
                // Likewise
            } else {
                Py_DECREF(res);
            }
            Py_DECREF(c);
        }
    }

    void Put(Ch c) {
        if (cursor == bufferEnd)
            Flush();
        if (!isBinary) {
            if ((c & 0x80) == 0) {
                multiByteChar = NULL;
            } else if (c & 0x40) {
                multiByteChar = cursor;
            }
        }
        *cursor++ = c;
    }

    Ch* PutBegin() {
        assert(false);
        return 0;
    }

    size_t PutEnd(Ch* begin) {
        assert(false);
        return 0;
    }

private:
    PyObject* stream;
    Ch* buffer;
    Ch* bufferEnd;
    Ch* cursor;
    Ch* multiByteChar;
    bool isBinary;
};


inline void PutUnsafe(PyWriteStreamWrapper& stream, char c) {
    stream.Put(c);
}


/////////////
// RawJSON //
/////////////


typedef struct {
    PyObject_HEAD
    PyObject* value;
} RawJSON;


static void
RawJSON_dealloc(RawJSON* self)
{
    Py_XDECREF(self->value);
    Py_TYPE(self)->tp_free((PyObject*) self);
}


static PyObject*
RawJSON_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    PyObject* self = type->tp_alloc(type, 0);
    static char const* kwlist[] = {
        "value",
        NULL
    };
    PyObject* value = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "U", (char**) kwlist, &value))
        return NULL;

    ((RawJSON*) self)->value = value;

    Py_INCREF(value);

    return self;
}

static PyMemberDef RawJSON_members[] = {
    {"value",
     T_OBJECT_EX, offsetof(RawJSON, value), READONLY,
     "string representing a serialized JSON object"},
    {NULL}  /* Sentinel */
};


PyDoc_STRVAR(rawjson_doc,
             "Raw (preserialized) JSON object\n"
             "\n"
             "When rapidjson tries to serialize instances of this class, it will"
             " use their literal `value`. For instance:\n"
             ">>> rapidjson.dumps(RawJSON('{\"already\": \"serialized\"}'))\n"
             "'{\"already\": \"serialized\"}'");


static PyTypeObject RawJSON_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.RawJSON",            /* tp_name */
    sizeof(RawJSON),                /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor) RawJSON_dealloc,   /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    0,                              /* tp_repr */
    0,                              /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    0,                              /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    rawjson_doc,                    /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    0,                              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    0,                              /* tp_methods */
    RawJSON_members,                /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    0,                              /* tp_init */
    0,                              /* tp_alloc */
    RawJSON_new,                    /* tp_new */
};


static bool
accept_indent_arg(PyObject* arg, unsigned &write_mode, unsigned &indent_count,
                   char &indent_char)
{
    if (arg != NULL && arg != Py_None) {
        write_mode = WM_PRETTY;

        if (PyLong_Check(arg) && PyLong_AsLong(arg) >= 0) {
            indent_count = PyLong_AsUnsignedLong(arg);
        } else if (PyUnicode_Check(arg)) {
            Py_ssize_t len;
            const char* indentStr = PyUnicode_AsUTF8AndSize(arg, &len);

            indent_count = len;
            if (indent_count) {
                indent_char = '\0';
                while (len--) {
                    char ch = indentStr[len];

                    if (ch == '\n' || ch == ' ' || ch == '\t' || ch == '\r') {
                        if (indent_char == '\0') {
                            indent_char = ch;
                        } else if (indent_char != ch) {
                            PyErr_SetString(
                                PyExc_TypeError,
                                "indent string cannot contains different chars");
                            return false;
                        }
                    } else {
                        PyErr_SetString(PyExc_TypeError,
                                        "non-whitespace char in indent string");
                        return false;
                    }
                }
            }
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "indent must be a non-negative int or a string");
            return false;
        }
    }
    return true;
}

static bool
accept_write_mode_arg(PyObject* arg, unsigned &write_mode)
{
    if (arg != NULL && arg != Py_None) {
        if (PyLong_Check(arg)) {
            long mode = PyLong_AsLong(arg);
            if (mode < 0 || mode >= WM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid write_mode");
                return false;
            }
            if (mode == WM_COMPACT) {
                write_mode = WM_COMPACT;
            } else if (mode & WM_SINGLE_LINE_ARRAY) {
                write_mode = (unsigned) (write_mode | WM_SINGLE_LINE_ARRAY);
            }
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "write_mode must be a non-negative int");
            return false;
        }
    }
    return true;
}

static bool
accept_number_mode_arg(PyObject* arg, int allow_nan, unsigned &number_mode)
{
    if (arg != NULL) {
        if (arg == Py_None)
            number_mode = NM_NONE;
        else if (PyLong_Check(arg)) {
            long mode = PyLong_AsLong(arg);
            if (mode < 0 || mode >= NM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid number_mode, out of range");
                return false;
            }
            number_mode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "number_mode must be a non-negative int");
            return false;
        }
    }
    if (allow_nan != -1) {
        if (allow_nan)
            number_mode |= NM_NAN;
        else
            number_mode &= ~NM_NAN;
    }
    return true;
}

static bool
accept_datetime_mode_arg(PyObject* arg, unsigned &datetime_mode)
{
    if (arg != NULL && arg != Py_None) {
        if (PyLong_Check(arg)) {
            long mode = PyLong_AsLong(arg);
            if (!valid_datetime_mode(mode)) {
                PyErr_SetString(PyExc_ValueError, "Invalid datetime_mode, out of range");
                return false;
            }
            datetime_mode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "datetime_mode must be a non-negative int");
            return false;
        }
    }
    return true;
}

static bool
accept_uuid_mode_arg(PyObject* arg, unsigned &uuid_mode)
{
    if (arg != NULL && arg != Py_None) {
        if (PyLong_Check(arg)) {
            long mode = PyLong_AsLong(arg);
            if (mode < 0 || mode >= UM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid uuid_mode, out of range");
                return false;
            }
            uuid_mode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError, "uuid_mode must be a non-negative int");
            return false;
        }
    }
    return true;
}

static bool
accept_bytes_mode_arg(PyObject* arg, unsigned &bytes_mode)
{
    if (arg != NULL && arg != Py_None) {
        if (PyLong_Check(arg)) {
            long mode = PyLong_AsLong(arg);
            if (mode < 0 || mode >= BM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid bytes_mode, out of range");
                return false;
            }
            bytes_mode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError, "bytes_mode must be a non-negative int");
            return false;
        }
    }
    return true;
}

static bool
accept_iterable_mode_arg(PyObject* arg, unsigned &iterable_mode)
{
    if (arg != NULL && arg != Py_None) {
        if (PyLong_Check(arg)) {
            long mode = PyLong_AsLong(arg);
            if (mode < 0 || mode >= IM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid iterable_mode, out of range");
                return false;
            }
            iterable_mode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError, "iterable_mode must be a non-negative int");
            return false;
        }
    }
    return true;
}

static bool
accept_mapping_mode_arg(PyObject* arg, unsigned &mapping_mode)
{
    if (arg != NULL && arg != Py_None) {
        if (PyLong_Check(arg)) {
            long mode = PyLong_AsLong(arg);
            if (mode < 0 || mode >= MM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid mapping_mode, out of range");
                return false;
            }
            mapping_mode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError, "mapping_mode must be a non-negative int");
            return false;
        }
    }
    return true;
}

static bool
accept_yggdrasil_mode_arg(PyObject* arg, unsigned &yggdrasil_mode)
{
    if (arg != NULL && arg != Py_None) {
        if (PyLong_Check(arg)) {
            long mode = PyLong_AsLong(arg);
            if (mode < 0 || mode >= YM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid yggdrasil_mode, out of range");
                return false;
            }
            yggdrasil_mode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError, "yggdrasil_mode must be a non-negative int");
            return false;
        }
    }
    return true;
}

static bool
accept_chunk_size_arg(PyObject* arg, size_t &chunk_size)
{
    if (arg != NULL && arg != Py_None) {
        if (PyLong_Check(arg)) {
            Py_ssize_t size = PyNumber_AsSsize_t(arg, PyExc_ValueError);
            if (PyErr_Occurred() || size < 4 || size > UINT_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid chunk_size, out of range");
                return false;
            }
            chunk_size = (size_t) size;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "chunk_size must be a non-negative int");
            return false;
        }
    }
    return true;
}

static bool
accept_parse_mode_arg(PyObject* arg, unsigned &parse_mode)
{
    if (arg != NULL && arg != Py_None) {
        if (PyLong_Check(arg)) {
            long mode = PyLong_AsLong(arg);
            if (mode < 0 || mode >= PM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid parse_mode, out of range");
                return false;
            }
            parse_mode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "parse_mode must be a non-negative int");
            return false;
        }
    }
    return true;
}


////////////////////////////////
// Python/Document Conversion //
////////////////////////////////

static unsigned check_expectsString(Document& d) {
    if (!d.IsObject())
	return 0;
    {
	Value::ConstMemberIterator it = d.FindMember("type");
	if ((it != d.MemberEnd()) && it->value.IsString()) {
	    if (strcmp(it->value.GetString(), "string") == 0)
		return 1;
	}
    }
    {
	Value::ConstMemberIterator it = d.FindMember("subtype");
	if ((it != d.MemberEnd()) && it->value.IsString()) {
	    if ((strcmp(it->value.GetString(), "bytes") == 0) ||
		(strcmp(it->value.GetString(), "string") == 0) ||
		(strcmp(it->value.GetString(), "unicode") == 0))
		return 1;
	}
    }
    return 0;
}


static bool isEmptyStr(const char* jsonStr, size_t len) {
    size_t i = 0;
    while (i < len) {
	switch (jsonStr[i]) {
	case ' ':
	case '\n':
	case '\r':
	case '\v':
	case '\f':
	case '\t': {
	    i++;
	    break;
	}
	default:
	    return false;
	}
    }
    return true;
}

static bool isPaddedStr(const char* str, size_t str_len,
			const char* pattern, size_t pattern_len) {
    if (pattern_len > str_len)
	return false;
    if (strncmp(str, pattern, pattern_len) != 0)
	return false;
    if (!isEmptyStr(str + pattern_len, str_len - pattern_len))
	return false;
    return true;
}

static bool endsWith(const char* jsonStr, size_t len, const char check) {
    size_t i = len - 1;
    while (i >= 0) {
	switch (jsonStr[i]) {
	case ' ':
	case '\n':
	case '\r':
	case '\v':
	case '\f':
	case '\t': {
	    i--;
	    break;
	}
	default:
	    return (jsonStr[i] == check);
	}
    }
    return false;
}

static bool isNumber(const char* jsonStr, size_t len, bool has_digit) {
    size_t i = 0;
    unsigned ndec = 0;
    while (i < len) {
	switch (jsonStr[i]) {
	case '0':
	case '1':
	case '2':
	case '3':
	case '4':
	case '5':
	case '6':
	case '7':
	case '8':
	case '9':
	    has_digit = true;
	    i++;
	    break;
	case '.':
	    if (ndec || !has_digit)
		return false;
	    ndec++;
	    i++;
	    break;
	case 'e':
	case 'E':
	    if (!has_digit)
		return false;
	    i++;
	    if ((i < len) && ((jsonStr[i] == '-') || (jsonStr[i] == '+')))
		i++;
	    ndec = 0;
	    has_digit = false;
	    break;
	case ' ':
	case '\n':
	case '\r':
	case '\v':
	case '\f':
	case '\t':
	    if (!has_digit)
		return false;
	    return isEmptyStr(jsonStr + i + 1, len - (i + 1));
	default:
	    return false;
	}
    }
    return has_digit;
}

static bool isJSONDocument(const char* jsonStr, size_t len,
			   bool* isEmpty = 0,
			   unsigned expectsString = 0) {
    size_t i = 0;
    while (i < len) {
	switch (jsonStr[i]) {
	case ' ':
	case '\n':
	case '\r':
	case '\v':
	case '\f':
	case '\t':
	    i++;
	    break;
	case '"':
	    return endsWith(jsonStr + i + 1, len - (i + 1), '"');
	case '{':
	    return endsWith(jsonStr, len, '}');
	case '[':
	    return endsWith(jsonStr, len, ']');
	case '-':
	case '+':
	    return isNumber(jsonStr + i + 1, len - (i + 1), false);
	case '0':
	case '1':
	case '2':
	case '3':
	case '4':
	case '5':
	case '6':
	case '7':
	case '8':
	case '9':
	    return isNumber(jsonStr + i + 1, len - (i + 1), true);
	case 'f':
	    return isPaddedStr(jsonStr + i, len - i, "false", 5);
	case 't':
	    return isPaddedStr(jsonStr + i, len - i, "true", 4);
	case 'n':
	    return isPaddedStr(jsonStr + i, len - i, "null", 4);
	case 'N':
	    return isPaddedStr(jsonStr + i, len - i, "NaN", 3);
	case 'I':
	    return isPaddedStr(jsonStr + i, len - i, "Infinity", 8);
	default:
	    return false;
	}
    }
    // Empty/whitespace string defaults to assuming an empty JSON document
    if (expectsString)
	return false;
    if (isEmpty)
	*isEmpty = true;
    return true;
}

/////////////
// Decoder //
/////////////


/* Adapted from CPython's Objects/floatobject.c::float_from_string_inner() */

static PyObject*
float_from_string(const char* s, Py_ssize_t len)
{
    double x;
    const char* end;

    /* We don't care about overflow or underflow.  If the platform
     * supports them, infinities and signed zeroes (on underflow) are
     * fine. */
    x = PyOS_string_to_double(s, (char **) &end, NULL);
    if (end != s + len) {
        return NULL;
    } else if (x == -1.0 && PyErr_Occurred()) {
        return NULL;
    } else {
        return PyFloat_FromDouble(x);
    }
}


struct PyHandler {
    typedef char Ch;
    PyObject* decoderStartObject;
    PyObject* decoderEndObject;
    PyObject* decoderEndArray;
    PyObject* decoderString;
    PyObject* sharedKeys;
    PyObject* root;
    PyObject* objectHook;
    unsigned datetimeMode;
    unsigned uuidMode;
    unsigned numberMode;
    std::vector<HandlerContext> stack;

    PyHandler(PyObject* decoder,
              PyObject* hook,
              unsigned dm,
              unsigned um,
              unsigned nm)
        : decoderStartObject(NULL),
          decoderEndObject(NULL),
          decoderEndArray(NULL),
          decoderString(NULL),
          root(NULL),
          objectHook(hook),
          datetimeMode(dm),
          uuidMode(um),
          numberMode(nm)
        {
            stack.reserve(128);
            if (decoder != NULL) {
                assert(!objectHook);
                if (PyObject_HasAttr(decoder, start_object_name)) {
                    decoderStartObject = PyObject_GetAttr(decoder, start_object_name);
                }
                if (PyObject_HasAttr(decoder, end_object_name)) {
                    decoderEndObject = PyObject_GetAttr(decoder, end_object_name);
                }
                if (PyObject_HasAttr(decoder, end_array_name)) {
                    decoderEndArray = PyObject_GetAttr(decoder, end_array_name);
                }
                if (PyObject_HasAttr(decoder, string_name)) {
                    decoderString = PyObject_GetAttr(decoder, string_name);
                }
            }
            sharedKeys = PyDict_New();
        }

    ~PyHandler() {
        while (!stack.empty()) {
            const HandlerContext& ctx = stack.back();
            if (ctx.copiedKey)
                PyMem_Free((void*) ctx.key);
            if (ctx.object != NULL)
                Py_DECREF(ctx.object);
            stack.pop_back();
        }
        Py_CLEAR(decoderStartObject);
        Py_CLEAR(decoderEndObject);
        Py_CLEAR(decoderEndArray);
        Py_CLEAR(decoderString);
        Py_CLEAR(sharedKeys);
    }

    bool Handle(PyObject* value) {
        if (root) {
            const HandlerContext& current = stack.back();

            if (current.isObject) {
                PyObject* key = PyUnicode_FromStringAndSize(current.key,
                                                            current.keyLength);
                if (key == NULL) {
                    Py_DECREF(value);
                    return false;
                }

                PyObject* shared_key = PyDict_SetDefault(sharedKeys, key, key);
                if (shared_key == NULL) {
                    Py_DECREF(key);
                    Py_DECREF(value);
                    return false;
                }
                Py_INCREF(shared_key);
                Py_DECREF(key);
                key = shared_key;

                int rc;
                if (current.keyValuePairs) {
                    PyObject* pair = PyTuple_Pack(2, key, value);

                    Py_DECREF(key);
                    Py_DECREF(value);
                    if (pair == NULL) {
                        return false;
                    }
                    rc = PyList_Append(current.object, pair);
                    Py_DECREF(pair);
                } else {
                    if (PyDict_CheckExact(current.object))
                        // If it's a standard dictionary, this is +20% faster
                        rc = PyDict_SetItem(current.object, key, value);
                    else
                        rc = PyObject_SetItem(current.object, key, value);
                    Py_DECREF(key);
                    Py_DECREF(value);
                }

                if (rc == -1) {
                    return false;
                }
            } else {
                PyList_Append(current.object, value);
                Py_DECREF(value);
            }
        } else {
            root = value;
        }
        return true;
    }

    bool Key(const char* str, SizeType length, bool copy) {
        HandlerContext& current = stack.back();

        // This happens when operating in stream mode and kParseInsituFlag is not set: we
        // must copy the incoming string in the context, and destroy the duplicate when
        // the context gets reused for the next dictionary key

        if (current.key && current.copiedKey) {
            PyMem_Free((void*) current.key);
            current.key = NULL;
        }

        if (copy) {
            char* copied_str = (char*) PyMem_Malloc(length+1);
            if (copied_str == NULL)
                return false;
            memcpy(copied_str, str, length+1);
            str = copied_str;
            assert(!current.key);
        }

        current.key = str;
        current.keyLength = length;
        current.copiedKey = copy;

        return true;
    }

    bool StartObject(bool yggdrasilInstance=false) {
        PyObject* mapping;
        bool key_value_pairs;

        if (decoderStartObject != NULL) {
            mapping = PyObject_CallFunctionObjArgs(decoderStartObject, NULL);
            if (mapping == NULL)
                return false;
            key_value_pairs = PyList_Check(mapping);
            if (!PyMapping_Check(mapping) && !key_value_pairs) {
                Py_DECREF(mapping);
                PyErr_SetString(PyExc_ValueError,
                                "start_object() must return a mapping or a list instance");
                return false;
            }
        } else {
            mapping = PyDict_New();
            if (mapping == NULL) {
                return false;
            }
            key_value_pairs = false;
        }

        if (!Handle(mapping)) {
            return false;
        }

        HandlerContext ctx;
        ctx.isObject = HandlerContextObjectFlagTrue;
	if (yggdrasilInstance)
	    ctx.isObject = HandlerContextObjectFlagInstance;
        ctx.keyValuePairs = key_value_pairs;
        ctx.object = mapping;
        ctx.key = NULL;
        ctx.copiedKey = false;
        Py_INCREF(mapping);

        stack.push_back(ctx);

        return true;
    }

    bool EndObject(SizeType member_count, bool yggdrasilInstance=false) {
        const HandlerContext& ctx = stack.back();

        if (ctx.copiedKey)
            PyMem_Free((void*) ctx.key);

        PyObject* mapping = ctx.object;
	
	bool isInstance = false;
	if (yggdrasilInstance && stack.size() > 0)
	    isInstance = (ctx.isObject == HandlerContextObjectFlagInstance);
        stack.pop_back();

        if (objectHook == NULL && decoderEndObject == NULL &&
	    !(yggdrasilInstance && isInstance)) {
            Py_DECREF(mapping);
            return true;
        }

        PyObject* replacement = NULL;
	if (yggdrasilInstance && isInstance) {
	    // TODO: Replace when schema?
	    replacement = dict2instance(mapping);
	} else if (decoderEndObject != NULL) {
            replacement = PyObject_CallFunctionObjArgs(decoderEndObject, mapping, NULL);
        } else /* if (objectHook != NULL) */ {
            replacement = PyObject_CallFunctionObjArgs(objectHook, mapping, NULL);
        }

        Py_DECREF(mapping);
        if (replacement == NULL)
            return false;

        if (!stack.empty()) {
            HandlerContext& current = stack.back();

            if (current.isObject) {
                PyObject* key = PyUnicode_FromStringAndSize(current.key,
                                                            current.keyLength);
                if (key == NULL) {
                    Py_DECREF(replacement);
                    return false;
                }

                PyObject* shared_key = PyDict_SetDefault(sharedKeys, key, key);
                if (shared_key == NULL) {
                    Py_DECREF(key);
                    Py_DECREF(replacement);
                    return false;
                }
                Py_INCREF(shared_key);
                Py_DECREF(key);
                key = shared_key;

                int rc;
                if (current.keyValuePairs) {
                    PyObject* pair = PyTuple_Pack(2, key, replacement);

                    Py_DECREF(key);
                    Py_DECREF(replacement);
                    if (pair == NULL) {
                        return false;
                    }

                    Py_ssize_t listLen = PyList_GET_SIZE(current.object);

                    rc = PyList_SetItem(current.object, listLen - 1, pair);

                    // NB: PyList_SetItem() steals a reference on the replacement, so it
                    // must not be DECREFed when the operation succeeds

                    if (rc == -1) {
                        Py_DECREF(pair);
                        return false;
                    }
                } else {
                    if (PyDict_CheckExact(current.object))
                        // If it's a standard dictionary, this is +20% faster
                        rc = PyDict_SetItem(current.object, key, replacement);
                    else
                        rc = PyObject_SetItem(current.object, key, replacement);
                    Py_DECREF(key);
                    Py_DECREF(replacement);
                    if (rc == -1) {
                        return false;
                    }
                }
            } else {
                // Change these to PySequence_Size() and PySequence_SetItem(),
                // should we implement Decoder.start_array()
                Py_ssize_t listLen = PyList_GET_SIZE(current.object);
                int rc = PyList_SetItem(current.object, listLen - 1, replacement);

                // NB: PyList_SetItem() steals a reference on the replacement, so it must
                // not be DECREFed when the operation succeeds

                if (rc == -1) {
                    Py_DECREF(replacement);
                    return false;
                }
            }
        } else {
            Py_SETREF(root, replacement);
        }

        return true;
    }

    bool StartArray() {
        PyObject* list = PyList_New(0);
        if (list == NULL) {
            return false;
        }

        if (!Handle(list)) {
            return false;
        }

        HandlerContext ctx;
        ctx.isObject = HandlerContextObjectFlagFalse;
        ctx.object = list;
        ctx.key = NULL;
        ctx.copiedKey = false;
        Py_INCREF(list);

        stack.push_back(ctx);

        return true;
    }

    bool EndArray(SizeType elementCount) {
        const HandlerContext& ctx = stack.back();

        if (ctx.copiedKey)
            PyMem_Free((void*) ctx.key);

        PyObject* sequence = ctx.object;
        stack.pop_back();

        PyObject* replacement = NULL;
        if (decoderEndArray == NULL) {
	    if (IsStructuredArray(sequence)) {
		replacement = GetStructuredArray(sequence);
	    } else {
		Py_DECREF(sequence);
		return true;
	    }
        } else {
	    replacement = PyObject_CallFunctionObjArgs(decoderEndArray, sequence,
						       NULL);
	}
        Py_DECREF(sequence);
        if (replacement == NULL)
            return false;

        if (!stack.empty()) {
            const HandlerContext& current = stack.back();

            if (current.isObject) {
                PyObject* key = PyUnicode_FromStringAndSize(current.key,
                                                            current.keyLength);
                if (key == NULL) {
                    Py_DECREF(replacement);
                    return false;
                }

                int rc;
                if (PyDict_Check(current.object))
                    // If it's a standard dictionary, this is +20% faster
                    rc = PyDict_SetItem(current.object, key, replacement);
                else
                    rc = PyObject_SetItem(current.object, key, replacement);

                Py_DECREF(key);
                Py_DECREF(replacement);

                if (rc == -1) {
                    return false;
                }
            } else {
                // Change these to PySequence_Size() and PySequence_SetItem(),
                // should we implement Decoder.start_array()
                Py_ssize_t listLen = PyList_GET_SIZE(current.object);
                int rc = PyList_SetItem(current.object, listLen - 1, replacement);

                // NB: PyList_SetItem() steals a reference on the replacement, so it must
                // not be DECREFed when the operation succeeds

                if (rc == -1) {
                    Py_DECREF(replacement);
                    return false;
                }
            }
        } else {
            Py_SETREF(root, replacement);
        }

        return true;
    }

    bool NaN() {
        if (!(numberMode & NM_NAN)) {
            PyErr_SetString(PyExc_ValueError,
                            "Out of range float values are not JSON compliant");
            return false;
        }

        PyObject* value;
        if (numberMode & NM_DECIMAL) {
            value = PyObject_CallFunctionObjArgs(decimal_type, nan_string_value, NULL);
        } else {
            value = PyFloat_FromString(nan_string_value);
        }

        if (value == NULL)
            return false;

        return Handle(value);
    }

    bool Infinity(bool minus) {
        if (!(numberMode & NM_NAN)) {
            PyErr_SetString(PyExc_ValueError,
                            "Out of range float values are not JSON compliant");
            return false;
        }

        PyObject* value;
        if (numberMode & NM_DECIMAL) {
            value = PyObject_CallFunctionObjArgs(decimal_type,
                                                 minus
                                                 ? minus_inf_string_value
                                                 : plus_inf_string_value, NULL);
        } else {
            value = PyFloat_FromString(minus
                                       ? minus_inf_string_value
                                       : plus_inf_string_value);
        }

        if (value == NULL)
            return false;

        return Handle(value);
    }

    bool Null() {
        PyObject* value = Py_None;
        Py_INCREF(value);

        return Handle(value);
    }

    bool Bool(bool b) {
        PyObject* value = b ? Py_True : Py_False;
        Py_INCREF(value);

        return Handle(value);
    }

    bool Int(int i) {
        PyObject* value = PyLong_FromLong(i);
        return Handle(value);
    }

    bool Uint(unsigned i) {
        PyObject* value = PyLong_FromUnsignedLong(i);
        return Handle(value);
    }

    bool Int64(int64_t i) {
        PyObject* value = PyLong_FromLongLong(i);
        return Handle(value);
    }

    bool Uint64(uint64_t i) {
        PyObject* value = PyLong_FromUnsignedLongLong(i);
        return Handle(value);
    }

    bool Double(double d) {
        PyObject* value = PyFloat_FromDouble(d);
        return Handle(value);
    }

    bool RawNumber(const char* str, SizeType length, bool copy) {
        PyObject* value;
        bool isFloat = false;

        for (int i = length - 1; i >= 0; --i) {
            // consider it a float if there is at least one non-digit character,
            // it may be either a decimal number or +-infinity or nan
            if (!isdigit(str[i]) && str[i] != '-') {
                isFloat = true;
                break;
            }
        }

        if (isFloat) {

            if (numberMode & NM_DECIMAL) {
                PyObject* pystr = PyUnicode_FromStringAndSize(str, length);
                if (pystr == NULL)
                    return false;
                value = PyObject_CallFunctionObjArgs(decimal_type, pystr, NULL);
                Py_DECREF(pystr);
            } else {
                std::string zstr(str, length);

                value = float_from_string(zstr.c_str(), length);
            }

        } else {
            std::string zstr(str, length);

            value = PyLong_FromString(zstr.c_str(), NULL, 10);
        }

        if (value == NULL) {
            PyErr_SetString(PyExc_ValueError,
                            isFloat
                            ? "Invalid float value"
                            : "Invalid integer value");
            return false;
        } else {
            return Handle(value);
        }
    }

#define digit(idx) (str[idx] - '0')

    bool IsIso8601Date(const char* str, int& year, int& month, int& day) {
        // we've already checked that str is a valid length and that 5 and 8 are '-'
        if (!isdigit(str[0]) || !isdigit(str[1]) || !isdigit(str[2]) || !isdigit(str[3])
            || !isdigit(str[5]) || !isdigit(str[6])
            || !isdigit(str[8]) || !isdigit(str[9])) return false;

        year = digit(0)*1000 + digit(1)*100 + digit(2)*10 + digit(3);
        month = digit(5)*10 + digit(6);
        day = digit(8)*10 + digit(9);

        return year > 0 && month <= 12 && day <= days_per_month(year, month);
    }

    bool IsIso8601Offset(const char* str, int& tzoff) {
        if (!isdigit(str[1]) || !isdigit(str[2]) || str[3] != ':'
            || !isdigit(str[4]) || !isdigit(str[5])) return false;

        int hofs = 0, mofs = 0, tzsign = 1;
        hofs = digit(1)*10 + digit(2);
        mofs = digit(4)*10 + digit(5);

        if (hofs > 23 || mofs > 59) return false;

        if (str[0] == '-') tzsign = -1;
        tzoff = tzsign * (hofs * 3600 + mofs * 60);
        return true;
    }

    bool IsIso8601Time(const char* str, SizeType length,
                       int& hours, int& mins, int& secs, int& usecs, int& tzoff) {
        // we've already checked that str is a minimum valid length, but nothing else
        if (!isdigit(str[0]) || !isdigit(str[1]) || str[2] != ':'
            || !isdigit(str[3]) || !isdigit(str[4]) || str[5] != ':'
            || !isdigit(str[6]) || !isdigit(str[7])) return false;

        hours = digit(0)*10 + digit(1);
        mins = digit(3)*10 + digit(4);
        secs = digit(6)*10 + digit(7);

        if (hours > 23 || mins > 59 || secs > 59) return false;

        if (length == 8 || (length == 9 && str[8] == 'Z')) {
            // just time
            return true;
        }


        if (length == 14 && (str[8] == '-' || str[8] == '+')) {
            return IsIso8601Offset(&str[8], tzoff);
        }

        // at this point we need a . AND at least 1 more digit
        if (length == 9 || str[8] != '.' || !isdigit(str[9])) return false;

        int usecLength;
        if (str[length - 1] == 'Z') {
            usecLength = length - 10;
        } else if (str[length - 3] == ':') {
            if (!IsIso8601Offset(&str[length - 6], tzoff)) return false;
            usecLength = length - 15;
        } else {
            usecLength = length - 9;
        }

        if (usecLength > 9) return false;

        switch (usecLength) {
            case 9: if (!isdigit(str[17])) { return false; }
            case 8: if (!isdigit(str[16])) { return false; }
            case 7: if (!isdigit(str[15])) { return false; }
            case 6: if (!isdigit(str[14])) { return false; } usecs += digit(14);
            case 5: if (!isdigit(str[13])) { return false; } usecs += digit(13)*10;
            case 4: if (!isdigit(str[12])) { return false; } usecs += digit(12)*100;
            case 3: if (!isdigit(str[11])) { return false; } usecs += digit(11)*1000;
            case 2: if (!isdigit(str[10])) { return false; } usecs += digit(10)*10000;
            case 1: if (!isdigit(str[9])) { return false; } usecs += digit(9)*100000;
        }

        return true;
    }

    bool IsIso8601(const char* str, SizeType length,
                   int& year, int& month, int& day,
                   int& hours, int& mins, int &secs, int& usecs, int& tzoff) {
        year = -1;
        month = day = hours = mins = secs = usecs = tzoff = 0;

        // Early exit for values that are clearly not valid (too short or too long)
        if (length < 8 || length > 35) return false;

        bool isDate = str[4] == '-' && str[7] == '-';

        if (!isDate) {
            return IsIso8601Time(str, length, hours, mins, secs, usecs, tzoff);
        }

        if (length == 10) {
            // if it looks like just a date, validate just the date
            return IsIso8601Date(str, year, month, day);
        }
        if (length > 18 && (str[10] == 'T' || str[10] == ' ')) {
            // if it looks like a date + time, validate date + time
            return IsIso8601Date(str, year, month, day)
                && IsIso8601Time(&str[11], length - 11, hours, mins, secs, usecs, tzoff);
        }
        // can't be valid
        return false;
    }

    bool HandleIso8601(const char* str, SizeType length,
                       int year, int month, int day,
                       int hours, int mins, int secs, int usecs, int tzoff) {
        // we treat year 0 as invalid and thus the default when there is no date
        bool hasDate = year > 0;

        if (length == 10 && hasDate) {
            // just a date, handle quickly
            return Handle(PyDate_FromDate(year, month, day));
        }

        bool isZ = str[length - 1] == 'Z';
        bool hasOffset = !isZ && (str[length - 6] == '-' || str[length - 6] == '+');

        PyObject* value;

        if ((datetimeMode & DM_NAIVE_IS_UTC || isZ) && !hasOffset) {
            if (hasDate) {
                value = PyDateTimeAPI->DateTime_FromDateAndTime(
                    year, month, day, hours, mins, secs, usecs, timezone_utc,
                    PyDateTimeAPI->DateTimeType);
            } else {
                value = PyDateTimeAPI->Time_FromTime(
                    hours, mins, secs, usecs, timezone_utc, PyDateTimeAPI->TimeType);
            }
        } else if (datetimeMode & DM_IGNORE_TZ || (!hasOffset && !isZ)) {
            if (hasDate) {
                value = PyDateTime_FromDateAndTime(year, month, day,
                                                   hours, mins, secs, usecs);
            } else {
                value = PyTime_FromTime(hours, mins, secs, usecs);
            }
        } else if (!hasDate && datetimeMode & DM_SHIFT_TO_UTC && tzoff) {
            PyErr_Format(PyExc_ValueError,
                         "Time literal cannot be shifted to UTC: %s", str);
            value = NULL;
        } else if (!hasDate && datetimeMode & DM_SHIFT_TO_UTC) {
            value = PyDateTimeAPI->Time_FromTime(
                hours, mins, secs, usecs, timezone_utc, PyDateTimeAPI->TimeType);
        } else {
            PyObject* offset = PyDateTimeAPI->Delta_FromDelta(0, tzoff, 0, 1,
                                                              PyDateTimeAPI->DeltaType);
            if (offset == NULL) {
                value = NULL;
            } else {
                PyObject* tz = PyObject_CallFunctionObjArgs(timezone_type, offset, NULL);
                Py_DECREF(offset);
                if (tz == NULL) {
                    value = NULL;
                } else {
                    if (hasDate) {
                        value = PyDateTimeAPI->DateTime_FromDateAndTime(
                            year, month, day, hours, mins, secs, usecs, tz,
                            PyDateTimeAPI->DateTimeType);
                        if (value != NULL && datetimeMode & DM_SHIFT_TO_UTC) {
                            PyObject* asUTC = PyObject_CallMethodObjArgs(
                                value, astimezone_name, timezone_utc, NULL);
                            Py_DECREF(value);
                            if (asUTC == NULL) {
                                value = NULL;
                            } else {
                                value = asUTC;
                            }
                        }
                    } else {
                        value = PyDateTimeAPI->Time_FromTime(hours, mins, secs, usecs, tz,
                                                             PyDateTimeAPI->TimeType);
                    }
                    Py_DECREF(tz);
                }
            }
        }

        if (value == NULL)
            return false;

        return Handle(value);
    }

#undef digit

    bool IsUuid(const char* str, SizeType length) {
        if (uuidMode == UM_HEX && length == 32) {
            for (int i = length - 1; i >= 0; --i)
                if (!isxdigit(str[i]))
                    return false;
            return true;
        } else if (length == 36
                   && str[8] == '-' && str[13] == '-'
                   && str[18] == '-' && str[23] == '-') {
            for (int i = length - 1; i >= 0; --i)
                if (i != 8 && i != 13 && i != 18 && i != 23 && !isxdigit(str[i]))
                    return false;
            return true;
        }
        return false;
    }

    bool HandleUuid(const char* str, SizeType length) {
        PyObject* pystr = PyUnicode_FromStringAndSize(str, length);
        if (pystr == NULL)
            return false;

        PyObject* value = PyObject_CallFunctionObjArgs(uuid_type, pystr, NULL);
        Py_DECREF(pystr);

        if (value == NULL)
            return false;
        else
            return Handle(value);
    }

    bool String(const char* str, SizeType length, bool copy) {
	if (isYggdrasilString(str, length, copy)) {
	    Document x;
	    if (!x.FromYggdrasilString(str, length, copy))
		return false;
	    x.FinalizeFromStack();
	    return x.Accept(*this);
	}
        PyObject* value;

        if (datetimeMode != DM_NONE) {
            int year, month, day, hours, mins, secs, usecs, tzoff;

            if (IsIso8601(str, length, year, month, day,
                          hours, mins, secs, usecs, tzoff))
                return HandleIso8601(str, length, year, month, day,
                                     hours, mins, secs, usecs, tzoff);
        }

        if (uuidMode != UM_NONE && IsUuid(str, length))
            return HandleUuid(str, length);

        value = PyUnicode_FromStringAndSize(str, length);
        if (value == NULL)
            return false;

        if (decoderString != NULL) {
            PyObject* replacement = PyObject_CallFunctionObjArgs(decoderString, value,
                                                                 NULL);
            Py_DECREF(value);
            if (replacement == NULL)
                return false;
            value = replacement;
        }

        return Handle(value);
    }

    template <typename YggSchemaValueType>
    bool YggdrasilString(const char* str, SizeType length, bool copy, YggSchemaValueType& schema) {
	PyObject* value = NULL;
	RAPIDJSON_DEFAULT_ALLOCATOR allocator;
	Value* x = new Value(str, length, allocator, schema);
	if (x->HasUnits()) {
	    PyObject* type = NULL;
	    if (x->IsScalar()) {
		type = (PyObject*)&Quantity_Type;
	    } else {
		type = (PyObject*)&QuantityArray_Type;
	    }
	    RAPIDJSON_DEFAULT_ALLOCATOR allocator;
	    PyObject* arr = x->GetPythonObjectRaw();
	    PyObject* units = PyUnicode_FromStringAndSize(x->GetUnits().GetString(),
							  x->GetUnits().GetStringLength());
	    if (arr != NULL && units != NULL) {
		PyObject* args = PyTuple_Pack(2, arr, units);
		if (args != NULL) {
		    value = PyObject_Call(type, args, NULL);
		    Py_DECREF(args);
		}
	    }
	    Py_XDECREF(arr);
	    Py_XDECREF(units);
	} else if (x->IsPly()) {
	    PlyObject* v = (PlyObject*) Ply_Type.tp_alloc(&Ply_Type, 0);
	    value = (PyObject*)v;
	    v->ply = new Ply();
	    x->GetPly(*v->ply);
	} else if (x->IsObjWavefront()) {
	    ObjWavefrontObject* v = (ObjWavefrontObject*) ObjWavefront_Type.tp_alloc(&ObjWavefront_Type, 0);
	    value = (PyObject*)v;
	    v->obj = new ObjWavefront();
	    x->GetObjWavefront(*v->obj);
	} else {
	    value = x->GetPythonObjectRaw();
	}
	delete x;
	if (value)
	    return Handle(value);
	return false;
    }

    template <typename YggSchemaValueType>
    bool YggdrasilStartObject(YggSchemaValueType& schema) {
	if (!schema.IsObject())
	    return false;
	typename YggSchemaValueType::ConstMemberIterator vs = schema.FindMember(YggSchemaValueType::GetTypeString());
	if ((vs != schema.MemberEnd()) &&
	    ((vs->value == YggSchemaValueType::GetPythonInstanceString()) ||
	     (vs->value == YggSchemaValueType::GetSchemaString())))
	    return StartObject((vs->value == YggSchemaValueType::GetPythonInstanceString()));
	return false;
    }

    PyObject* dict2instance(PyObject* x) {
	PyObject* cls_name = NULL;
	PyObject* args = NULL;
	PyObject* kwargs = NULL;
	PyObject* class_key = PyUnicode_FromString("class");
	PyObject* args_key = PyUnicode_FromString("args");
	PyObject* kwargs_key = PyUnicode_FromString("kwargs");
	if (PyDict_CheckExact(x)) {
	    cls_name = PyDict_GetItem(x, class_key);
	    args = PyDict_GetItem(x, args_key);
	    kwargs = PyDict_GetItem(x, kwargs_key);
	    Py_XINCREF(cls_name);
	    Py_XINCREF(args);
	    Py_XINCREF(kwargs);
	} else {
	    cls_name = PyObject_GetItem(x, class_key);
	    args = PyObject_GetItem(x, args_key);
	    kwargs = PyObject_GetItem(x, kwargs_key);
	}
	Py_DECREF(class_key);
	Py_DECREF(args_key);
	Py_DECREF(kwargs_key);
	if (cls_name == NULL) {
	    Py_XDECREF(args);
	    Py_XDECREF(kwargs);
	    return NULL;
	}
	if (args == NULL)
	    args = PyTuple_New(0);
	else {
	    PyObject* args_list = args;
	    args = PyList_AsTuple(args_list);
	    Py_DECREF(args_list);
	}
	if (args == NULL) {
	    Py_DECREF(cls_name);
	    Py_XDECREF(kwargs);
	    return NULL;
	}
	if (kwargs == NULL)
	    kwargs = PyDict_New();
	if (kwargs == NULL) {
	    Py_DECREF(cls_name);
	    Py_DECREF(args);
	    return NULL;
	}
	PyObject* cls = import_python_object(PyUnicode_AsUTF8(cls_name),
					     "dict2instance: ", true);
	Py_DECREF(cls_name);
	if (cls == NULL) {
	    Py_DECREF(args);
	    Py_DECREF(kwargs);
	    return NULL;
	}
	PyObject* inst = PyObject_Call(cls, args, kwargs);
	Py_DECREF(cls);
	Py_DECREF(args);
	Py_DECREF(kwargs);
	return inst;
    }

    bool YggdrasilEndObject(SizeType memberCount) {
	return EndObject(memberCount, true);
    }
};


typedef struct {
    PyObject_HEAD
    unsigned datetimeMode;
    unsigned uuidMode;
    unsigned numberMode;
    unsigned parseMode;
} DecoderObject;


PyDoc_STRVAR(loads_docstring,
             "loads(string, *, object_hook=None, number_mode=None, datetime_mode=None,"
             " uuid_mode=None, parse_mode=None, allow_nan=True)\n"
             "\n"
             "Decode a JSON string into a Python object.");


static PyObject*
loads(PyObject* self, PyObject* args, PyObject* kwargs)
{
    /* Converts a JSON encoded string to a Python object. */

    static char const* kwlist[] = {
        "string",
        "object_hook",
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "parse_mode",

        /* compatibility with stdlib json */
        "allow_nan",

        NULL
    };
    PyObject* jsonObject;
    PyObject* objectHook = NULL;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* parseModeObj = NULL;
    unsigned parseMode = PM_NONE;
    int allowNan = -1;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$OOOOOp:rapidjson.loads",
                                     (char**) kwlist,
                                     &jsonObject,
                                     &objectHook,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
                                     &parseModeObj,
                                     &allowNan))
        return NULL;

    if (objectHook && !PyCallable_Check(objectHook)) {
        if (objectHook == Py_None) {
            objectHook = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "object_hook is not callable");
            return NULL;
        }
    }

    if (!accept_number_mode_arg(numberModeObj, allowNan, numberMode))
        return NULL;
    if (numberMode & NM_DECIMAL && numberMode & NM_NATIVE) {
        PyErr_SetString(PyExc_ValueError,
                        "Invalid number_mode, combining NM_NATIVE with NM_DECIMAL"
                        " is not supported");
        return NULL;
    }

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;
    if (datetimeMode && datetime_mode_format(datetimeMode) != DM_ISO8601) {
        PyErr_SetString(PyExc_ValueError,
                        "Invalid datetime_mode, can deserialize only from"
                        " ISO8601");
        return NULL;
    }

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    if (!accept_parse_mode_arg(parseModeObj, parseMode))
        return NULL;

    Py_ssize_t jsonStrLen;
    const char* jsonStr;
    PyObject* asUnicode = NULL;

    if (PyUnicode_Check(jsonObject)) {
        jsonStr = PyUnicode_AsUTF8AndSize(jsonObject, &jsonStrLen);
        if (jsonStr == NULL) {
            return NULL;
        }
    } else if (PyBytes_Check(jsonObject) || PyByteArray_Check(jsonObject)) {
        asUnicode = PyUnicode_FromEncodedObject(jsonObject, "utf-8", NULL);
        if (asUnicode == NULL)
            return NULL;
        jsonStr = PyUnicode_AsUTF8AndSize(asUnicode, &jsonStrLen);
        if (jsonStr == NULL) {
            Py_DECREF(asUnicode);
            return NULL;
        }
    } else {
        PyErr_SetString(PyExc_TypeError,
                        "Expected string or UTF-8 encoded bytes or bytearray");
        return NULL;
    }

    PyObject* result = do_decode(NULL, jsonStr, jsonStrLen, NULL, 0, objectHook,
                                 numberMode, datetimeMode, uuidMode, parseMode);

    if (asUnicode != NULL)
        Py_DECREF(asUnicode);

    return result;
}


PyDoc_STRVAR(load_docstring,
             "load(stream, *, object_hook=None, number_mode=None, datetime_mode=None,"
             " uuid_mode=None, parse_mode=None, chunk_size=65536, allow_nan=True)\n"
             "\n"
             "Decode a JSON stream into a Python object.");


static PyObject*
load(PyObject* self, PyObject* args, PyObject* kwargs)
{
    /* Converts a JSON encoded stream to a Python object. */

    static char const* kwlist[] = {
        "stream",
        "object_hook",
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "parse_mode",
        "chunk_size",

        /* compatibility with stdlib json */
        "allow_nan",

        NULL
    };
    PyObject* jsonObject;
    PyObject* objectHook = NULL;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* parseModeObj = NULL;
    unsigned parseMode = PM_NONE;
    PyObject* chunkSizeObj = NULL;
    size_t chunkSize = 65536;
    int allowNan = -1;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$OOOOOOp:rapidjson.load",
                                     (char**) kwlist,
                                     &jsonObject,
                                     &objectHook,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
                                     &parseModeObj,
                                     &chunkSizeObj,
                                     &allowNan))
        return NULL;

    if (!PyObject_HasAttr(jsonObject, read_name)) {
        PyErr_SetString(PyExc_TypeError, "Expected file-like object");
        return NULL;
    }

    if (objectHook && !PyCallable_Check(objectHook)) {
        if (objectHook == Py_None) {
            objectHook = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "object_hook is not callable");
            return NULL;
        }
    }

    if (numberModeObj) {
        if (numberModeObj == Py_None) {
            numberMode = NM_NONE;
        } else if (PyLong_Check(numberModeObj)) {
            int mode = PyLong_AsLong(numberModeObj);
            if (mode < 0 || mode >= NM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid number_mode");
                return NULL;
            }
            numberMode = (unsigned) mode;
            if (numberMode & NM_DECIMAL && numberMode & NM_NATIVE) {
                PyErr_SetString(PyExc_ValueError,
                                "Combining NM_NATIVE with NM_DECIMAL is not supported");
                return NULL;
            }
        }
    }
    if (allowNan != -1) {
        if (allowNan)
            numberMode |= NM_NAN;
        else
            numberMode &= ~NM_NAN;
    }

    if (datetimeModeObj) {
        if (datetimeModeObj == Py_None) {
            datetimeMode = DM_NONE;
        } else if (PyLong_Check(datetimeModeObj)) {
            int mode = PyLong_AsLong(datetimeModeObj);
            if (!valid_datetime_mode(mode)) {
                PyErr_SetString(PyExc_ValueError, "Invalid datetime_mode");
                return NULL;
            }
            datetimeMode = (unsigned) mode;
            if (datetimeMode && datetime_mode_format(datetimeMode) != DM_ISO8601) {
                PyErr_SetString(PyExc_ValueError,
                                "Invalid datetime_mode, can deserialize only from"
                                " ISO8601");
                return NULL;
            }
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "datetime_mode must be a non-negative integer value or None");
            return NULL;
        }
    }

    if (uuidModeObj) {
        if (uuidModeObj == Py_None) {
            uuidMode = UM_NONE;
        } else if (PyLong_Check(uuidModeObj)) {
            int mode = PyLong_AsLong(uuidModeObj);
            if (mode < 0 || mode >= UM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid uuid_mode");
                return NULL;
            }
            uuidMode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "uuid_mode must be an integer value or None");
            return NULL;
        }
    }

    if (parseModeObj) {
        if (parseModeObj == Py_None) {
            parseMode = PM_NONE;
        } else if (PyLong_Check(parseModeObj)) {
            int mode = PyLong_AsLong(parseModeObj);
            if (mode < 0 || mode >= PM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid parse_mode");
                return NULL;
            }
            parseMode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "parse_mode must be an integer value or None");
            return NULL;
        }
    }

    if (chunkSizeObj && chunkSizeObj != Py_None) {
        if (PyLong_Check(chunkSizeObj)) {
            Py_ssize_t size = PyNumber_AsSsize_t(chunkSizeObj, PyExc_ValueError);
            if (PyErr_Occurred() || size < 4 || size > UINT_MAX) {
                PyErr_SetString(PyExc_ValueError,
                                "Invalid chunk_size, must be an integer between 4 and"
                                " UINT_MAX");
                return NULL;
            }
            chunkSize = (size_t) size;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "chunk_size must be an unsigned integer value or None");
            return NULL;
        }
    }

    return do_decode(NULL, NULL, 0, jsonObject, chunkSize, objectHook,
                     numberMode, datetimeMode, uuidMode, parseMode);
}


PyDoc_STRVAR(decoder_doc,
             "Decoder(number_mode=None, datetime_mode=None, uuid_mode=None,"
             " parse_mode=None)\n"
             "\n"
             "Create and return a new Decoder instance.");


static PyMemberDef decoder_members[] = {
    {"datetime_mode",
     T_UINT, offsetof(DecoderObject, datetimeMode), READONLY,
     "The datetime mode, whether and how datetime literals will be recognized."},
    {"uuid_mode",
     T_UINT, offsetof(DecoderObject, uuidMode), READONLY,
     "The UUID mode, whether and how UUID literals will be recognized."},
    {"number_mode",
     T_UINT, offsetof(DecoderObject, numberMode), READONLY,
     "The number mode, whether numeric literals will be decoded."},
    {"parse_mode",
     T_UINT, offsetof(DecoderObject, parseMode), READONLY,
     "The parse mode, whether comments and trailing commas are allowed."},
    {NULL}
};


static PyTypeObject Decoder_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.Decoder",                      /* tp_name */
    sizeof(DecoderObject),                    /* tp_basicsize */
    0,                                        /* tp_itemsize */
    0,                                        /* tp_dealloc */
    0,                                        /* tp_print */
    0,                                        /* tp_getattr */
    0,                                        /* tp_setattr */
    0,                                        /* tp_compare */
    0,                                        /* tp_repr */
    0,                                        /* tp_as_number */
    0,                                        /* tp_as_sequence */
    0,                                        /* tp_as_mapping */
    0,                                        /* tp_hash */
    (ternaryfunc) decoder_call,               /* tp_call */
    0,                                        /* tp_str */
    0,                                        /* tp_getattro */
    0,                                        /* tp_setattro */
    0,                                        /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
    decoder_doc,                              /* tp_doc */
    0,                                        /* tp_traverse */
    0,                                        /* tp_clear */
    0,                                        /* tp_richcompare */
    0,                                        /* tp_weaklistoffset */
    0,                                        /* tp_iter */
    0,                                        /* tp_iternext */
    0,                                        /* tp_methods */
    decoder_members,                          /* tp_members */
    0,                                        /* tp_getset */
    0,                                        /* tp_base */
    0,                                        /* tp_dict */
    0,                                        /* tp_descr_get */
    0,                                        /* tp_descr_set */
    0,                                        /* tp_dictoffset */
    0,                                        /* tp_init */
    0,                                        /* tp_alloc */
    decoder_new,                              /* tp_new */
    PyObject_Del,                             /* tp_free */
};


#define Decoder_CheckExact(v) (Py_TYPE(v) == &Decoder_Type)
#define Decoder_Check(v) PyObject_TypeCheck(v, &Decoder_Type)


#define DECODE(r, f, s, h)                                              \
    do {                                                                \
        /* FIXME: isn't there a cleverer way to write the following?    \
                                                                        \
           Ideally, one would do something like:                        \
                                                                        \
               unsigned flags = kParseInsituFlag;                       \
                                                                        \
               if (! (numberMode & NM_NATIVE))                          \
                   flags |= kParseNumbersAsStringsFlag;                 \
               if (numberMode & NM_NAN)                                 \
                   flags |= kParseNanAndInfFlag;                        \
               if (parseMode & PM_COMMENTS)                             \
                   flags |= kParseCommentsFlag;                         \
               if (parseMode & PM_TRAILING_COMMAS)                      \
                   flags |= kParseTrailingCommasFlag;                   \
                                                                        \
               reader.Parse<flags>(ss, handler);                        \
                                                                        \
           but C++ does not allow that...                               \
        */                                                              \
                                                                        \
        if (numberMode & NM_NAN) {                                      \
            if (numberMode & NM_NATIVE) {                               \
                if (parseMode & PM_TRAILING_COMMAS) {                   \
                    if (parseMode & PM_COMMENTS) {                      \
                        r.Parse<f |                                     \
                                kParseNanAndInfFlag |                   \
                                kParseCommentsFlag |                    \
                                kParseTrailingCommasFlag>(s, h);        \
                    } else {                                            \
                        r.Parse<f |                                     \
                                kParseNanAndInfFlag |                   \
                                kParseTrailingCommasFlag>(s, h);        \
                    }                                                   \
                } else if (parseMode & PM_COMMENTS) {                   \
                    r.Parse<f |                                         \
                            kParseNanAndInfFlag |                       \
                            kParseCommentsFlag>(s, h);                  \
                } else {                                                \
                    r.Parse<f |                                         \
                            kParseNanAndInfFlag>(s, h);                 \
                }                                                       \
            } else if (parseMode & PM_TRAILING_COMMAS) {                \
                if (parseMode & PM_COMMENTS) {                          \
                    r.Parse<f |                                         \
                            kParseNumbersAsStringsFlag |                \
                            kParseNanAndInfFlag |                       \
                            kParseCommentsFlag |                        \
                            kParseTrailingCommasFlag>(s, h);            \
                } else {                                                \
                    r.Parse<f |                                         \
                            kParseNumbersAsStringsFlag |                \
                            kParseNanAndInfFlag |                       \
                            kParseTrailingCommasFlag>(s, h);            \
                }                                                       \
            } else if (parseMode & PM_COMMENTS) {                       \
                r.Parse<f |                                             \
                        kParseNumbersAsStringsFlag |                    \
                        kParseNanAndInfFlag |                           \
                        kParseCommentsFlag>(s, h);                      \
            } else {                                                    \
                r.Parse<f |                                             \
                        kParseNumbersAsStringsFlag |                    \
                        kParseNanAndInfFlag>(s, h);                     \
            }                                                           \
        } else if (numberMode & NM_NATIVE) {                            \
            if (parseMode & PM_TRAILING_COMMAS) {                       \
                if (parseMode & PM_COMMENTS) {                          \
                    r.Parse<f |                                         \
                            kParseCommentsFlag |                        \
                            kParseTrailingCommasFlag>(s, h);            \
                } else {                                                \
                    r.Parse<f |                                         \
                            kParseTrailingCommasFlag>(s, h);            \
                }                                                       \
            } else if (parseMode & PM_COMMENTS) {                       \
                r.Parse<f |                                             \
                        kParseCommentsFlag>(s, h);                      \
            } else {                                                    \
                r.Parse<f>(s, h);                                       \
            }                                                           \
        } else if (parseMode & PM_TRAILING_COMMAS) {                    \
            if (parseMode & PM_COMMENTS) {                              \
                r.Parse<f |                                             \
                        kParseCommentsFlag |                            \
                        kParseNumbersAsStringsFlag>(s, h);              \
            } else {                                                    \
                r.Parse<f |                                             \
                        kParseNumbersAsStringsFlag |                    \
                        kParseTrailingCommasFlag>(s, h);                \
            }                                                           \
        } else {                                                        \
            r.Parse<f | kParseNumbersAsStringsFlag>(s, h);              \
        }                                                               \
    } while(0)


static PyObject*
do_decode(PyObject* decoder, const char* jsonStr, Py_ssize_t jsonStrLen,
          PyObject* jsonStream, size_t chunkSize, PyObject* objectHook,
          unsigned numberMode, unsigned datetimeMode, unsigned uuidMode,
          unsigned parseMode)
{
    PyHandler handler(decoder, objectHook, datetimeMode, uuidMode, numberMode);
    Reader reader;

    if (jsonStr != NULL) {
        char* jsonStrCopy = (char*) PyMem_Malloc(sizeof(char) * (jsonStrLen+1));

        if (jsonStrCopy == NULL)
            return PyErr_NoMemory();

        memcpy(jsonStrCopy, jsonStr, jsonStrLen+1);

        InsituStringStream ss(jsonStrCopy);

        DECODE(reader, kParseInsituFlag, ss, handler);

        PyMem_Free(jsonStrCopy);
    } else {
        PyReadStreamWrapper sw(jsonStream, chunkSize);

        DECODE(reader, kParseNoFlags, sw, handler);
    }

    if (reader.HasParseError()) {
        size_t offset = reader.GetErrorOffset();

        if (PyErr_Occurred()) {
            PyObject* etype;
            PyObject* evalue;
            PyObject* etraceback;
            PyErr_Fetch(&etype, &evalue, &etraceback);

            // Try to add the offset in the error message if the exception
            // value is a string.  Otherwise, use the original exception since
            // we can't be sure the exception type takes a single string.
            if (evalue != NULL && PyUnicode_Check(evalue)) {
                PyErr_Format(etype, "Python parse error at offset %zu: %S", offset, evalue);
                Py_DECREF(etype);
                Py_DECREF(evalue);
                Py_XDECREF(etraceback);
            }
            else
                PyErr_Restore(etype, evalue, etraceback);
        }
        else
            PyErr_Format(decode_error, "Parse error at offset %zu: %s",
                         offset, GetParseError_En(reader.GetParseErrorCode()));

        Py_XDECREF(handler.root);
        return NULL;
    } else if (PyErr_Occurred()) {
        // Catch possible error raised in associated stream operations
        Py_XDECREF(handler.root);
        return NULL;
    }

    return handler.root;
}


static PyObject*
decoder_call(PyObject* self, PyObject* args, PyObject* kwargs)
{
    static char const* kwlist[] = {
        "json",
        "chunk_size",
        NULL
    };
    PyObject* jsonObject;
    PyObject* chunkSizeObj = NULL;
    size_t chunkSize = 65536;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$O",
                                     (char**) kwlist,
                                     &jsonObject,
                                     &chunkSizeObj))
        return NULL;

    if (chunkSizeObj && chunkSizeObj != Py_None) {
        if (PyLong_Check(chunkSizeObj)) {
            Py_ssize_t size = PyNumber_AsSsize_t(chunkSizeObj, PyExc_ValueError);
            if (PyErr_Occurred() || size < 4 || size > UINT_MAX) {
                PyErr_SetString(PyExc_ValueError,
                                "Invalid chunk_size, must be an integer between 4 and"
                                " UINT_MAX");
                return NULL;
            }
            chunkSize = (size_t) size;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "chunk_size must be an unsigned integer value or None");
            return NULL;
        }
    }

    Py_ssize_t jsonStrLen;
    const char* jsonStr;
    PyObject* asUnicode = NULL;

    if (PyUnicode_Check(jsonObject)) {
        jsonStr = PyUnicode_AsUTF8AndSize(jsonObject, &jsonStrLen);
        if (jsonStr == NULL)
            return NULL;
    } else if (PyBytes_Check(jsonObject) || PyByteArray_Check(jsonObject)) {
        asUnicode = PyUnicode_FromEncodedObject(jsonObject, "utf-8", NULL);
        if (asUnicode == NULL)
            return NULL;
        jsonStr = PyUnicode_AsUTF8AndSize(asUnicode, &jsonStrLen);
        if (jsonStr == NULL) {
            Py_DECREF(asUnicode);
            return NULL;
        }
    } else if (PyObject_HasAttr(jsonObject, read_name)) {
        jsonStr = NULL;
        jsonStrLen = 0;
    } else {
        PyErr_SetString(PyExc_TypeError,
                        "Expected string or UTF-8 encoded bytes or bytearray");
        return NULL;
    }

    DecoderObject* d = (DecoderObject*) self;

    PyObject* result = do_decode(self, jsonStr, jsonStrLen, jsonObject, chunkSize, NULL,
                                 d->numberMode, d->datetimeMode, d->uuidMode,
                                 d->parseMode);

    if (asUnicode != NULL)
        Py_DECREF(asUnicode);

    return result;
}


static PyObject*
decoder_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    DecoderObject* d;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* parseModeObj = NULL;
    unsigned parseMode = PM_NONE;
    static char const* kwlist[] = {
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "parse_mode",
        NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|OOOO:Decoder",
                                     (char**) kwlist,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
                                     &parseModeObj))
        return NULL;

    if (numberModeObj) {
        if (numberModeObj == Py_None) {
            numberMode = NM_NONE;
        } else if (PyLong_Check(numberModeObj)) {
            int mode = PyLong_AsLong(numberModeObj);
            if (mode < 0 || mode >= NM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid number_mode");
                return NULL;
            }
            numberMode = (unsigned) mode;
            if (numberMode & NM_DECIMAL && numberMode & NM_NATIVE) {
                PyErr_SetString(PyExc_ValueError,
                                "Combining NM_NATIVE with NM_DECIMAL is not supported");
                return NULL;
            }
        }
    }

    if (datetimeModeObj) {
        if (datetimeModeObj == Py_None) {
            datetimeMode = DM_NONE;
        } else if (PyLong_Check(datetimeModeObj)) {
            int mode = PyLong_AsLong(datetimeModeObj);
            if (!valid_datetime_mode(mode)) {
                PyErr_SetString(PyExc_ValueError, "Invalid datetime_mode");
                return NULL;
            }
            datetimeMode = (unsigned) mode;
            if (datetimeMode && datetime_mode_format(datetimeMode) != DM_ISO8601) {
                PyErr_SetString(PyExc_ValueError,
                                "Invalid datetime_mode, can deserialize only from"
                                " ISO8601");
                return NULL;
            }
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "datetime_mode must be a non-negative integer value or None");
            return NULL;
        }
    }

    if (uuidModeObj) {
        if (uuidModeObj == Py_None) {
            uuidMode = UM_NONE;
        } else if (PyLong_Check(uuidModeObj)) {
            int mode = PyLong_AsLong(uuidModeObj);
            if (mode < 0 || mode >= UM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid uuid_mode");
                return NULL;
            }
            uuidMode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "uuid_mode must be an integer value or None");
            return NULL;
        }
    }

    if (parseModeObj) {
        if (parseModeObj == Py_None) {
            parseMode = PM_NONE;
        } else if (PyLong_Check(parseModeObj)) {
            int mode = PyLong_AsLong(parseModeObj);
            if (mode < 0 || mode >= PM_MAX) {
                PyErr_SetString(PyExc_ValueError, "Invalid parse_mode");
                return NULL;
            }
            parseMode = (unsigned) mode;
        } else {
            PyErr_SetString(PyExc_TypeError,
                            "parse_mode must be an integer value or None");
            return NULL;
        }
    }

    d = (DecoderObject*) type->tp_alloc(type, 0);
    if (d == NULL)
        return NULL;

    d->datetimeMode = datetimeMode;
    d->uuidMode = uuidMode;
    d->numberMode = numberMode;
    d->parseMode = parseMode;

    return (PyObject*) d;
}


/////////////
// Encoder //
/////////////


struct DictItem {
    const char* key_str;
    Py_ssize_t key_size;
    PyObject* item;

    DictItem(const char* k,
             Py_ssize_t s,
             PyObject* i)
        : key_str(k),
          key_size(s),
          item(i)
        {}

    bool operator<(const DictItem& other) const {
        Py_ssize_t tks = this->key_size;
        Py_ssize_t oks = other.key_size;
        int cmp = strncmp(this->key_str, other.key_str, tks < oks ? tks : oks);
        return (cmp == 0) ? (tks < oks) : (cmp < 0);
    }
};


static inline bool
all_keys_are_string(PyObject* dict) {
    Py_ssize_t pos = 0;
    PyObject* key;

    while (PyDict_Next(dict, &pos, &key, NULL))
        if (!PyUnicode_Check(key))
            return false;
    return true;
}


template<typename Handler>
static bool
PythonAccept(
    Handler* handler,
    PyObject* object,
    unsigned numberMode,
    unsigned datetimeMode,
    unsigned uuidMode,
    unsigned bytesMode,
    unsigned iterableMode,
    unsigned mappingMode,
    unsigned yggdrasilMode)
{
    int is_decimal;

#define RECURSE(v) PythonAccept(handler, v,				\
				numberMode, datetimeMode, uuidMode,	\
				bytesMode, iterableMode, mappingMode,	\
				yggdrasilMode)

#define ASSERT_VALID_SIZE(l) do {                                       \
    if (l < 0 || l > UINT_MAX) {                                        \
        PyErr_SetString(PyExc_ValueError, "Out of range string size");  \
        return false;                                                   \
    } } while(0)


    if (object == Py_None) {
        handler->Null();
    } else if (PyBool_Check(object)) {
        handler->Bool(object == Py_True);
    } else if (numberMode & NM_DECIMAL
               && (is_decimal = PyObject_IsInstance(object, decimal_type))) {
        if (is_decimal == -1) {
            return false;
        }
	PyObject* floatMethod = PyUnicode_FromString("__float__");
	if (floatMethod == NULL)
	    return false;
	PyObject* decFloat = PyObject_CallMethodObjArgs(object, floatMethod, NULL);
	Py_DECREF(floatMethod);
	if (decFloat == NULL)
	    return false;
	bool r = RECURSE(decFloat);
	Py_LeaveRecursiveCall();
	Py_DECREF(decFloat);
	if (!r)
	  return false;
    } else if (PyLong_Check(object)) {
	int overflow;
	long long i = PyLong_AsLongLongAndOverflow(object, &overflow);
	if (i == -1 && PyErr_Occurred())
	    return false;
	
	if (overflow == 0) {
	    handler->Int64(i);
	} else {
	    unsigned long long ui = PyLong_AsUnsignedLongLong(object);
	    if (PyErr_Occurred())
		return false;
	    
	    handler->Uint64(ui);
	}
    } else if (PyFloat_Check(object)) {
        double d = PyFloat_AsDouble(object);
        if (d == -1.0 && PyErr_Occurred())
            return false;

        if (IS_NAN(d)) {
 	    if (!(numberMode & NM_NAN)) {
                PyErr_SetString(PyExc_ValueError,
                                "Out of range float values are not JSON compliant");
                return false;
            }
        } else if (IS_INF(d)) {
            if (!(numberMode & NM_NAN)) {
                PyErr_SetString(PyExc_ValueError,
                                "Out of range float values are not JSON compliant");
                return false;
            }
        }
	handler->Double(d);
    } else if (PyUnicode_Check(object)) {
        Py_ssize_t l;
        const char* s = PyUnicode_AsUTF8AndSize(object, &l);
        if (s == NULL)
            return false;
        ASSERT_VALID_SIZE(l);
        handler->String(s, (SizeType) l, true);
    } else if (bytesMode == BM_UTF8
               && (PyBytes_Check(object) || PyByteArray_Check(object))) {
        PyObject* unicodeObj = PyUnicode_FromEncodedObject(object, "utf-8", NULL);

        if (unicodeObj == NULL)
            return false;

        Py_ssize_t l;
        const char* s = PyUnicode_AsUTF8AndSize(unicodeObj, &l);
        if (s == NULL) {
            Py_DECREF(unicodeObj);
            return false;
        }
        ASSERT_VALID_SIZE(l);
        handler->String(s, (SizeType) l, true);
        Py_DECREF(unicodeObj);
    } else if ((!(iterableMode & IM_ONLY_LISTS) && PyList_Check(object))
               ||
               PyList_CheckExact(object)) {
        handler->StartArray();

        Py_ssize_t size = PyList_GET_SIZE(object);

        for (Py_ssize_t i = 0; i < size; i++) {
            if (Py_EnterRecursiveCall(" while JSONifying list object"))
                return false;
            PyObject* item = PyList_GET_ITEM(object, i);
            bool r = RECURSE(item);
            Py_LeaveRecursiveCall();
            if (!r)
                return false;
        }

        handler->EndArray((SizeType) size);
    } else if (!(iterableMode & IM_ONLY_LISTS) && PyTuple_Check(object)) {
        handler->StartArray();

        Py_ssize_t size = PyTuple_GET_SIZE(object);

        for (Py_ssize_t i = 0; i < size; i++) {
            if (Py_EnterRecursiveCall(" while JSONifying tuple object"))
                return false;
            PyObject* item = PyTuple_GET_ITEM(object, i);
            bool r = RECURSE(item);
            Py_LeaveRecursiveCall();
            if (!r)
                return false;
        }

        handler->EndArray((SizeType) size);
    } else if (((!(mappingMode & MM_ONLY_DICTS) && PyDict_Check(object))
                ||
                PyDict_CheckExact(object))
               &&
               ((mappingMode & MM_SKIP_NON_STRING_KEYS)
                ||
                (mappingMode & MM_COERCE_KEYS_TO_STRINGS)
                ||
                all_keys_are_string(object))) {
        handler->StartObject();

        Py_ssize_t pos = 0;
        PyObject* key;
        PyObject* item;
        PyObject* coercedKey = NULL;
	SizeType size = 0;

        if (!(mappingMode & MM_SORT_KEYS)) {
            while (PyDict_Next(object, &pos, &key, &item)) {
                if (mappingMode & MM_COERCE_KEYS_TO_STRINGS) {
                    if (!PyUnicode_Check(key)) {
                        coercedKey = PyObject_Str(key);
                        if (coercedKey == NULL)
                            return false;
                        key = coercedKey;
                    }
                }
                if (coercedKey || PyUnicode_Check(key)) {
                    Py_ssize_t l;
                    const char* key_str = PyUnicode_AsUTF8AndSize(key, &l);
                    if (key_str == NULL) {
                        Py_XDECREF(coercedKey);
                        return false;
                    }
                    ASSERT_VALID_SIZE(l);
                    handler->Key(key_str, (SizeType) l, true);
                    if (Py_EnterRecursiveCall(" while JSONifying dict object")) {
                        Py_XDECREF(coercedKey);
                        return false;
                    }
                    bool r = RECURSE(item);
                    Py_LeaveRecursiveCall();
                    if (!r) {
                        Py_XDECREF(coercedKey);
                        return false;
                    }
                } else if (!(mappingMode & MM_SKIP_NON_STRING_KEYS)) {
                    PyErr_SetString(PyExc_TypeError, "keys must be strings");
                    // No need to dispose coercedKey here, because it can be set *only*
                    // when mapping_mode is MM_COERCE_KEYS_TO_STRINGS
                    assert(!coercedKey);
                    return false;
                }
                Py_CLEAR(coercedKey);
		size++;
            }
        } else {
            std::vector<DictItem> items;

            while (PyDict_Next(object, &pos, &key, &item)) {
                if (mappingMode & MM_COERCE_KEYS_TO_STRINGS) {
                    if (!PyUnicode_Check(key)) {
                        coercedKey = PyObject_Str(key);
                        if (coercedKey == NULL)
                            return false;
                        key = coercedKey;
                    }
                }
                if (coercedKey || PyUnicode_Check(key)) {
                    Py_ssize_t l;
                    const char* key_str = PyUnicode_AsUTF8AndSize(key, &l);
                    if (key_str == NULL) {
                        Py_XDECREF(coercedKey);
                        return false;
                    }
                    ASSERT_VALID_SIZE(l);
                    items.push_back(DictItem(key_str, l, item));
                } else if (!(mappingMode & MM_SKIP_NON_STRING_KEYS)) {
                    PyErr_SetString(PyExc_TypeError, "keys must be strings");
                    assert(!coercedKey);
                    return false;
                }
                Py_CLEAR(coercedKey);
            }

            std::sort(items.begin(), items.end());

            for (size_t i=0, s=items.size(); i < s; i++) {
                handler->Key(items[i].key_str, (SizeType) items[i].key_size, true);
                if (Py_EnterRecursiveCall(" while JSONifying dict object"))
                    return false;
                bool r = RECURSE(items[i].item);
                Py_LeaveRecursiveCall();
                if (!r)
                    return false;
		size++;
            }
        }

        handler->EndObject((SizeType) size);
    } else if (datetimeMode != DM_NONE
               && (PyTime_Check(object) || PyDateTime_Check(object))) {
        unsigned year, month, day, hour, min, sec, microsec;
        PyObject* dtObject = object;
        PyObject* asUTC = NULL;

        const int ISOFORMAT_LEN = 42;
        char isoformat[ISOFORMAT_LEN];
        memset(isoformat, 0, ISOFORMAT_LEN);

        const int TIMEZONE_LEN = 16;
        char timeZone[TIMEZONE_LEN] = { 0 };

        if (!(datetimeMode & DM_IGNORE_TZ)
            && PyObject_HasAttr(object, utcoffset_name)) {
            PyObject* utcOffset = PyObject_CallMethodObjArgs(object,
                                                             utcoffset_name,
                                                             NULL);

            if (utcOffset == NULL)
                return false;

            if (utcOffset == Py_None) {
                // Naive value: maybe assume it's in UTC instead of local time
                if (datetimeMode & DM_NAIVE_IS_UTC) {
                    if (PyDateTime_Check(object)) {
                        hour = PyDateTime_DATE_GET_HOUR(dtObject);
                        min = PyDateTime_DATE_GET_MINUTE(dtObject);
                        sec = PyDateTime_DATE_GET_SECOND(dtObject);
                        microsec = PyDateTime_DATE_GET_MICROSECOND(dtObject);
                        year = PyDateTime_GET_YEAR(dtObject);
                        month = PyDateTime_GET_MONTH(dtObject);
                        day = PyDateTime_GET_DAY(dtObject);

                        asUTC = PyDateTimeAPI->DateTime_FromDateAndTime(
                            year, month, day, hour, min, sec, microsec,
                            timezone_utc, PyDateTimeAPI->DateTimeType);
                    } else {
                        hour = PyDateTime_TIME_GET_HOUR(dtObject);
                        min = PyDateTime_TIME_GET_MINUTE(dtObject);
                        sec = PyDateTime_TIME_GET_SECOND(dtObject);
                        microsec = PyDateTime_TIME_GET_MICROSECOND(dtObject);
                        asUTC = PyDateTimeAPI->Time_FromTime(
                            hour, min, sec, microsec,
                            timezone_utc, PyDateTimeAPI->TimeType);
                    }

                    if (asUTC == NULL) {
                        Py_DECREF(utcOffset);
                        return false;
                    }

                    dtObject = asUTC;

                    if (datetime_mode_format(datetimeMode) == DM_ISO8601)
                        strcpy(timeZone, "+00:00");
                }
            } else {
                // Timezone-aware value
                if (datetimeMode & DM_SHIFT_TO_UTC) {
                    // If it's not already in UTC, shift the value
                    if (PyObject_IsTrue(utcOffset)) {
                        asUTC = PyObject_CallMethodObjArgs(object, astimezone_name,
                                                           timezone_utc, NULL);

                        if (asUTC == NULL) {
                            Py_DECREF(utcOffset);
                            return false;
                        }

                        dtObject = asUTC;
                    }

                    if (datetime_mode_format(datetimeMode) == DM_ISO8601)
                        strcpy(timeZone, "+00:00");
                } else if (datetime_mode_format(datetimeMode) == DM_ISO8601) {
                    int seconds_from_utc = 0;

                    if (PyObject_IsTrue(utcOffset)) {
                        PyObject* tsObj = PyObject_CallMethodObjArgs(utcOffset,
                                                                     total_seconds_name,
                                                                     NULL);

                        if (tsObj == NULL) {
                            Py_DECREF(utcOffset);
                            return false;
                        }

                        seconds_from_utc = (int) PyFloat_AsDouble(tsObj);

                        Py_DECREF(tsObj);
                    }

                    char sign = '+';

                    if (seconds_from_utc < 0) {
                        sign = '-';
                        seconds_from_utc = -seconds_from_utc;
                    }

                    unsigned tz_hour = seconds_from_utc / 3600;
                    unsigned tz_min = (seconds_from_utc % 3600) / 60;

                    snprintf(timeZone, TIMEZONE_LEN-1, "%c%02u:%02u",
                             sign, tz_hour, tz_min);
                }
            }
            Py_DECREF(utcOffset);
        }

        if (datetime_mode_format(datetimeMode) == DM_ISO8601) {
            int size;
            if (PyDateTime_Check(dtObject)) {
                year = PyDateTime_GET_YEAR(dtObject);
                month = PyDateTime_GET_MONTH(dtObject);
                day = PyDateTime_GET_DAY(dtObject);
                hour = PyDateTime_DATE_GET_HOUR(dtObject);
                min = PyDateTime_DATE_GET_MINUTE(dtObject);
                sec = PyDateTime_DATE_GET_SECOND(dtObject);
                microsec = PyDateTime_DATE_GET_MICROSECOND(dtObject);

                if (microsec > 0) {
                    size = snprintf(isoformat,
                                    ISOFORMAT_LEN-1,
                                    "\"%04u-%02u-%02uT%02u:%02u:%02u.%06u%s\"",
                                    year, month, day,
                                    hour, min, sec, microsec,
                                    timeZone);
                } else {
                    size = snprintf(isoformat,
                                    ISOFORMAT_LEN-1,
                                    "\"%04u-%02u-%02uT%02u:%02u:%02u%s\"",
                                    year, month, day,
                                    hour, min, sec,
                                    timeZone);
                }
            } else {
                hour = PyDateTime_TIME_GET_HOUR(dtObject);
                min = PyDateTime_TIME_GET_MINUTE(dtObject);
                sec = PyDateTime_TIME_GET_SECOND(dtObject);
                microsec = PyDateTime_TIME_GET_MICROSECOND(dtObject);

                if (microsec > 0) {
                    size = snprintf(isoformat,
                                    ISOFORMAT_LEN-1,
                                    "\"%02u:%02u:%02u.%06u%s\"",
                                    hour, min, sec, microsec,
                                    timeZone);
                } else {
                    size = snprintf(isoformat,
                                    ISOFORMAT_LEN-1,
                                    "\"%02u:%02u:%02u%s\"",
                                    hour, min, sec,
                                    timeZone);
                }
            }
            handler->String(isoformat, (SizeType) size, true);
        } else /* if (datetimeMode & DM_UNIX_TIME) */ {
            if (PyDateTime_Check(dtObject)) {
                PyObject* timestampObj = PyObject_CallMethodObjArgs(dtObject,
                                                                    timestamp_name,
                                                                    NULL);

                if (timestampObj == NULL) {
                    Py_XDECREF(asUTC);
                    return false;
                }

                double timestamp = PyFloat_AsDouble(timestampObj);

                Py_DECREF(timestampObj);

                if (datetimeMode & DM_ONLY_SECONDS) {
                    handler->Int64((int64_t) timestamp);
                } else {
                    handler->Double(timestamp);
                }
            } else {
                hour = PyDateTime_TIME_GET_HOUR(dtObject);
                min = PyDateTime_TIME_GET_MINUTE(dtObject);
                sec = PyDateTime_TIME_GET_SECOND(dtObject);
                microsec = PyDateTime_TIME_GET_MICROSECOND(dtObject);

                long timestamp = hour * 3600 + min * 60 + sec;

                if (datetimeMode & DM_ONLY_SECONDS)
                    handler->Int64(timestamp);
                else
                    handler->Double(timestamp + (microsec / 1000000.0));
            }
        }
        Py_XDECREF(asUTC);
    } else if (datetimeMode != DM_NONE && PyDate_Check(object)) {
        unsigned year = PyDateTime_GET_YEAR(object);
        unsigned month = PyDateTime_GET_MONTH(object);
        unsigned day = PyDateTime_GET_DAY(object);

        if (datetime_mode_format(datetimeMode) == DM_ISO8601) {
            const int ISOFORMAT_LEN = 18;
            char isoformat[ISOFORMAT_LEN];
            int size;
            memset(isoformat, 0, ISOFORMAT_LEN);

            size = snprintf(isoformat, ISOFORMAT_LEN-1, "\"%04u-%02u-%02u\"",
                            year, month, day);
            handler->String(isoformat, (SizeType) size, true);
        } else /* datetime_mode_format(datetimeMode) == DM_UNIX_TIME */ {
            // A date object, take its midnight timestamp
            PyObject* midnightObj;
            PyObject* timestampObj;

            if (datetimeMode & (DM_SHIFT_TO_UTC | DM_NAIVE_IS_UTC))
                midnightObj = PyDateTimeAPI->DateTime_FromDateAndTime(
                    year, month, day, 0, 0, 0, 0,
                    timezone_utc, PyDateTimeAPI->DateTimeType);
            else
                midnightObj = PyDateTime_FromDateAndTime(year, month, day,
                                                         0, 0, 0, 0);

            if (midnightObj == NULL) {
                return false;
            }

            timestampObj = PyObject_CallMethodObjArgs(midnightObj, timestamp_name,
                                                      NULL);

            Py_DECREF(midnightObj);

            if (timestampObj == NULL) {
                return false;
            }

            double timestamp = PyFloat_AsDouble(timestampObj);

            Py_DECREF(timestampObj);

            if (datetimeMode & DM_ONLY_SECONDS) {
                handler->Int64((int64_t) timestamp);
            } else {
                handler->Double(timestamp);
            }
        }
    } else if (uuidMode != UM_NONE
               && PyObject_TypeCheck(object, (PyTypeObject*) uuid_type)) {
        PyObject* hexval;
        if (uuidMode == UM_CANONICAL)
            hexval = PyObject_Str(object);
        else
            hexval = PyObject_GetAttr(object, hex_name);
        if (hexval == NULL)
            return false;

        Py_ssize_t size;
        const char* s = PyUnicode_AsUTF8AndSize(hexval, &size);
        if (s == NULL) {
            Py_DECREF(hexval);
            return false;
        }
        if (RAPIDJSON_UNLIKELY(size != 32 && size != 36)) {
            PyErr_Format(PyExc_ValueError,
                         "Bad UUID hex, expected a string of either 32 or 36 chars,"
                         " got %.200R", hexval);
            Py_DECREF(hexval);
            return false;
        }

        char quoted[39];
        quoted[0] = quoted[size + 1] = '"';
        memcpy(quoted + 1, s, size);
        handler->String(quoted, (SizeType) size + 2, true);
        Py_DECREF(hexval);
    } else if (!(iterableMode & IM_ONLY_LISTS) && PyIter_Check(object)) {
        PyObject* iterator = PyObject_GetIter(object);
        if (iterator == NULL)
            return false;

        handler->StartArray();

        PyObject* item;
	SizeType size = 0;
        while ((item = PyIter_Next(iterator))) {
            if (Py_EnterRecursiveCall(" while JSONifying iterable object")) {
                Py_DECREF(item);
                Py_DECREF(iterator);
                return false;
            }
            bool r = RECURSE(item);
            Py_LeaveRecursiveCall();
            Py_DECREF(item);
            if (!r) {
                Py_DECREF(iterator);
                return false;
            }
	    size++;
        }

        Py_DECREF(iterator);

        // PyIter_Next() may exit with an error
        if (PyErr_Occurred())
            return false;

        handler->EndArray((SizeType) size);
    } else if (PyObject_TypeCheck(object, &RawJSON_Type)) {
        const char* jsonStr;
        Py_ssize_t l;
        jsonStr = PyUnicode_AsUTF8AndSize(((RawJSON*) object)->value, &l);
        if (jsonStr == NULL)
            return false;
        ASSERT_VALID_SIZE(l);
        handler->String(jsonStr, (SizeType) l, true);
    } else if (PyObject_IsInstance(object, (PyObject*)&QuantityArray_Type)) {
	RAPIDJSON_DEFAULT_ALLOCATOR allocator;
	QuantityArrayObject* v = (QuantityArrayObject*) object;
	Value* x = new Value();
	bool ret = x->SetPythonObjectRaw(object);
	if (ret) {
	    std::string unitsS = v->units->units->str();
	    ret = x->SetUnits(unitsS.c_str(), unitsS.length());
	}
	if (ret)
	    ret = x->Accept(*handler);
	delete x;
	if (!ret) {
	    PyObject* cls_name = PyObject_GetAttrString((PyObject*)(object->ob_type),
							"__name__");
	    PyErr_Format(PyExc_TypeError, "Error serializing %s", PyUnicode_AsUTF8(cls_name));
	}
	return ret;
    } else if (PyObject_IsInstance(object, (PyObject*)&Ply_Type)) {
	RAPIDJSON_DEFAULT_ALLOCATOR allocator;
	PlyObject* v = (PlyObject*) object;
	Value* x = new Value();
	x->SetPlyRaw(*v->ply, &allocator);
	bool ret = x->Accept(*handler);
	delete x;
	if (!ret)
	    PyErr_Format(PyExc_TypeError, "Error serializing Ply instance");
	return ret;
    } else if (PyObject_IsInstance(object, (PyObject*)&ObjWavefront_Type)) {
	RAPIDJSON_DEFAULT_ALLOCATOR allocator;
	ObjWavefrontObject* v = (ObjWavefrontObject*) object;
	Value* x = new Value();
	x->SetObj(*v->obj, &allocator);
	bool ret = x->Accept(*handler);
	delete x;
	if (!ret)
	    PyErr_Format(PyExc_TypeError, "Error serializing ObjWavefront instance");
	return ret;
    } else if (!((object == Py_None) ||
		 PyBool_Check(object) ||
		 PyObject_IsInstance(object, decimal_type) ||
		 PyLong_Check(object) ||
		 PyFloat_Check(object) ||
		 PyUnicode_Check(object) ||
		 ((bytesMode == BM_UTF8 || bytesMode == BM_NONE) &&
		  (PyBytes_Check(object) || PyByteArray_Check(object))) ||
		 PyList_Check(object) ||
		 PyTuple_Check(object) ||
		 PyDict_Check(object) ||
		 PyTime_Check(object) ||
		 PyDateTime_Check(object) ||
		 PyDate_Check(object) ||
		 PyObject_TypeCheck(object, (PyTypeObject*) uuid_type) ||
		 PyIter_Check(object))) {
	// Try to import trimesh
	PyObject* trimeshClass = import_trimesh_class();
	if (trimeshClass != NULL && PyObject_IsInstance(object, trimeshClass)) {
	    RAPIDJSON_DEFAULT_ALLOCATOR allocator;
	    Py_INCREF(object);
	    PyObject* ply_args = PyTuple_Pack(1, object);
	    if (ply_args == NULL) {
		Py_DECREF(object);
		return false;
	    }
	    PlyObject* object_ply = (PlyObject*)ply_from_trimesh(NULL, ply_args, NULL);
	    Py_DECREF(ply_args);
	    if (object_ply == NULL)
		return false;
	    Value* x = new Value();
	    x->SetPlyRaw(*object_ply->ply, &allocator);
	    Py_DECREF((PyObject*)object_ply);
	    bool ret = x->Accept(*handler);
	    if (!ret)
		PyErr_Format(PyExc_TypeError, "Error serializing Trimesh instance as Ply instance");
	    return ret;
	}
	// PythonAccept
	RAPIDJSON_DEFAULT_ALLOCATOR allocator;
	Value* x = new Value();
	bool ret = x->SetPythonObjectRaw(object, &allocator, false,
					 (yggdrasilMode & YM_PICKLE));
	if (ret)
	    ret = x->Accept(*handler);
	delete x;
	if (!ret && !PyErr_Occurred())
	    PyErr_Format(PyExc_TypeError, "%R is not JSON serializable even with yggdrasil extension", object);
	return ret;
    } else {
	if (!PyErr_Occurred())
	    PyErr_Format(PyExc_TypeError, "%R is not JSON serializable", object);
	return false;
    }

    // Catch possible error raised in associated stream operations
    return PyErr_Occurred() ? false : true;

#undef RECURSE
#undef ASSERT_VALID_SIZE
}

static bool python2document(PyObject* jsonObject, Document& d,
			    unsigned numberMode,
			    unsigned datetimeMode,
			    unsigned uuidMode,
			    unsigned bytesMode,
			    unsigned iterableMode,
			    unsigned mappingMode,
			    unsigned yggdrasilMode,
			    unsigned expectsString,
			    bool forSchema = false,
			    bool forceObject = false,
			    bool* isEmptyString = NULL) {
    const char* jsonStr;
    Py_ssize_t jsonStrLen = 0;

    if (isEmptyString != NULL)
	isEmptyString[0] = false;
    if ((!forceObject) && PyBytes_Check(jsonObject)) {
        jsonStr = PyBytes_AsString(jsonObject);
        if (jsonStr == NULL)
	    return false;
	jsonStrLen = PyBytes_Size(jsonObject);
    } else if ((!forceObject) && PyUnicode_Check(jsonObject)) {
        jsonStr = PyUnicode_AsUTF8AndSize(jsonObject, &jsonStrLen);
        if (jsonStr == NULL)
	    return false;
    } else if (forceObject || (!forSchema) || PyDict_Check(jsonObject)) {
        jsonStr = NULL;
    } else {
        PyErr_Format(PyExc_TypeError, "Expected string or UTF-8 encoded bytes or a schema in a Python dictionary (not %R).", PyObject_Type(jsonObject));
	return false;
    }
    if (jsonStr != NULL && jsonStrLen == 0 && !forSchema) {
	if (isEmptyString != NULL) {
	    isEmptyString[0] = true;
	}
	jsonStr = NULL;
    }

    bool error;
    bool empty = false;

    if ((jsonStr != NULL) && (!isJSONDocument(jsonStr, jsonStrLen, &empty,
					      expectsString)))
	jsonStr = NULL;

    if (jsonStr == NULL) {
        error = (!PythonAccept(&d, jsonObject, numberMode, datetimeMode,
			       uuidMode, bytesMode, iterableMode,
			       mappingMode, yggdrasilMode));
	d.FinalizeFromStack();
	if (error)
	    return false;
    } else {
        Py_BEGIN_ALLOW_THREADS
        error = d.Parse(jsonStr).HasParseError();
        Py_END_ALLOW_THREADS
	if (error && expectsString) {
	    error = (!PythonAccept(&d, jsonObject, numberMode, datetimeMode,
				   uuidMode, bytesMode, iterableMode,
				   mappingMode, yggdrasilMode));
	    d.FinalizeFromStack();
	    if (error)
		return false;
	}
    }

    if (error) {
        PyErr_Format(decode_error, "Invalid JSON when creating a document (expectsString = %d)", (int)expectsString);
	return false;
    }
    return true;
}

template<typename WriterT>
static bool
dumps_internal(
    WriterT* writer,
    PyObject* object,
    PyObject* defaultFn,
    unsigned numberMode,
    unsigned datetimeMode,
    unsigned uuidMode,
    unsigned bytesMode,
    unsigned iterableMode,
    unsigned mappingMode,
    unsigned yggdrasilMode)
{
    int is_decimal;

#define RECURSE(v) dumps_internal(writer, v, defaultFn,                 \
                                  numberMode, datetimeMode, uuidMode,   \
                                  bytesMode, iterableMode, mappingMode,	\
				  yggdrasilMode)

#define ASSERT_VALID_SIZE(l) do {                                       \
    if (l < 0 || l > UINT_MAX) {                                        \
        PyErr_SetString(PyExc_ValueError, "Out of range string size");  \
        return false;                                                   \
    } } while(0)


    if (object == Py_None) {
        writer->Null();
    } else if (PyBool_Check(object)) {
        writer->Bool(object == Py_True);
    } else if (numberMode & NM_DECIMAL
               && (is_decimal = PyObject_IsInstance(object, decimal_type))) {
        if (is_decimal == -1) {
            return false;
        }

        if (!(numberMode & NM_NAN)) {
            bool is_inf_or_nan;
            PyObject* is_inf = PyObject_CallMethodObjArgs(object, is_infinite_name,
                                                          NULL);

            if (is_inf == NULL) {
                return false;
            }
            is_inf_or_nan = is_inf == Py_True;
            Py_DECREF(is_inf);

            if (!is_inf_or_nan) {
                PyObject* is_nan = PyObject_CallMethodObjArgs(object, is_nan_name,
                                                              NULL);

                if (is_nan == NULL) {
                    return false;
                }
                is_inf_or_nan = is_nan == Py_True;
                Py_DECREF(is_nan);
            }

            if (is_inf_or_nan) {
                PyErr_SetString(PyExc_ValueError,
                                "Out of range decimal values are not JSON compliant");
                return false;
            }
        }

        PyObject* decStrObj = PyObject_Str(object);
        if (decStrObj == NULL)
            return false;

        Py_ssize_t size;
        const char* decStr = PyUnicode_AsUTF8AndSize(decStrObj, &size);
        if (decStr == NULL) {
            Py_DECREF(decStrObj);
            return false;
        }

        writer->RawValue(decStr, size, kNumberType);
        Py_DECREF(decStrObj);
    } else if (PyLong_Check(object)) {
        if (numberMode & NM_NATIVE) {
            int overflow;
            long long i = PyLong_AsLongLongAndOverflow(object, &overflow);
            if (i == -1 && PyErr_Occurred())
                return false;

            if (overflow == 0) {
                writer->Int64(i);
            } else {
                unsigned long long ui = PyLong_AsUnsignedLongLong(object);
                if (PyErr_Occurred())
                    return false;

                writer->Uint64(ui);
            }
        } else {
            // Mimic stdlib json: subclasses of int may override __repr__, but we still
            // want to encode them as integers in JSON; one example within the standard
            // library is IntEnum

            PyObject* intStrObj = PyLong_Type.tp_repr(object);
            if (intStrObj == NULL)
                return false;

            Py_ssize_t size;
            const char* intStr = PyUnicode_AsUTF8AndSize(intStrObj, &size);
            if (intStr == NULL) {
                Py_DECREF(intStrObj);
                return false;
            }

            writer->RawValue(intStr, size, kNumberType);
            Py_DECREF(intStrObj);
        }
    } else if (PyFloat_Check(object)) {
        double d = PyFloat_AsDouble(object);
        if (d == -1.0 && PyErr_Occurred())
            return false;

        if (IS_NAN(d)) {
            if (numberMode & NM_NAN) {
                writer->RawValue("NaN", 3, kNumberType);
            } else {
                PyErr_SetString(PyExc_ValueError,
                                "Out of range float values are not JSON compliant");
                return false;
            }
        } else if (IS_INF(d)) {
            if (!(numberMode & NM_NAN)) {
                PyErr_SetString(PyExc_ValueError,
                                "Out of range float values are not JSON compliant");
                return false;
            } else if (d < 0) {
                writer->RawValue("-Infinity", 9, kNumberType);
            } else {
                writer->RawValue("Infinity", 8, kNumberType);
            }
        } else {
            // The RJ dtoa() produces "strange" results for particular values, see #101:
            // use Python's repr() to emit a raw value instead of writer->Double(d)

            PyObject* dr = PyObject_Repr(object);

            if (dr == NULL)
                return false;

            Py_ssize_t l;
            const char* rs = PyUnicode_AsUTF8AndSize(dr, &l);
            if (rs == NULL) {
                Py_DECREF(dr);
                return false;
            }

            writer->RawValue(rs, l, kNumberType);
            Py_DECREF(dr);
        }
    } else if (PyUnicode_Check(object)) {
        Py_ssize_t l;
        const char* s = PyUnicode_AsUTF8AndSize(object, &l);
        if (s == NULL)
            return false;
        ASSERT_VALID_SIZE(l);
        writer->String(s, (SizeType) l);
    } else if (bytesMode == BM_UTF8
               && (PyBytes_Check(object) || PyByteArray_Check(object))) {
        PyObject* unicodeObj = PyUnicode_FromEncodedObject(object, "utf-8", NULL);

        if (unicodeObj == NULL)
            return false;

        Py_ssize_t l;
        const char* s = PyUnicode_AsUTF8AndSize(unicodeObj, &l);
        if (s == NULL) {
            Py_DECREF(unicodeObj);
            return false;
        }
        ASSERT_VALID_SIZE(l);
        writer->String(s, (SizeType) l);
        Py_DECREF(unicodeObj);
    } else if (PyList_CheckExact(object)
               ||
               (!(iterableMode & IM_ONLY_LISTS) && PyList_Check(object))) {
        writer->StartArray();

        Py_ssize_t size = PyList_GET_SIZE(object);

        for (Py_ssize_t i = 0; i < size; i++) {
            if (Py_EnterRecursiveCall(" while JSONifying list object"))
                return false;
            PyObject* item = PyList_GET_ITEM(object, i);
            bool r = RECURSE(item);
            Py_LeaveRecursiveCall();
            if (!r)
                return false;
        }

        writer->EndArray();
    } else if (!(iterableMode & IM_ONLY_LISTS) && PyTuple_Check(object)) {
        writer->StartArray();

        Py_ssize_t size = PyTuple_GET_SIZE(object);

        for (Py_ssize_t i = 0; i < size; i++) {
            if (Py_EnterRecursiveCall(" while JSONifying tuple object"))
                return false;
            PyObject* item = PyTuple_GET_ITEM(object, i);
            bool r = RECURSE(item);
            Py_LeaveRecursiveCall();
            if (!r)
                return false;
        }

        writer->EndArray();
    } else if ((PyDict_CheckExact(object)
                ||
                (!(mappingMode & MM_ONLY_DICTS) && PyDict_Check(object)))
               &&
               ((mappingMode & MM_SKIP_NON_STRING_KEYS)
                ||
                (mappingMode & MM_COERCE_KEYS_TO_STRINGS)
                ||
                all_keys_are_string(object))) {
        writer->StartObject();

        Py_ssize_t pos = 0;
        PyObject* key;
        PyObject* item;
        PyObject* coercedKey = NULL;

        if (!(mappingMode & MM_SORT_KEYS)) {
            while (PyDict_Next(object, &pos, &key, &item)) {
                if (mappingMode & MM_COERCE_KEYS_TO_STRINGS) {
                    if (!PyUnicode_Check(key)) {
                        coercedKey = PyObject_Str(key);
                        if (coercedKey == NULL)
                            return false;
                        key = coercedKey;
                    }
                }
                if (coercedKey || PyUnicode_Check(key)) {
                    Py_ssize_t l;
                    const char* key_str = PyUnicode_AsUTF8AndSize(key, &l);
                    if (key_str == NULL) {
                        Py_XDECREF(coercedKey);
                        return false;
                    }
                    ASSERT_VALID_SIZE(l);
                    writer->Key(key_str, (SizeType) l);
                    if (Py_EnterRecursiveCall(" while JSONifying dict object")) {
                        Py_XDECREF(coercedKey);
                        return false;
                    }
                    bool r = RECURSE(item);
                    Py_LeaveRecursiveCall();
                    if (!r) {
                        Py_XDECREF(coercedKey);
                        return false;
                    }
                } else if (!(mappingMode & MM_SKIP_NON_STRING_KEYS)) {
                    PyErr_SetString(PyExc_TypeError, "keys must be strings");
                    // No need to dispose coercedKey here, because it can be set *only*
                    // when mapping_mode is MM_COERCE_KEYS_TO_STRINGS
                    assert(!coercedKey);
                    return false;
                }
                Py_CLEAR(coercedKey);
            }
        } else {
            std::vector<DictItem> items;

            while (PyDict_Next(object, &pos, &key, &item)) {
                if (mappingMode & MM_COERCE_KEYS_TO_STRINGS) {
                    if (!PyUnicode_Check(key)) {
                        coercedKey = PyObject_Str(key);
                        if (coercedKey == NULL)
                            return false;
                        key = coercedKey;
                    }
                }
                if (coercedKey || PyUnicode_Check(key)) {
                    Py_ssize_t l;
                    const char* key_str = PyUnicode_AsUTF8AndSize(key, &l);
                    if (key_str == NULL) {
                        Py_XDECREF(coercedKey);
                        return false;
                    }
                    ASSERT_VALID_SIZE(l);
                    items.push_back(DictItem(key_str, l, item));
                } else if (!(mappingMode & MM_SKIP_NON_STRING_KEYS)) {
                    PyErr_SetString(PyExc_TypeError, "keys must be strings");
                    assert(!coercedKey);
                    return false;
                }
                Py_CLEAR(coercedKey);
            }

            std::sort(items.begin(), items.end());

            for (size_t i=0, s=items.size(); i < s; i++) {
                writer->Key(items[i].key_str, (SizeType) items[i].key_size);
                if (Py_EnterRecursiveCall(" while JSONifying dict object"))
                    return false;
                bool r = RECURSE(items[i].item);
                Py_LeaveRecursiveCall();
                if (!r)
                    return false;
            }
        }

        writer->EndObject();
    } else if (datetimeMode != DM_NONE
               && (PyTime_Check(object) || PyDateTime_Check(object))) {
        unsigned year, month, day, hour, min, sec, microsec;
        PyObject* dtObject = object;
        PyObject* asUTC = NULL;

        const int ISOFORMAT_LEN = 42;
        char isoformat[ISOFORMAT_LEN];
        memset(isoformat, 0, ISOFORMAT_LEN);

        // The timezone is always shorter than this, but gcc12 emits a warning about
        // sprintf() that *may* produce longer results, because we pass int values when
        // concretely they are constrained to 24*3600 seconds: pacify gcc using a bigger
        // buffer
        const int TIMEZONE_LEN = 24;
        char timeZone[TIMEZONE_LEN] = { 0 };

        if (!(datetimeMode & DM_IGNORE_TZ)
            && PyObject_HasAttr(object, utcoffset_name)) {
            PyObject* utcOffset = PyObject_CallMethodObjArgs(object,
                                                             utcoffset_name,
                                                             NULL);

            if (utcOffset == NULL)
                return false;

            if (utcOffset == Py_None) {
                // Naive value: maybe assume it's in UTC instead of local time
                if (datetimeMode & DM_NAIVE_IS_UTC) {
                    if (PyDateTime_Check(object)) {
                        hour = PyDateTime_DATE_GET_HOUR(dtObject);
                        min = PyDateTime_DATE_GET_MINUTE(dtObject);
                        sec = PyDateTime_DATE_GET_SECOND(dtObject);
                        microsec = PyDateTime_DATE_GET_MICROSECOND(dtObject);
                        year = PyDateTime_GET_YEAR(dtObject);
                        month = PyDateTime_GET_MONTH(dtObject);
                        day = PyDateTime_GET_DAY(dtObject);

                        asUTC = PyDateTimeAPI->DateTime_FromDateAndTime(
                            year, month, day, hour, min, sec, microsec,
                            timezone_utc, PyDateTimeAPI->DateTimeType);
                    } else {
                        hour = PyDateTime_TIME_GET_HOUR(dtObject);
                        min = PyDateTime_TIME_GET_MINUTE(dtObject);
                        sec = PyDateTime_TIME_GET_SECOND(dtObject);
                        microsec = PyDateTime_TIME_GET_MICROSECOND(dtObject);
                        asUTC = PyDateTimeAPI->Time_FromTime(
                            hour, min, sec, microsec,
                            timezone_utc, PyDateTimeAPI->TimeType);
                    }

                    if (asUTC == NULL) {
                        Py_DECREF(utcOffset);
                        return false;
                    }

                    dtObject = asUTC;

                    if (datetime_mode_format(datetimeMode) == DM_ISO8601)
                        strcpy(timeZone, "+00:00");
                }
            } else {
                // Timezone-aware value
                if (datetimeMode & DM_SHIFT_TO_UTC) {
                    // If it's not already in UTC, shift the value
                    if (PyObject_IsTrue(utcOffset)) {
                        asUTC = PyObject_CallMethodObjArgs(object, astimezone_name,
                                                           timezone_utc, NULL);

                        if (asUTC == NULL) {
                            Py_DECREF(utcOffset);
                            return false;
                        }

                        dtObject = asUTC;
                    }

                    if (datetime_mode_format(datetimeMode) == DM_ISO8601)
                        strcpy(timeZone, "+00:00");
                } else if (datetime_mode_format(datetimeMode) == DM_ISO8601) {
                    int seconds_from_utc = 0;

                    if (PyObject_IsTrue(utcOffset)) {
                        PyObject* tsObj = PyObject_CallMethodObjArgs(utcOffset,
                                                                     total_seconds_name,
                                                                     NULL);

                        if (tsObj == NULL) {
                            Py_DECREF(utcOffset);
                            return false;
                        }

                        seconds_from_utc = (int) PyFloat_AsDouble(tsObj);

                        Py_DECREF(tsObj);
                    }

                    char sign = '+';

                    if (seconds_from_utc < 0) {
                        sign = '-';
                        seconds_from_utc = -seconds_from_utc;
                    }

                    unsigned tz_hour = seconds_from_utc / 3600;
                    unsigned tz_min = (seconds_from_utc % 3600) / 60;

                    snprintf(timeZone, TIMEZONE_LEN-1, "%c%02u:%02u",
                             sign, tz_hour, tz_min);
                }
            }
            Py_DECREF(utcOffset);
        }

        if (datetime_mode_format(datetimeMode) == DM_ISO8601) {
            int size;
            if (PyDateTime_Check(dtObject)) {
                year = PyDateTime_GET_YEAR(dtObject);
                month = PyDateTime_GET_MONTH(dtObject);
                day = PyDateTime_GET_DAY(dtObject);
                hour = PyDateTime_DATE_GET_HOUR(dtObject);
                min = PyDateTime_DATE_GET_MINUTE(dtObject);
                sec = PyDateTime_DATE_GET_SECOND(dtObject);
                microsec = PyDateTime_DATE_GET_MICROSECOND(dtObject);

                if (microsec > 0) {
                    size = snprintf(isoformat,
                                    ISOFORMAT_LEN-1,
                                    "\"%04u-%02u-%02uT%02u:%02u:%02u.%06u%s\"",
                                    year, month, day,
                                    hour, min, sec, microsec,
                                    timeZone);
                } else {
                    size = snprintf(isoformat,
                                    ISOFORMAT_LEN-1,
                                    "\"%04u-%02u-%02uT%02u:%02u:%02u%s\"",
                                    year, month, day,
                                    hour, min, sec,
                                    timeZone);
                }
            } else {
                hour = PyDateTime_TIME_GET_HOUR(dtObject);
                min = PyDateTime_TIME_GET_MINUTE(dtObject);
                sec = PyDateTime_TIME_GET_SECOND(dtObject);
                microsec = PyDateTime_TIME_GET_MICROSECOND(dtObject);

                if (microsec > 0) {
                    size = snprintf(isoformat,
                                    ISOFORMAT_LEN-1,
                                    "\"%02u:%02u:%02u.%06u%s\"",
                                    hour, min, sec, microsec,
                                    timeZone);
                } else {
                    size = snprintf(isoformat,
                                    ISOFORMAT_LEN-1,
                                    "\"%02u:%02u:%02u%s\"",
                                    hour, min, sec,
                                    timeZone);
                }
            }
            writer->RawValue(isoformat, size, kStringType);
        } else /* if (datetimeMode & DM_UNIX_TIME) */ {
            if (PyDateTime_Check(dtObject)) {
                PyObject* timestampObj = PyObject_CallMethodObjArgs(dtObject,
                                                                    timestamp_name,
                                                                    NULL);

                if (timestampObj == NULL) {
                    Py_XDECREF(asUTC);
                    return false;
                }

                double timestamp = PyFloat_AsDouble(timestampObj);

                Py_DECREF(timestampObj);

                if (datetimeMode & DM_ONLY_SECONDS) {
                    writer->Int64((int64_t) timestamp);
                } else {
                    // Writer.SetMaxDecimalPlaces(6) truncates the value,
                    // so for example 1514893636.276703 would come out as
                    // 1514893636.276702, because its exact double value is
                    // 1514893636.2767028808593750000000000...
                    char tsStr[12 + 1 + 6 + 1];

                    // Temporarily switch to a POSIX locale, in case the outer world is
                    // configured differently: by chance I got one doctest failure, and I
                    // can only imagine that recent Sphinx (that is, 4.2+) initializes the
                    // locale to something that implies a decimal separator different from
                    // a dot ".", say a comma "," when LANG is "it_IT"... not the best
                    // thing to do when emitting JSON!

                    const char* locale = setlocale(LC_NUMERIC, NULL);
                    setlocale(LC_NUMERIC, "C");

                    int size = snprintf(tsStr, 12 + 1 + 6, "%.6f", timestamp);

                    setlocale(LC_NUMERIC, locale);

                    // Remove trailing 0s
                    while (tsStr[size-2] != '.' && tsStr[size-1] == '0')
                        size--;
                    writer->RawValue(tsStr, size, kNumberType);
                }
            } else {
                hour = PyDateTime_TIME_GET_HOUR(dtObject);
                min = PyDateTime_TIME_GET_MINUTE(dtObject);
                sec = PyDateTime_TIME_GET_SECOND(dtObject);
                microsec = PyDateTime_TIME_GET_MICROSECOND(dtObject);

                long timestamp = hour * 3600 + min * 60 + sec;

                if (datetimeMode & DM_ONLY_SECONDS)
                    writer->Int64(timestamp);
                else
                    writer->Double(timestamp + (microsec / 1000000.0));
            }
        }
        Py_XDECREF(asUTC);
    } else if (datetimeMode != DM_NONE && PyDate_Check(object)) {
        unsigned year = PyDateTime_GET_YEAR(object);
        unsigned month = PyDateTime_GET_MONTH(object);
        unsigned day = PyDateTime_GET_DAY(object);

        if (datetime_mode_format(datetimeMode) == DM_ISO8601) {
            const int ISOFORMAT_LEN = 18;
            char isoformat[ISOFORMAT_LEN];
            int size;
            memset(isoformat, 0, ISOFORMAT_LEN);

            size = snprintf(isoformat, ISOFORMAT_LEN-1, "\"%04u-%02u-%02u\"",
                            year, month, day);
            writer->RawValue(isoformat, size, kStringType);
        } else /* datetime_mode_format(datetimeMode) == DM_UNIX_TIME */ {
            // A date object, take its midnight timestamp
            PyObject* midnightObj;
            PyObject* timestampObj;

            if (datetimeMode & (DM_SHIFT_TO_UTC | DM_NAIVE_IS_UTC))
                midnightObj = PyDateTimeAPI->DateTime_FromDateAndTime(
                    year, month, day, 0, 0, 0, 0,
                    timezone_utc, PyDateTimeAPI->DateTimeType);
            else
                midnightObj = PyDateTime_FromDateAndTime(year, month, day,
                                                         0, 0, 0, 0);

            if (midnightObj == NULL) {
                return false;
            }

            timestampObj = PyObject_CallMethodObjArgs(midnightObj, timestamp_name,
                                                      NULL);

            Py_DECREF(midnightObj);

            if (timestampObj == NULL) {
                return false;
            }

            double timestamp = PyFloat_AsDouble(timestampObj);

            Py_DECREF(timestampObj);

            if (datetimeMode & DM_ONLY_SECONDS) {
                writer->Int64((int64_t) timestamp);
            } else {
                // Writer.SetMaxDecimalPlaces(6) truncates the value,
                // so for example 1514893636.276703 would come out as
                // 1514893636.276702, because its exact double value is
                // 1514893636.2767028808593750000000000...
                char tsStr[12 + 1 + 6 + 1];

                // Temporarily switch to a POSIX locale, in case the outer
                // world is configured differently, see above

                const char* locale = setlocale(LC_NUMERIC, NULL);
                setlocale(LC_NUMERIC, "C");

                setlocale(LC_NUMERIC, locale);

                int size = snprintf(tsStr, 12 + 1 + 6, "%.6f", timestamp);
                // Remove trailing 0s
                while (tsStr[size-2] != '.' && tsStr[size-1] == '0')
                    size--;
                writer->RawValue(tsStr, size, kNumberType);
            }
        }
    } else if (uuidMode != UM_NONE
               && PyObject_TypeCheck(object, (PyTypeObject*) uuid_type)) {
        PyObject* hexval;
        if (uuidMode == UM_CANONICAL)
            hexval = PyObject_Str(object);
        else
            hexval = PyObject_GetAttr(object, hex_name);
        if (hexval == NULL)
            return false;

        Py_ssize_t size;
        const char* s = PyUnicode_AsUTF8AndSize(hexval, &size);
        if (s == NULL) {
            Py_DECREF(hexval);
            return false;
        }
        if (RAPIDJSON_UNLIKELY(size != 32 && size != 36)) {
            PyErr_Format(PyExc_ValueError,
                         "Bad UUID hex, expected a string of either 32 or 36 chars,"
                         " got %.200R", hexval);
            Py_DECREF(hexval);
            return false;
        }

        char quoted[39];
        quoted[0] = quoted[size + 1] = '"';
        memcpy(quoted + 1, s, size);
        writer->RawValue(quoted, (SizeType) size + 2, kStringType);
        Py_DECREF(hexval);
    } else if (!(iterableMode & IM_ONLY_LISTS) && PyIter_Check(object)) {
        PyObject* iterator = PyObject_GetIter(object);
        if (iterator == NULL)
            return false;

        writer->StartArray();

        PyObject* item;
        while ((item = PyIter_Next(iterator))) {
            if (Py_EnterRecursiveCall(" while JSONifying iterable object")) {
                Py_DECREF(item);
                Py_DECREF(iterator);
                return false;
            }
            bool r = RECURSE(item);
            Py_LeaveRecursiveCall();
            Py_DECREF(item);
            if (!r) {
                Py_DECREF(iterator);
                return false;
            }
        }

        Py_DECREF(iterator);

        // PyIter_Next() may exit with an error
        if (PyErr_Occurred())
            return false;

        writer->EndArray();
    } else if (PyObject_TypeCheck(object, &RawJSON_Type)) {
        const char* jsonStr;
        Py_ssize_t l;
        jsonStr = PyUnicode_AsUTF8AndSize(((RawJSON*) object)->value, &l);
        if (jsonStr == NULL)
            return false;
        ASSERT_VALID_SIZE(l);
        writer->RawValue(jsonStr, (SizeType) l, kStringType);
    } else if (defaultFn) {
        PyObject* retval = PyObject_CallFunctionObjArgs(defaultFn, object, NULL);
        if (retval == NULL) {
	    PyObject *type, *value, *traceback;
	    PyErr_Fetch(&type, &value, &traceback);
	    bool r = PythonAccept(writer, object, numberMode, datetimeMode, uuidMode,
				  bytesMode, iterableMode, mappingMode, yggdrasilMode);
	    PyErr_Restore(type, value, traceback);
	    if (r)
		PyErr_Clear();
            return r;
	}
        if (Py_EnterRecursiveCall(" while JSONifying default function result")) {
            Py_DECREF(retval);
            return false;
        }
        bool r = RECURSE(retval);
        Py_LeaveRecursiveCall();
        Py_DECREF(retval);
        if (!r)
            return false;
    } else {
	return PythonAccept(writer, object, numberMode, datetimeMode, uuidMode,
			    bytesMode, iterableMode, mappingMode, yggdrasilMode);
    }

    // Catch possible error raised in associated stream operations
    return PyErr_Occurred() ? false : true;

#undef RECURSE
#undef ASSERT_VALID_SIZE
}


typedef struct {
    PyObject_HEAD
    bool ensureAscii;
    unsigned writeMode;
    char indentChar;
    unsigned indentCount;
    unsigned datetimeMode;
    unsigned uuidMode;
    unsigned numberMode;
    unsigned bytesMode;
    unsigned iterableMode;
    unsigned mappingMode;
    unsigned yggdrasilMode;
} EncoderObject;


PyDoc_STRVAR(dumps_docstring,
             "dumps(obj, *, skipkeys=False, ensure_ascii=True, write_mode=WM_COMPACT,"
             " indent=4, default=None, sort_keys=False, number_mode=None,"
             " datetime_mode=None, uuid_mode=None, bytes_mode=BM_SCALAR,"
             " iterable_mode=IM_ANY_ITERABLE, mapping_mode=MM_ANY_MAPPING,"
             " yggdrasil_mode=YM_BASE64, allow_nan=True)\n"
             "\n"
             "Encode a Python object into a JSON string.");


static PyObject*
dumps(PyObject* self, PyObject* args, PyObject* kwargs)
{
    /* Converts a Python object to a JSON-encoded string. */

    PyObject* value;
    int ensureAscii = true;
    PyObject* indent = NULL;
    PyObject* defaultFn = NULL;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* bytesModeObj = NULL;
    unsigned bytesMode = BM_SCALAR;
    PyObject* writeModeObj = NULL;
    unsigned writeMode = WM_COMPACT;
    PyObject* iterableModeObj = NULL;
    unsigned iterableMode = IM_ANY_ITERABLE;
    PyObject* mappingModeObj = NULL;
    unsigned mappingMode = MM_ANY_MAPPING;
    PyObject* yggdrasilModeObj = NULL;
    unsigned yggdrasilMode = YM_BASE64;
    char indentChar = ' ';
    unsigned indentCount = 4;
    static char const* kwlist[] = {
        "obj",
        "skipkeys",             // alias of MM_SKIP_NON_STRING_KEYS
        "ensure_ascii",
        "indent",
        "default",
        "sort_keys",            // alias of MM_SORT_KEYS
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "bytes_mode",
        "write_mode",
        "iterable_mode",
        "mapping_mode",
	"yggdrasil_mode",

        /* compatibility with stdlib json */
        "allow_nan",

        NULL
    };
    int skipKeys = false;
    int sortKeys = false;
    int allowNan = -1;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$ppOOpOOOOOOOOp:rapidjson.dumps",
                                     (char**) kwlist,
                                     &value,
                                     &skipKeys,
                                     &ensureAscii,
                                     &indent,
                                     &defaultFn,
                                     &sortKeys,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
                                     &bytesModeObj,
                                     &writeModeObj,
                                     &iterableModeObj,
                                     &mappingModeObj,
				     &yggdrasilModeObj,
                                     &allowNan))
        return NULL;

    if (defaultFn && !PyCallable_Check(defaultFn)) {
        if (defaultFn == Py_None) {
            defaultFn = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "default must be a callable");
            return NULL;
        }
    }

    if (!accept_indent_arg(indent, writeMode, indentCount, indentChar))
        return NULL;

    if (!accept_write_mode_arg(writeModeObj, writeMode))
        return NULL;

    if (!accept_number_mode_arg(numberModeObj, allowNan, numberMode))
        return NULL;

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    if (!accept_bytes_mode_arg(bytesModeObj, bytesMode))
        return NULL;

    if (!accept_iterable_mode_arg(iterableModeObj, iterableMode))
        return NULL;

    if (!accept_mapping_mode_arg(mappingModeObj, mappingMode))
        return NULL;

    if (!accept_yggdrasil_mode_arg(yggdrasilModeObj, yggdrasilMode))
        return NULL;

    if (skipKeys)
        mappingMode |= MM_SKIP_NON_STRING_KEYS;

    if (sortKeys)
        mappingMode |= MM_SORT_KEYS;

    return do_encode(value, defaultFn, ensureAscii ? true : false, writeMode, indentChar,
                     indentCount, numberMode, datetimeMode, uuidMode, bytesMode,
                     iterableMode, mappingMode, yggdrasilMode);
}


PyDoc_STRVAR(dump_docstring,
             "dump(obj, stream, *, skipkeys=False, ensure_ascii=True,"
             " write_mode=WM_COMPACT, indent=4, default=None, sort_keys=False,"
             " number_mode=None, datetime_mode=None, uuid_mode=None, bytes_mode=BM_SCALAR,"
             " iterable_mode=IM_ANY_ITERABLE, mapping_mode=MM_ANY_MAPPING,"
             " yggdrasil_mode=YM_BASE64, chunk_size=65536, allow_nan=True)\n"
             "\n"
             "Encode a Python object into a JSON stream.");


static PyObject*
dump(PyObject* self, PyObject* args, PyObject* kwargs)
{
    /* Converts a Python object to a JSON-encoded stream. */

    PyObject* value;
    PyObject* stream;
    int ensureAscii = true;
    PyObject* indent = NULL;
    PyObject* defaultFn = NULL;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* bytesModeObj = NULL;
    unsigned bytesMode = BM_SCALAR;
    PyObject* writeModeObj = NULL;
    unsigned writeMode = WM_COMPACT;
    PyObject* iterableModeObj = NULL;
    unsigned iterableMode = IM_ANY_ITERABLE;
    PyObject* mappingModeObj = NULL;
    unsigned mappingMode = MM_ANY_MAPPING;
    PyObject* yggdrasilModeObj = NULL;
    unsigned yggdrasilMode = YM_BASE64;
    char indentChar = ' ';
    unsigned indentCount = 4;
    PyObject* chunkSizeObj = NULL;
    size_t chunkSize = 65536;
    int allowNan = -1;
    static char const* kwlist[] = {
        "obj",
        "stream",
        "skipkeys",             // alias of MM_SKIP_NON_STRING_KEYS
        "ensure_ascii",
        "indent",
        "default",
        "sort_keys",            // alias of MM_SORT_KEYS
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "bytes_mode",
        "chunk_size",
        "write_mode",
        "iterable_mode",
        "mapping_mode",
	"yggdrasil_mode",

        /* compatibility with stdlib json */
        "allow_nan",

        NULL
    };
    int skipKeys = false;
    int sortKeys = false;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO|$ppOOpOOOOOOOOOp:rapidjson.dump",
                                     (char**) kwlist,
                                     &value,
                                     &stream,
                                     &skipKeys,
                                     &ensureAscii,
                                     &indent,
                                     &defaultFn,
                                     &sortKeys,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
                                     &bytesModeObj,
                                     &chunkSizeObj,
                                     &writeModeObj,
                                     &iterableModeObj,
                                     &mappingModeObj,
				     &yggdrasilModeObj,
                                     &allowNan))
        return NULL;

    if (defaultFn && !PyCallable_Check(defaultFn)) {
        if (defaultFn == Py_None) {
            defaultFn = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "default must be a callable");
            return NULL;
        }
    }

    if (!accept_indent_arg(indent, writeMode, indentCount, indentChar))
        return NULL;

    if (!accept_write_mode_arg(writeModeObj, writeMode))
        return NULL;

    if (!accept_number_mode_arg(numberModeObj, allowNan, numberMode))
        return NULL;

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    if (!accept_bytes_mode_arg(bytesModeObj, bytesMode))
        return NULL;

    if (!accept_chunk_size_arg(chunkSizeObj, chunkSize))
        return NULL;

    if (!accept_iterable_mode_arg(iterableModeObj, iterableMode))
        return NULL;

    if (!accept_mapping_mode_arg(mappingModeObj, mappingMode))
        return NULL;

    if (!accept_yggdrasil_mode_arg(yggdrasilModeObj, yggdrasilMode))
        return NULL;

    if (skipKeys)
        mappingMode |= MM_SKIP_NON_STRING_KEYS;

    if (sortKeys)
        mappingMode |= MM_SORT_KEYS;

    return do_stream_encode(value, stream, chunkSize, defaultFn,
                            ensureAscii ? true : false, writeMode, indentChar,
                            indentCount, numberMode, datetimeMode, uuidMode, bytesMode,
                            iterableMode, mappingMode, yggdrasilMode);
}


PyDoc_STRVAR(encoder_doc,
             "Encoder(skip_invalid_keys=False, ensure_ascii=True, write_mode=WM_COMPACT,"
             " indent=4, sort_keys=False, number_mode=None, datetime_mode=None,"
             " uuid_mode=None, bytes_mode=None, iterable_mode=IM_ANY_ITERABLE,"
             " mapping_mode=MM_ANY_MAPPING, yggdrasil_mode=YM_BASE64)\n\n"
             "Create and return a new Encoder instance.");


static PyMemberDef encoder_members[] = {
    {"ensure_ascii",
     T_BOOL, offsetof(EncoderObject, ensureAscii), READONLY,
     "whether the output should contain only ASCII characters."},
    {"indent_char",
     T_CHAR, offsetof(EncoderObject, indentChar), READONLY,
     "What will be used as end-of-line character."},
    {"indent_count",
     T_UINT, offsetof(EncoderObject, indentCount), READONLY,
     "The indentation width."},
    {"datetime_mode",
     T_UINT, offsetof(EncoderObject, datetimeMode), READONLY,
     "Whether and how datetime values should be encoded."},
    {"uuid_mode",
     T_UINT, offsetof(EncoderObject, uuidMode), READONLY,
     "Whether and how UUID values should be encoded"},
    {"number_mode",
     T_UINT, offsetof(EncoderObject, numberMode), READONLY,
     "The encoding behavior with regards to numeric values."},
    {"bytes_mode",
     T_UINT, offsetof(EncoderObject, bytesMode), READONLY,
     "How bytes values should be treated."},
    {"write_mode",
     T_UINT, offsetof(EncoderObject, writeMode), READONLY,
     "Whether the output should be pretty printed or not."},
    {"iterable_mode",
     T_UINT, offsetof(EncoderObject, iterableMode), READONLY,
     "Whether iterable values other than lists shall be encoded as JSON arrays or not."},
    {"mapping_mode",
     T_UINT, offsetof(EncoderObject, mappingMode), READONLY,
     "Whether mapping values other than dicts shall be encoded as JSON objects or not."},
    {"yggdrasil_mode",
     T_UINT, offsetof(EncoderObject, yggdrasilMode), READONLY,
     "Whether yggdrasil extension values shall be encoded in base64 or not."},
    {NULL}
};


static PyObject*
encoder_get_skip_invalid_keys(EncoderObject* e, void* closure)
{
    return PyBool_FromLong(e->mappingMode & MM_SKIP_NON_STRING_KEYS);
}

static PyObject*
encoder_get_sort_keys(EncoderObject* e, void* closure)
{
    return PyBool_FromLong(e->mappingMode & MM_SORT_KEYS);
}

// Backward compatibility, previously they were members of EncoderObject

static PyGetSetDef encoder_props[] = {
    {"skip_invalid_keys", (getter) encoder_get_skip_invalid_keys, NULL,
     "Whether invalid keys shall be skipped."},
    {"sort_keys", (getter) encoder_get_sort_keys, NULL,
     "Whether dictionary keys shall be sorted alphabetically."},
    {NULL}
};

static PyTypeObject Encoder_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.Encoder",                      /* tp_name */
    sizeof(EncoderObject),                    /* tp_basicsize */
    0,                                        /* tp_itemsize */
    0,                                        /* tp_dealloc */
    0,                                        /* tp_print */
    0,                                        /* tp_getattr */
    0,                                        /* tp_setattr */
    0,                                        /* tp_compare */
    0,                                        /* tp_repr */
    0,                                        /* tp_as_number */
    0,                                        /* tp_as_sequence */
    0,                                        /* tp_as_mapping */
    0,                                        /* tp_hash */
    (ternaryfunc) encoder_call,               /* tp_call */
    0,                                        /* tp_str */
    0,                                        /* tp_getattro */
    0,                                        /* tp_setattro */
    0,                                        /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
    encoder_doc,                              /* tp_doc */
    0,                                        /* tp_traverse */
    0,                                        /* tp_clear */
    0,                                        /* tp_richcompare */
    0,                                        /* tp_weaklistoffset */
    0,                                        /* tp_iter */
    0,                                        /* tp_iternext */
    0,                                        /* tp_methods */
    encoder_members,                          /* tp_members */
    encoder_props,                            /* tp_getset */
    0,                                        /* tp_base */
    0,                                        /* tp_dict */
    0,                                        /* tp_descr_get */
    0,                                        /* tp_descr_set */
    0,                                        /* tp_dictoffset */
    0,                                        /* tp_init */
    0,                                        /* tp_alloc */
    encoder_new,                              /* tp_new */
    PyObject_Del,                             /* tp_free */
};


#define Encoder_CheckExact(v) (Py_TYPE(v) == &Encoder_Type)
#define Encoder_Check(v) PyObject_TypeCheck(v, &Encoder_Type)


#define DUMPS_INTERNAL_CALL                             \
    (dumps_internal(&writer,                            \
                    value,                              \
                    defaultFn,                          \
                    numberMode,                         \
                    datetimeMode,                       \
                    uuidMode,                           \
                    bytesMode,                          \
                    iterableMode,                       \
                    mappingMode,				\
		    yggdrasilMode)				\
     ? PyUnicode_FromString(buf.GetString()) : NULL)


static PyObject*
do_encode(PyObject* value, PyObject* defaultFn, bool ensureAscii, unsigned writeMode,
          char indentChar, unsigned indentCount, unsigned numberMode,
          unsigned datetimeMode, unsigned uuidMode, unsigned bytesMode,
          unsigned iterableMode, unsigned mappingMode, unsigned yggdrasilMode)
{
    if (writeMode == WM_COMPACT) {
        if (ensureAscii) {
            GenericStringBuffer<ASCII<> > buf;
            Writer<GenericStringBuffer<ASCII<> >, UTF8<>, ASCII<> > writer(buf);
	    if (yggdrasilMode & YM_READABLE) {
		writer.SetYggdrasilMode(true);
	    }
            return DUMPS_INTERNAL_CALL;
        } else {
            StringBuffer buf;
            Writer<StringBuffer> writer(buf);
	    if (yggdrasilMode & YM_READABLE) {
		writer.SetYggdrasilMode(true);
	    }
            return DUMPS_INTERNAL_CALL;
        }
    } else if (ensureAscii) {
        GenericStringBuffer<ASCII<> > buf;
        PrettyWriter<GenericStringBuffer<ASCII<> >, UTF8<>, ASCII<> > writer(buf);
        writer.SetIndent(indentChar, indentCount);
        if (writeMode & WM_SINGLE_LINE_ARRAY) {
            writer.SetFormatOptions(kFormatSingleLineArray);
        }
	if (yggdrasilMode & YM_READABLE) {
	    writer.SetYggdrasilMode(true);
	}
        return DUMPS_INTERNAL_CALL;
    } else {
        StringBuffer buf;
        PrettyWriter<StringBuffer> writer(buf);
        writer.SetIndent(indentChar, indentCount);
        if (writeMode & WM_SINGLE_LINE_ARRAY) {
            writer.SetFormatOptions(kFormatSingleLineArray);
        }
	if (yggdrasilMode & YM_READABLE) {
	    writer.SetYggdrasilMode(true);
	}
        return DUMPS_INTERNAL_CALL;
    }
}


#define DUMP_INTERNAL_CALL                      \
    (dumps_internal(&writer,                    \
                    value,                      \
                    defaultFn,                  \
                    numberMode,                 \
                    datetimeMode,               \
                    uuidMode,                   \
                    bytesMode,                  \
                    iterableMode,               \
                    mappingMode,			\
		    yggdrasilMode)			\
     ? Py_INCREF(Py_None), Py_None : NULL)


static PyObject*
do_stream_encode(PyObject* value, PyObject* stream, size_t chunkSize, PyObject* defaultFn,
                 bool ensureAscii, unsigned writeMode, char indentChar,
                 unsigned indentCount, unsigned numberMode, unsigned datetimeMode,
                 unsigned uuidMode, unsigned bytesMode, unsigned iterableMode,
                 unsigned mappingMode, unsigned yggdrasilMode)
{
    PyWriteStreamWrapper os(stream, chunkSize);

    if (writeMode == WM_COMPACT) {
        if (ensureAscii) {
            Writer<PyWriteStreamWrapper, UTF8<>, ASCII<> > writer(os);
	    if (yggdrasilMode & YM_READABLE) {
		writer.SetYggdrasilMode(true);
	    }
            return DUMP_INTERNAL_CALL;
        } else {
            Writer<PyWriteStreamWrapper> writer(os);
	    if (yggdrasilMode & YM_READABLE) {
		writer.SetYggdrasilMode(true);
	    }
            return DUMP_INTERNAL_CALL;
        }
    } else if (ensureAscii) {
        PrettyWriter<PyWriteStreamWrapper, UTF8<>, ASCII<> > writer(os);
        writer.SetIndent(indentChar, indentCount);
        if (writeMode & WM_SINGLE_LINE_ARRAY) {
            writer.SetFormatOptions(kFormatSingleLineArray);
        }
	if (yggdrasilMode & YM_READABLE) {
	    writer.SetYggdrasilMode(true);
	}
        return DUMP_INTERNAL_CALL;
    } else {
        PrettyWriter<PyWriteStreamWrapper> writer(os);
        writer.SetIndent(indentChar, indentCount);
        if (writeMode & WM_SINGLE_LINE_ARRAY) {
            writer.SetFormatOptions(kFormatSingleLineArray);
        }
	if (yggdrasilMode & YM_READABLE) {
	    writer.SetYggdrasilMode(true);
	}
        return DUMP_INTERNAL_CALL;
    }
}


static PyObject*
encoder_call(PyObject* self, PyObject* args, PyObject* kwargs)
{
    static char const* kwlist[] = {
        "obj",
        "stream",
        "chunk_size",
        NULL
    };
    PyObject* value;
    PyObject* stream = NULL;
    PyObject* chunkSizeObj = NULL;
    size_t chunkSize = 65536;
    PyObject* defaultFn = NULL;
    PyObject* result;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|O$O",
                                     (char**) kwlist,
                                     &value,
                                     &stream,
                                     &chunkSizeObj))
        return NULL;

    EncoderObject* e = (EncoderObject*) self;

    if (stream != NULL && stream != Py_None) {
        if (!PyObject_HasAttr(stream, write_name)) {
            PyErr_SetString(PyExc_TypeError, "Expected a writable stream");
            return NULL;
        }

        if (!accept_chunk_size_arg(chunkSizeObj, chunkSize))
            return NULL;

        if (PyObject_HasAttr(self, default_name)) {
            defaultFn = PyObject_GetAttr(self, default_name);
        }

        result = do_stream_encode(value, stream, chunkSize, defaultFn, e->ensureAscii,
                                  e->writeMode, e->indentChar, e->indentCount,
                                  e->numberMode, e->datetimeMode, e->uuidMode,
                                  e->bytesMode, e->iterableMode, e->mappingMode,
				  e->yggdrasilMode);
    } else {
        if (PyObject_HasAttr(self, default_name)) {
            defaultFn = PyObject_GetAttr(self, default_name);
        }

        result = do_encode(value, defaultFn, e->ensureAscii, e->writeMode, e->indentChar,
                           e->indentCount, e->numberMode, e->datetimeMode, e->uuidMode,
                           e->bytesMode, e->iterableMode, e->mappingMode,
			   e->yggdrasilMode);
    }

    if (defaultFn != NULL)
        Py_DECREF(defaultFn);

    return result;
}


static PyObject*
encoder_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    EncoderObject* e;
    int ensureAscii = true;
    PyObject* indent = NULL;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* bytesModeObj = NULL;
    unsigned bytesMode = BM_SCALAR;
    PyObject* writeModeObj = NULL;
    unsigned writeMode = WM_COMPACT;
    PyObject* iterableModeObj = NULL;
    unsigned iterableMode = IM_ANY_ITERABLE;
    PyObject* mappingModeObj = NULL;
    unsigned mappingMode = MM_ANY_MAPPING;
    PyObject* yggdrasilModeObj = NULL;
    unsigned yggdrasilMode = YM_BASE64;
    char indentChar = ' ';
    unsigned indentCount = 4;
    static char const* kwlist[] = {
        "skip_invalid_keys",    // alias of MM_SKIP_NON_STRING_KEYS
        "ensure_ascii",
        "indent",
        "sort_keys",            // alias of MM_SORT_KEYS
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "bytes_mode",
        "write_mode",
        "iterable_mode",
        "mapping_mode",
	"yggdrasil_mode",
        NULL
    };
    int skipInvalidKeys = false;
    int sortKeys = false;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ppOpOOOOOOOO:Encoder",
                                     (char**) kwlist,
                                     &skipInvalidKeys,
                                     &ensureAscii,
                                     &indent,
                                     &sortKeys,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
                                     &bytesModeObj,
                                     &writeModeObj,
                                     &iterableModeObj,
                                     &mappingModeObj,
				     &yggdrasilModeObj))
        return NULL;

    if (!accept_indent_arg(indent, writeMode, indentCount, indentChar))
        return NULL;

    if (!accept_write_mode_arg(writeModeObj, writeMode))
        return NULL;

    if (!accept_number_mode_arg(numberModeObj, -1, numberMode))
        return NULL;

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    if (!accept_bytes_mode_arg(bytesModeObj, bytesMode))
        return NULL;

    if (!accept_iterable_mode_arg(iterableModeObj, iterableMode))
        return NULL;

    if (!accept_mapping_mode_arg(mappingModeObj, mappingMode))
        return NULL;

    if (!accept_yggdrasil_mode_arg(yggdrasilModeObj, yggdrasilMode))
	return NULL;

    if (skipInvalidKeys)
        mappingMode |= MM_SKIP_NON_STRING_KEYS;

    if (sortKeys)
        mappingMode |= MM_SORT_KEYS;

    e = (EncoderObject*) type->tp_alloc(type, 0);
    if (e == NULL)
        return NULL;

    e->ensureAscii = ensureAscii ? true : false;
    e->writeMode = writeMode;
    e->indentChar = indentChar;
    e->indentCount = indentCount;
    e->datetimeMode = datetimeMode;
    e->uuidMode = uuidMode;
    e->numberMode = numberMode;
    e->bytesMode = bytesMode;
    e->iterableMode = iterableMode;
    e->mappingMode = mappingMode;
    e->yggdrasilMode = yggdrasilMode;

    return (PyObject*) e;
}


///////////////
// Validator //
///////////////

template <typename ValidatorObject>
static void set_validation_error(ValidatorObject& validator,
				 PyObject* error_type=validation_error,
				 bool warning = false) {
    StringBuffer sptr;
    StringBuffer dptr;

    Py_BEGIN_ALLOW_THREADS
    validator.GetInvalidSchemaPointer().StringifyUriFragment(sptr);
    validator.GetInvalidDocumentPointer().StringifyUriFragment(dptr);
    Py_END_ALLOW_THREADS

    StringBuffer sb;
    PrettyWriter<StringBuffer> w(sb);
    RAPIDJSON_DEFAULT_ALLOCATOR allocator;
    Value err;
    std::string msg;
    bool success = (warning) ? validator.GetWarningMsg(err, allocator) :
	validator.GetErrorMsg(err, allocator);
    if (!success)
	msg = "Error creating ValidationError message.";
    else {
	err.Accept(w);
	msg = std::string(sb.GetString());
    }
    if (warning) {
	PyErr_WarnEx(error_type, msg.c_str(), 1);
    } else {
	PyErr_SetString(error_type, msg.c_str());
    }
	
    sptr.Clear();
    dptr.Clear();
}

typedef struct {
    PyObject_HEAD
    SchemaDocument *schema;
    PyObject* objectHook;
    unsigned numberMode;
    unsigned datetimeMode;
    unsigned uuidMode;
    unsigned bytesMode;
    unsigned iterableMode;
    unsigned mappingMode;
    unsigned yggdrasilMode;
    unsigned expectsString;
} ValidatorObject;


PyDoc_STRVAR(validator_doc,
             "Validator(json_schema, object_hook=None, number_mode=None,"
	     " datetime_mode=None, uuid_mode=None, bytes_mode=BM_SCALAR,"
	     " iterable_mode=IM_ANY_ITERABLE, mapping_mode=MM_ANY_MAPPING,"
	     " yggdrasil_mode=YM_BASE64, allow_nan=True)\n"
             "\n"
             "Create and return a new Validator instance from the given `json_schema`"
             " string or Python dictionary.");


static PyMethodDef validator_methods[] = {
    {"validate", (PyCFunction) validator_validate,
     METH_VARARGS | METH_KEYWORDS,
     "Validate a JSON document."
    },
    {"compare", (PyCFunction) validator_compare,
     METH_VARARGS | METH_KEYWORDS,
     "Compare two schemas for compatiblity."},
    {"generate_data", (PyCFunction) validator_generate_data,
     METH_NOARGS,
     "Generate data that fits the schema."},
    {"check_schema", (PyCFunction) validator_check_schema,
     METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     "Validate a schema against the JSON metaschema."},
    {NULL}  /* Sentinel */
};


static PyTypeObject Validator_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.Validator",          /* tp_name */
    sizeof(ValidatorObject),        /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor) validator_dealloc, /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    0,                              /* tp_repr */
    0,                              /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    (ternaryfunc) validator_call,   /* tp_call */
    0,                              /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    validator_doc,                  /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    0,                              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    validator_methods,              /* tp_methods */
    0,                              /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    0,                              /* tp_init */
    0,                              /* tp_alloc */
    validator_new,                  /* tp_new */
    PyObject_Del,                   /* tp_free */
};


static PyObject* validator_call(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject* jsonObject;
    PyObject* relativePathRootObj = NULL;
    static char const* kwlist[] = {
	"obj",
	"relative_path_root",
	NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$O",
				     (char**) kwlist,
				     &jsonObject,
				     &relativePathRootObj))
        return NULL;

    ValidatorObject* v = (ValidatorObject*) self;
    Document d;
    bool isEmptyString = false;
    if (!python2document(jsonObject, d, v->numberMode, v->datetimeMode,
			 v->uuidMode, v->bytesMode, v->iterableMode,
			 v->mappingMode, v->yggdrasilMode, v->expectsString,
			 false, false, &isEmptyString))
	return NULL;

    SchemaValidator validator(*v->schema);
    if (relativePathRootObj != NULL) {
	Py_ssize_t relativePathRootLen = 0;
	const char* relativePathRootStr = PyUnicode_AsUTF8AndSize(relativePathRootObj, &relativePathRootLen);
	if (!relativePathRootStr)
	    return NULL;
	validator.SetRelativePathRoot(relativePathRootStr,
				      (SizeType)relativePathRootLen);
    }
    bool accept;

    if (validator.RequiresPython() || d.RequiresPython()) {
	accept = d.Accept(validator);
    } else {
	Py_BEGIN_ALLOW_THREADS
	accept = d.Accept(validator);
	Py_END_ALLOW_THREADS
    }

    if (!accept) {
	if (isEmptyString) {
	    PyErr_SetString(decode_error, "Invalid empty JSON document");
	    return NULL;
	}
	set_validation_error(validator);
        return NULL;
    }

    if (validator.GetInvalidSchemaCode() == kValidateWarnings)
	set_validation_error(validator, validation_warning, true);
    
    Py_RETURN_NONE;
}

static void validator_dealloc(PyObject* self)
{
    ValidatorObject* s = (ValidatorObject*) self;
    if (s->objectHook)
	Py_DECREF(s->objectHook);
    delete s->schema;
    Py_TYPE(self)->tp_free(self);
}


static PyObject* validator_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject* jsonObject = NULL;
    PyObject* objectHook = NULL;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* bytesModeObj = NULL;
    unsigned bytesMode = BM_SCALAR;
    PyObject* iterableModeObj = NULL;
    unsigned iterableMode = IM_ANY_ITERABLE;
    PyObject* mappingModeObj = NULL;
    unsigned mappingMode = MM_ANY_MAPPING;
    PyObject* yggdrasilModeObj = NULL;
    unsigned yggdrasilMode = YM_BASE64;
    int allowNan = -1;
    static char const* kwlist[] = {
	"schema",
        "object_hook",
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "bytes_mode",
        "iterable_mode",
        "mapping_mode",
	"yggdrasil_mode",

        /* compatibility with stdlib json */
        "allow_nan",

        NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$OOOOOOOOp:Validator",
                                     (char**) kwlist,
				     &jsonObject,
                                     &objectHook,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
				     &bytesModeObj,
				     &iterableModeObj,
				     &mappingModeObj,
				     &yggdrasilModeObj,
                                     &allowNan))
        return NULL;

    if (objectHook && !PyCallable_Check(objectHook)) {
        if (objectHook == Py_None) {
            objectHook = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "object_hook is not callable");
            return NULL;
        }
    }

    if (!accept_number_mode_arg(numberModeObj, allowNan, numberMode))
        return NULL;

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    if (!accept_bytes_mode_arg(bytesModeObj, bytesMode))
        return NULL;

    if (!accept_iterable_mode_arg(iterableModeObj, iterableMode))
        return NULL;

    if (!accept_mapping_mode_arg(mappingModeObj, mappingMode))
        return NULL;

    if (!accept_yggdrasil_mode_arg(yggdrasilModeObj, yggdrasilMode))
        return NULL;

    Document d;
    if (!python2document(jsonObject, d, numberMode, datetimeMode,
			 uuidMode, bytesMode, iterableMode,
			 mappingMode, yggdrasilMode, 0, true))
	return NULL;

    ValidatorObject* v = (ValidatorObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;

    v->schema = new SchemaDocument(d);
    if (objectHook)
	Py_INCREF(objectHook);
    v->objectHook = objectHook;
    v->numberMode = numberMode;
    v->datetimeMode = datetimeMode;
    v->uuidMode = uuidMode;
    v->bytesMode = bytesMode;
    v->iterableMode = iterableMode;
    v->mappingMode = mappingMode;
    v->yggdrasilMode = yggdrasilMode;
    v->expectsString = check_expectsString(d);

    return (PyObject*) v;
}


static PyObject* validator_validate(PyObject* self, PyObject* args, PyObject* kwargs)
{ return validator_call(self, args, kwargs); }


static PyObject* validator_check_schema(PyObject* cls, PyObject* args, PyObject* kwargs)
{
    PyObject* jsonObject;
    PyObject* jsonStandardObj = NULL;
    bool jsonStandard = false;
    PyObject* objectHook = NULL;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* bytesModeObj = NULL;
    unsigned bytesMode = BM_SCALAR;
    PyObject* iterableModeObj = NULL;
    unsigned iterableMode = IM_ANY_ITERABLE;
    PyObject* mappingModeObj = NULL;
    unsigned mappingMode = MM_ANY_MAPPING;
    PyObject* yggdrasilModeObj = NULL;
    unsigned yggdrasilMode = YM_BASE64;
    int allowNan = -1;
    static char const* kwlist[] = {
	"schema",
	"json_standard",
        "object_hook",
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "bytes_mode",
        "iterable_mode",
        "mapping_mode",
	"yggdrasil_mode",

        /* compatibility with stdlib json */
        "allow_nan",

        NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,
				     "O|$OOOOOOOOOp:Validator.check_schema",
                                     (char**) kwlist,
				     &jsonObject,
				     &jsonStandardObj,
                                     &objectHook,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
				     &bytesModeObj,
				     &iterableModeObj,
				     &mappingModeObj,
				     &yggdrasilModeObj,
                                     &allowNan))
        return NULL;

    if (jsonStandardObj && PyBool_Check(jsonStandardObj))
	jsonStandard = (jsonStandardObj == Py_True);
    // TODO: Allow a draft name?

    if (objectHook && !PyCallable_Check(objectHook)) {
        if (objectHook == Py_None) {
            objectHook = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "object_hook is not callable");
            return NULL;
        }
    }

    if (!accept_number_mode_arg(numberModeObj, allowNan, numberMode))
        return NULL;

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    if (!accept_bytes_mode_arg(bytesModeObj, bytesMode))
        return NULL;

    if (!accept_iterable_mode_arg(iterableModeObj, iterableMode))
        return NULL;

    if (!accept_mapping_mode_arg(mappingModeObj, mappingMode))
        return NULL;

    if (!accept_yggdrasil_mode_arg(yggdrasilModeObj, yggdrasilMode))
        return NULL;

    Document d;
    if (!python2document(jsonObject, d, numberMode, datetimeMode,
			 uuidMode, bytesMode, iterableMode,
			 mappingMode, yggdrasilMode, 0, true))
	return NULL;

    Document d_meta;
    bool error = false;
    Py_BEGIN_ALLOW_THREADS
    if (jsonStandard)
	error = d_meta.Parse(get_standard_metaschema<char>()).HasParseError();
    else
	error = d_meta.Parse(get_metaschema<char>()).HasParseError();
    Py_END_ALLOW_THREADS
    if (error) {
	PyErr_SetString(decode_error, "Invalid metaschema");
	return NULL;
    }

    SchemaDocument metaschema(d_meta);
    SchemaValidator validator(metaschema);
    bool accept;

    if (validator.RequiresPython() || d.RequiresPython()) {
	accept = d.Accept(validator);
    } else {
	Py_BEGIN_ALLOW_THREADS
	accept = d.Accept(validator);
	Py_END_ALLOW_THREADS
    }

    if (!accept) {
	set_validation_error(validator);
        return NULL;
    }

    if (validator.GetInvalidSchemaCode() == kValidateWarnings)
	set_validation_error(validator, validation_warning, true);
    
    Py_RETURN_NONE;
    
}

static PyObject* validator_compare(PyObject* self, PyObject* args, PyObject* kwargs)
{
    bool dontRaise = false;
    PyObject* kwargs_copy = NULL;
    if (kwargs != NULL) {
	PyObject* dontRaiseObject = PyDict_GetItemString(kwargs, "dont_raise");
	if (dontRaiseObject == NULL) {
	    Py_INCREF(kwargs);
	    kwargs_copy = kwargs;
	} else {
	    if (dontRaiseObject == Py_False)
		dontRaise = false;
	    else if (dontRaiseObject == Py_True)
		dontRaise = true;
	    PyObject *kw_key, *kw_val;
	    Py_ssize_t kw_pos = 0;
	    kwargs_copy = PyDict_New();
	    if (kwargs_copy == NULL)
		return NULL;
	    PyObject* tmp = PyUnicode_FromString("dont_raise");
	    if (PyDict_Size(kwargs) > 1) {
		while (PyDict_Next(kwargs, &kw_pos, &kw_key, &kw_val)) {
		    if (PyObject_RichCompareBool(kw_key, tmp, Py_EQ))
			continue;
		    if (PyDict_SetItem(kwargs_copy, kw_key, kw_val) < 0) {
			Py_DECREF(tmp);
			return NULL;
		    }
		}
	    }
	    Py_DECREF(tmp);
	}
    }
    PyObject* validator2 = validator_new(&Validator_Type, args, kwargs_copy);
    Py_DECREF(kwargs_copy);
    if (validator2 == NULL)
	return NULL;

    SchemaValidator v1(*((ValidatorObject*)self)->schema);
    SchemaValidator v2(*((ValidatorObject*)validator2)->schema);
    bool accept;
    
    if (v1.RequiresPython() || v2.RequiresPython()) {
	accept = v1.Compare(v2);
    } else {
	Py_BEGIN_ALLOW_THREADS
	accept = v1.Compare(v2);
	Py_END_ALLOW_THREADS
    }

    Py_DECREF(validator2);
    if (!accept) {
	if (dontRaise) {
	    Py_INCREF(Py_False);
	    return Py_False;
	} else {
	    set_validation_error(v1, comparison_error);
	    return NULL;
	}
    }
    Py_INCREF(Py_True);
    return Py_True;
    
}


static PyObject* validator_generate_data(PyObject* self, PyObject*, PyObject*)
{
    Document d;
    ValidatorObject* v = (ValidatorObject*) self;
    SchemaValidator validator(*v->schema);
    bool accept = validator.GenerateData(d);
    if (!accept) {
	set_validation_error(validator, generate_error);
	return NULL;
    }

    PyHandler handler(NULL, v->objectHook, v->datetimeMode, v->uuidMode,
		      v->numberMode);
    accept = d.Accept(handler);
    if (!accept) {
	PyErr_SetString(generate_error, "Error converting the generated JSON document to a Python object");
	return NULL;
    }
    
    if (PyErr_Occurred()) {
        Py_XDECREF(handler.root);
        return NULL;
    }
    
    return handler.root;
}


PyDoc_STRVAR(validate_docstring,
             "validate(obj, schema, object_hook=None, number_mode=None,"
	     " datetime_mode=None, uuid_mode=None, bytes_mode=BM_SCALAR,"
	     " iterable_mode=IM_ANY_ITERABLE, mapping_mode=MM_ANY_MAPPING,"
	     " allow_nan=True, relative_path_root=None)\n"
             "\n"
	     "Validate a Python object against a JSON schema.");


static PyObject*
validate(PyObject* self, PyObject* args, PyObject* kwargs)
{

    if (!PyTuple_Check(args))
	return NULL;

    Py_ssize_t nargs = PyTuple_Size(args);
    if (nargs != 2)
	return NULL;
    PyObject* validator_args = PyTuple_New(nargs - 1);
    for (Py_ssize_t i = 1; i < nargs; i++) {
	PyObject* iarg = PyTuple_GetItem(args, i);
	if (iarg == NULL) {
	    Py_DECREF(validator_args);
	    return NULL;
	}
	Py_INCREF(iarg);
	if (PyTuple_SetItem(validator_args, i - 1, iarg) < 0) {
	    Py_DECREF(iarg);
	    Py_DECREF(validator_args);
	    return NULL;
	}
    }

    PyObject* relativePathRootObj = NULL;
    if (kwargs != NULL)
	relativePathRootObj = PyDict_GetItemString(kwargs, "relative_path_root");
    PyObject* call_kwargs = NULL;
    if (relativePathRootObj != NULL) {
	call_kwargs = PyDict_New();
	if (PyDict_SetItemString(call_kwargs, "relative_path_root",
				 relativePathRootObj) < 0) {
	    Py_DECREF(validator_args);
	    Py_DECREF(call_kwargs);
	    return NULL;
	}
	if (PyDict_DelItemString(kwargs, "relative_path_root") < 0) {
	    Py_DECREF(validator_args);
	    Py_DECREF(call_kwargs);
	    return NULL;
	}
    }
			
    PyObject* validator = validator_new(&Validator_Type, validator_args, kwargs);
    Py_DECREF(validator_args);
    if (validator == NULL) {
	Py_XDECREF(call_kwargs);
	return NULL;
    }

    PyObject* instance = PyTuple_GetItem(args, 0);
    if (instance == NULL) {
	Py_XDECREF(call_kwargs);
	Py_DECREF(validator);
	return NULL;
    }
    PyObject* call_args = PyTuple_Pack(1, instance);
    PyObject* out = validator_call(validator, call_args, NULL);
    Py_DECREF(call_args);
    Py_XDECREF(call_kwargs);
    Py_DECREF(validator);
    return out;
}


PyDoc_STRVAR(encode_schema_docstring,
             "encode_schema(obj, minimal=False, object_hook=None,"
	     " number_mode=None, datetime_mode=None, uuid_mode=None,"
	     " bytes_mode=BM_SCALAR, iterable_mode=IM_ANY_ITERABLE,"
	     " mapping_mode=MM_ANY_MAPPING, allow_nan=True)\n"
             "\n"
	     "Encode a schema for a Python object.");


static PyObject*
encode_schema(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject* jsonObject;
    int minimalSchema = 0;
    PyObject* objectHook = NULL;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* bytesModeObj = NULL;
    unsigned bytesMode = BM_SCALAR;
    PyObject* iterableModeObj = NULL;
    unsigned iterableMode = IM_ANY_ITERABLE;
    PyObject* mappingModeObj = NULL;
    unsigned mappingMode = MM_ANY_MAPPING;
    PyObject* yggdrasilModeObj = NULL;
    unsigned yggdrasilMode = YM_BASE64;
    int allowNan = -1;
    static char const* kwlist[] = {
	"obj",
	"minimal",
        "object_hook"
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "bytes_mode",
        "iterable_mode",
        "mapping_mode",
	"yggdrasil_mode",

        /* compatibility with stdlib json */
        "allow_nan",

        NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$pOOOOOOOOp:encode_schema",
                                     (char**) kwlist,
				     &jsonObject,
				     &minimalSchema,
                                     &objectHook,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
				     &bytesModeObj,
				     &iterableModeObj,
				     &mappingModeObj,
				     &yggdrasilModeObj,
                                     &allowNan))
        return NULL;

    if (objectHook && !PyCallable_Check(objectHook)) {
        if (objectHook == Py_None) {
            objectHook = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "object_hook is not callable");
            return NULL;
        }
    }

    if (!accept_number_mode_arg(numberModeObj, allowNan, numberMode))
        return NULL;

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    if (!accept_bytes_mode_arg(bytesModeObj, bytesMode))
        return NULL;

    if (!accept_iterable_mode_arg(iterableModeObj, iterableMode))
        return NULL;

    if (!accept_mapping_mode_arg(mappingModeObj, mappingMode))
        return NULL;

    if (!accept_yggdrasil_mode_arg(yggdrasilModeObj, yggdrasilMode))
        return NULL;

    Document d;
    if (!python2document(jsonObject, d, numberMode, datetimeMode,
			 uuidMode, bytesMode, iterableMode,
			 mappingMode, yggdrasilMode, 0, false, true))
	return NULL;

    bool accept = false;

    SchemaEncoder schema_encoder(minimalSchema);
    accept = d.Accept(schema_encoder);
    if (!accept) {
	PyErr_SetString(decode_error, "Error encoding schema");
	return NULL;
    }
    
    PyHandler handler(NULL, objectHook, datetimeMode, uuidMode, numberMode);
    accept = schema_encoder.Accept(handler);
    if (!accept) {
	return NULL;
    }
    
    if (PyErr_Occurred()) {
        Py_XDECREF(handler.root);
        return NULL;
    }

    return handler.root;
}


PyDoc_STRVAR(get_metaschema_docstring,
             "get_metaschema(object_hook=None, number_mode=None,"
	     " datetime_mode=None, uuid_mode=None, bytes_mode=BM_SCALAR,"
	     " iterable_mode=IM_ANY_ITERABLE, mapping_mode=MM_ANY_MAPPING,"
	     " allow_nan=True)\n"
             "\n"
	     "Get the yggdrasil modified metaschema.");


static PyObject*
rj_get_metaschema(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject* objectHook = NULL;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    int allowNan = -1;
    static char const* kwlist[] = {
        "object_hook",
        "number_mode",
        "datetime_mode",
        "uuid_mode",

        /* compatibility with stdlib json */
        "allow_nan",

        NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|$OOOOp:get_metaschema",
                                     (char**) kwlist,
                                     &objectHook,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
                                     &allowNan))
        return NULL;

    if (objectHook && !PyCallable_Check(objectHook)) {
        if (objectHook == Py_None) {
            objectHook = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "object_hook is not callable");
            return NULL;
        }
    }

    if (!accept_number_mode_arg(numberModeObj, allowNan, numberMode))
        return NULL;

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    Document d_meta;
    bool error = false;
    Py_BEGIN_ALLOW_THREADS
    error = d_meta.Parse(get_metaschema<char>()).HasParseError();
    Py_END_ALLOW_THREADS
    if (error) {
	PyErr_SetString(decode_error, "Invalid metaschema");
	return NULL;
    }
    
    PyHandler handler(NULL, objectHook, datetimeMode, uuidMode, numberMode);
    bool accept = d_meta.Accept(handler);
    if (!accept) {
	return NULL;
    }
    
    if (PyErr_Occurred()) {
        Py_XDECREF(handler.root);
        return NULL;
    }

    return handler.root;
}


PyDoc_STRVAR(compare_schemas_docstring,
             "compare_schemas(schemaA, schemaB, dont_raise=False)\n"
             "\n"
	     "Compare two schemas for compatibility.");


static PyObject*
compare_schemas(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject *validatorObject1 = NULL, *validatorObject2 = NULL;
    int dontRaise = 0;
    static char const* kwlist[] = {
	"schemaA",
	"schemaB",
	"dont_raise",
	NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO|$p:compare_schemas",
				     (char**) kwlist,
				     &validatorObject1,
				     &validatorObject2,
				     &dontRaise))
	return NULL;

    if (validatorObject1 == NULL || validatorObject2 == NULL) {
	return NULL;
    }

    PyObject* validator1_args = PyTuple_Pack(1, validatorObject1);
    if (validator1_args == NULL)
	return NULL;
    PyObject* validator1_kwargs = PyDict_New();
    if (validator1_kwargs == NULL) {
	Py_DECREF(validator1_args);
	return NULL;
    }
    PyObject* validator1 = validator_new(&Validator_Type, validator1_args, validator1_kwargs);
    Py_DECREF(validator1_args);
    Py_DECREF(validator1_kwargs);
    if (validator1 == NULL)
	return NULL;

    // Py_INCREF(validatorObject2);
    PyObject* validator2_args = PyTuple_Pack(1, validatorObject2);
    if (validator2_args == NULL) {
	Py_DECREF(validator1);
	return NULL;
    }
    PyObject* validator2_kwargs = PyDict_New();
    if (validator2_kwargs == NULL) {
	Py_DECREF(validator1);
	Py_DECREF(validator2_args);
	return NULL;
    }
    PyObject* dontRaiseObject = NULL;
    if (dontRaise)
	dontRaiseObject = Py_True;
    else
	dontRaiseObject = Py_False;
    if (PyDict_SetItemString(validator2_kwargs, "dont_raise", dontRaiseObject) < 0) {
	Py_DECREF(validator1);
	Py_DECREF(validator2_args);
	Py_DECREF(validator2_kwargs);
	return NULL;
    }
    PyObject* out = validator_compare(validator1, validator2_args, validator2_kwargs);
    Py_DECREF(validator1);
    Py_DECREF(validator2_args);
    Py_DECREF(validator2_kwargs);
    return out;
}


PyDoc_STRVAR(generate_data_docstring,
             "generate_data(schema)\n"
             "\n"
	     "Generate data that conforms to the provided schema.");


static PyObject*
generate_data(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject *validatorObject = NULL;
    static char const* kwlist[] = {
	"schema",
	NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$p:generate_data",
				     (char**) kwlist,
				     &validatorObject))
	return NULL;

    if (validatorObject == NULL) {
	return NULL;
    }

    PyObject* validator_args = PyTuple_Pack(1, validatorObject);
    if (validator_args == NULL)
	return NULL;
    PyObject* validator_kwargs = PyDict_New();
    if (validator_kwargs == NULL) {
	Py_DECREF(validator_args);
	return NULL;
    }
    PyObject* validator = validator_new(&Validator_Type, validator_args, validator_kwargs);
    Py_DECREF(validator_args);
    Py_DECREF(validator_kwargs);
    if (validator == NULL)
	return NULL;

    PyObject* out = validator_generate_data(validator, NULL, NULL);
    Py_DECREF(validator);
    return out;
}


PyDoc_STRVAR(as_pure_json_docstring,
	     "as_pure_json(json)\n"
	     "\n"
	     "Convert a JSON document containing yggdrasil extension values to pure JSON.");


static PyObject*
as_pure_json(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject* jsonObject = NULL;
    PyObject* decoderObject = NULL;
    PyObject* objectHook = NULL;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* bytesModeObj = NULL;
    unsigned bytesMode = BM_SCALAR;
    PyObject* iterableModeObj = NULL;
    unsigned iterableMode = IM_ANY_ITERABLE;
    PyObject* mappingModeObj = NULL;
    unsigned mappingMode = MM_ANY_MAPPING;
    PyObject* yggdrasilModeObj = NULL;
    unsigned yggdrasilMode = YM_BASE64;
    int allowNan = -1;
    static char const* kwlist[] = {
	"json",
	"decoder",
        "object_hook",
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "bytes_mode",
        "iterable_mode",
        "mapping_mode",
	"yggdrasil_mode",

        /* compatibility with stdlib json */
        "allow_nan",

	NULL
    };
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$OOOOOOOOp:as_pure_json",
				     (char**) kwlist,
				     &jsonObject,
				     &decoderObject,
                                     &objectHook,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
				     &bytesModeObj,
				     &iterableModeObj,
				     &mappingModeObj,
				     &yggdrasilModeObj,
                                     &allowNan))
	return NULL;
    
    if (objectHook && !PyCallable_Check(objectHook)) {
        if (objectHook == Py_None) {
            objectHook = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "object_hook is not callable");
            return NULL;
        }
    }

    if (!accept_number_mode_arg(numberModeObj, allowNan, numberMode))
        return NULL;

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    if (!accept_bytes_mode_arg(bytesModeObj, bytesMode))
        return NULL;

    if (!accept_iterable_mode_arg(iterableModeObj, iterableMode))
        return NULL;

    if (!accept_mapping_mode_arg(mappingModeObj, mappingMode))
        return NULL;

    if (!accept_yggdrasil_mode_arg(yggdrasilModeObj, yggdrasilMode))
        return NULL;

    Document d;
    bool isEmptyString = false;
    if (!python2document(jsonObject, d, numberMode, datetimeMode,
			 uuidMode, bytesMode, iterableMode,
			 mappingMode, yggdrasilMode, 0, false, false,
			 &isEmptyString))
	return NULL;

    PyHandler handler(decoderObject, objectHook, datetimeMode, uuidMode,
		      numberMode);
    JSONCoreWrapper<PyHandler> wrapped(handler);
    if (!d.Accept(wrapped)) {
	return NULL;
    }
    return handler.root;
}


////////////////
// Normalizer //
////////////////


typedef struct {
    PyObject_HEAD
    SchemaDocument *schema;
    PyObject* objectHook;
    unsigned numberMode;
    unsigned datetimeMode;
    unsigned uuidMode;
    unsigned bytesMode;
    unsigned iterableMode;
    unsigned mappingMode;
    unsigned yggdrasilMode;
    unsigned expectsString;
} NormalizerObject;


PyDoc_STRVAR(normalizer_doc,
             "Normalizer(json_schema, object_hook=None, number_mode=None,"
	     " datetime_mode=None, uuid_mode=None, bytes_mode=BM_SCALAR,"
	     " iterable_mode=IM_ANY_ITERABLE, mapping_mode=MM_ANY_MAPPING,"
	     " yggdrasil_mode=YM_BASE64, allow_nan=True)\n"
             "\n"
             "Create and return a new Normalizer instance from the given `json_schema`"
             " string or Python dictionary.");


static PyMethodDef normalizer_methods[] = {
    {"validate", (PyCFunction) normalizer_validate,
     METH_VARARGS | METH_KEYWORDS,
     "Validate a JSON document."},
    {"normalize", (PyCFunction) normalizer_normalize,
     METH_VARARGS | METH_KEYWORDS,
     "Normalize a JSON document."},
    {"compare", (PyCFunction) normalizer_compare,
     METH_VARARGS | METH_KEYWORDS,
     "Compare two schemas for compatiblity."},
    {"generate_data", (PyCFunction) normalizer_generate_data,
     METH_NOARGS,
     "Generate data that fits the schema."},
    {"check_schema", (PyCFunction) normalizer_check_schema,
     METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     "Validate a schema against the JSON metaschema."},
    {NULL}  /* Sentinel */
};


static PyTypeObject Normalizer_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.Normalizer",         /* tp_name */
    sizeof(NormalizerObject),       /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor) normalizer_dealloc, /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    0,                              /* tp_repr */
    0,                              /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    (ternaryfunc) normalizer_call,  /* tp_call */
    0,                              /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    normalizer_doc,                 /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    0,                              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    normalizer_methods,             /* tp_methods */
    0,                              /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    0,                              /* tp_init */
    0,                              /* tp_alloc */
    normalizer_new,                 /* tp_new */
    PyObject_Del,                   /* tp_free */
};


static PyObject* normalizer_call(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject* jsonObject;
    PyObject* relativePathRootObj = NULL;
    static char const* kwlist[] = {
	"obj",
	"relative_path_root",
	NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$O",
				     (char**) kwlist,
				     &jsonObject,
				     &relativePathRootObj))
        return NULL;

    NormalizerObject* v = (NormalizerObject*) self;
    Document d;
    bool isEmptyString = false;
    if (!python2document(jsonObject, d, v->numberMode, v->datetimeMode,
			 v->uuidMode, v->bytesMode, v->iterableMode,
			 v->mappingMode, v->yggdrasilMode, v->expectsString,
			 false, false, &isEmptyString))
	return NULL;
    
    SchemaNormalizer normalizer(*((NormalizerObject*) self)->schema);
    if (relativePathRootObj != NULL) {
	Py_ssize_t relativePathRootLen = 0;
	const char* relativePathRootStr = PyUnicode_AsUTF8AndSize(relativePathRootObj, &relativePathRootLen);
	if (!relativePathRootStr)
	    return NULL;
	normalizer.SetRelativePathRoot(relativePathRootStr,
				       (SizeType)relativePathRootLen);
    }
    bool accept;

    if (normalizer.RequiresPython() || d.RequiresPython()) {
	accept = d.Accept(normalizer);
    } else {
	Py_BEGIN_ALLOW_THREADS
        accept = d.Accept(normalizer);
	Py_END_ALLOW_THREADS
    }

    if (!accept) {
	if (isEmptyString) {
	    PyErr_SetString(decode_error, "Invalid empty JSON document");
	    return NULL;
	}
	set_validation_error(normalizer, normalization_error);
	return NULL;
    }

    if (normalizer.GetInvalidSchemaCode() == kValidateWarnings)
	set_validation_error(normalizer, normalization_warning, true);
    
    PyHandler handler(NULL, v->objectHook, v->datetimeMode, v->uuidMode,
		      v->numberMode);
    accept = normalizer.GetNormalized().Accept(handler);
    if (!accept) {
	PyErr_SetString(normalization_error, "Error converting the normalized JSON document to a Python object");
	return NULL;
    }
    
    if (PyErr_Occurred()) {
        Py_XDECREF(handler.root);
        return NULL;
    }
    
    return handler.root;
}


static void normalizer_dealloc(PyObject* self)
{
    NormalizerObject* s = (NormalizerObject*) self;
    if (s->objectHook)
	Py_DECREF(s->objectHook);
    delete s->schema;
    Py_TYPE(self)->tp_free(self);
}


static PyObject* normalizer_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject* jsonObject;
    PyObject* objectHook = NULL;
    PyObject* numberModeObj = NULL;
    unsigned numberMode = NM_NAN;
    PyObject* datetimeModeObj = NULL;
    unsigned datetimeMode = DM_NONE;
    PyObject* uuidModeObj = NULL;
    unsigned uuidMode = UM_NONE;
    PyObject* bytesModeObj = NULL;
    unsigned bytesMode = BM_SCALAR;
    PyObject* iterableModeObj = NULL;
    unsigned iterableMode = IM_ANY_ITERABLE;
    PyObject* mappingModeObj = NULL;
    unsigned mappingMode = MM_ANY_MAPPING;
    PyObject* yggdrasilModeObj = NULL;
    unsigned yggdrasilMode = YM_BASE64;
    int allowNan = -1;
    static char const* kwlist[] = {
	"schema",
        "object_hook",
        "number_mode",
        "datetime_mode",
        "uuid_mode",
        "bytes_mode",
        "iterable_mode",
        "mapping_mode",
	"yggdrasil_mode",

        /* compatibility with stdlib json */
        "allow_nan",

        NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|$OOOOOOOOp:Normalizer",
                                     (char**) kwlist,
				     &jsonObject,
                                     &objectHook,
                                     &numberModeObj,
                                     &datetimeModeObj,
                                     &uuidModeObj,
				     &bytesModeObj,
				     &iterableModeObj,
				     &mappingModeObj,
				     &yggdrasilModeObj,
                                     &allowNan))
        return NULL;

    if (objectHook && !PyCallable_Check(objectHook)) {
        if (objectHook == Py_None) {
            objectHook = NULL;
        } else {
            PyErr_SetString(PyExc_TypeError, "object_hook is not callable");
            return NULL;
        }
    }

    if (!accept_number_mode_arg(numberModeObj, allowNan, numberMode))
        return NULL;

    if (!accept_datetime_mode_arg(datetimeModeObj, datetimeMode))
        return NULL;

    if (!accept_uuid_mode_arg(uuidModeObj, uuidMode))
        return NULL;

    if (!accept_bytes_mode_arg(bytesModeObj, bytesMode))
        return NULL;

    if (!accept_iterable_mode_arg(iterableModeObj, iterableMode))
        return NULL;

    if (!accept_mapping_mode_arg(mappingModeObj, mappingMode))
        return NULL;

    if (!accept_yggdrasil_mode_arg(yggdrasilModeObj, yggdrasilMode))
        return NULL;

    Document d;
    if (!python2document(jsonObject, d, numberMode, datetimeMode,
			 uuidMode, bytesMode, iterableMode,
			 mappingMode, yggdrasilMode, 0, true))
	return NULL;

    NormalizerObject* v = (NormalizerObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;

    v->schema = new SchemaDocument(d);
    if (objectHook)
	Py_INCREF(objectHook);
    v->objectHook = objectHook;
    v->numberMode = numberMode;
    v->datetimeMode = datetimeMode;
    v->uuidMode = uuidMode;
    v->bytesMode = bytesMode;
    v->iterableMode = iterableMode;
    v->mappingMode = mappingMode;
    v->yggdrasilMode = yggdrasilMode;
    v->expectsString = check_expectsString(d);

    return (PyObject*) v;
}


static PyObject* normalizer_normalize(PyObject* self, PyObject* args, PyObject* kwargs)
{ return normalizer_call(self, args, kwargs); }


static PyObject* normalizer_validate(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject* jsonObject;

    if (!PyArg_ParseTuple(args, "O", &jsonObject))
        return NULL;

    NormalizerObject* v = (NormalizerObject*) self;
    Document d;
    bool isEmptyString = false;
    if (!python2document(jsonObject, d, v->numberMode, v->datetimeMode,
			 v->uuidMode, v->bytesMode, v->iterableMode,
			 v->mappingMode, v->yggdrasilMode, v->expectsString,
			 false, false, &isEmptyString))
	return NULL;

    SchemaValidator validator(*(v->schema));
    bool accept;

    if (validator.RequiresPython() || d.RequiresPython()) {
	accept = d.Accept(validator);
    } else {
	Py_BEGIN_ALLOW_THREADS
	accept = d.Accept(validator);
	Py_END_ALLOW_THREADS
    }

    if (!accept) {
	if (isEmptyString) {
	    PyErr_SetString(decode_error, "Invalid empty JSON document");
	    return NULL;
	}
	set_validation_error(validator);
        return NULL;
    }

    if (validator.GetInvalidSchemaCode() == kValidateWarnings)
	set_validation_error(validator, validation_warning, true);
    
    Py_RETURN_NONE;
}

static PyObject* normalizer_compare(PyObject* self, PyObject* args, PyObject* kwargs)
{
    bool dontRaise = false;
    if (kwargs) {
	PyObject* dontRaiseObject = PyDict_GetItemString(kwargs, "dont_raise");
	if (dontRaiseObject != NULL) {
	    if (dontRaiseObject == Py_False)
		dontRaise = false;
	    else if (dontRaiseObject == Py_True)
		dontRaise = true;
	    if (PyDict_DelItemString(kwargs, "dont_raise") < 0)
		return NULL;
	}
    }
    PyObject* validator2 = normalizer_new(&Normalizer_Type, args, kwargs);
    if (validator2 == NULL)
	return NULL;

    SchemaValidator v1(*((NormalizerObject*)self)->schema);
    SchemaValidator v2(*((NormalizerObject*)validator2)->schema);
    bool accept;
    if (v1.RequiresPython() || v2.RequiresPython()) {
	accept = v1.Compare(v2);
    } else {
	Py_BEGIN_ALLOW_THREADS
	accept = v1.Compare(v2);
	Py_END_ALLOW_THREADS
    }
    Py_DECREF(validator2);
    if (!accept) {
	if (dontRaise) {
	    Py_INCREF(Py_False);
	    return Py_False;
	} else {
	    set_validation_error(v1, comparison_error);
	    return NULL;
	}
    }

    Py_INCREF(Py_True);
    return Py_True;
    
}


static PyObject* normalizer_check_schema(PyObject*, PyObject* args, PyObject* kwargs)
{ return validator_check_schema((PyObject*)(&Validator_Type), args, kwargs); }


static PyObject* normalizer_generate_data(PyObject* self, PyObject*, PyObject*)
{
    Document d;
    NormalizerObject* v = (NormalizerObject*) self;
    SchemaNormalizer normalizer(*v->schema);
    bool accept = normalizer.GenerateData(d);
    if (!accept) {
	set_validation_error(normalizer, generate_error);
	return NULL;
    }

    PyHandler handler(NULL, v->objectHook, v->datetimeMode, v->uuidMode,
		      v->numberMode);
    accept = d.Accept(handler);
    if (!accept) {
	PyErr_SetString(generate_error, "Error converting the generated JSON document to a Python object");
	return NULL;
    }
    
    if (PyErr_Occurred()) {
        Py_XDECREF(handler.root);
        return NULL;
    }
    
    return handler.root;
}


PyDoc_STRVAR(normalize_docstring,
             "normalize(obj, schema, object_hook=None, number_mode=None,"
	     " datetime_mode=None, uuid_mode=None, bytes_mode=BM_SCALAR,"
	     " iterable_mode=IM_ANY_ITERABLE, mapping_mode=MM_ANY_MAPPING,"
	     " allow_nan=True, relative_path_root=None)\n"
             "\n"
	     "Normalize a Python object against a JSON schema.");


static PyObject*
normalize(PyObject* self, PyObject* args, PyObject* kwargs)
{

    if (!PyTuple_Check(args))
	return NULL;

    Py_ssize_t nargs = PyTuple_Size(args);
    if (nargs != 2)
	return NULL;
    PyObject* normalizer_args = PyTuple_New(nargs - 1);
    for (Py_ssize_t i = 1; i < nargs; i++) {
	PyObject* iarg = PyTuple_GetItem(args, i);
	if (iarg == NULL) {
	    Py_DECREF(normalizer_args);
	    return NULL;
	}
	Py_INCREF(iarg);
	if (PyTuple_SetItem(normalizer_args, i - 1, iarg) < 0) {
	    Py_DECREF(iarg);
	    Py_DECREF(normalizer_args);
	    return NULL;
	}
    }
			
    PyObject* relativePathRootObj = NULL;
    if (kwargs != NULL)
	relativePathRootObj = PyDict_GetItemString(kwargs, "relative_path_root");
    PyObject* call_kwargs = NULL;
    if (relativePathRootObj != NULL) {
	call_kwargs = PyDict_New();
	if (PyDict_SetItemString(call_kwargs, "relative_path_root",
				 relativePathRootObj) < 0) {
	    Py_DECREF(normalizer_args);
	    Py_DECREF(call_kwargs);
	    return NULL;
	}
	if (PyDict_DelItemString(kwargs, "relative_path_root") < 0) {
	    Py_DECREF(normalizer_args);
	    Py_DECREF(call_kwargs);
	    return NULL;
	}
    }
			
    PyObject* normalizer = normalizer_new(&Normalizer_Type, normalizer_args, kwargs);
    Py_DECREF(normalizer_args);
    if (normalizer == NULL) {
	Py_XDECREF(call_kwargs);
	return NULL;
    }

    PyObject* instance = PyTuple_GetItem(args, 0);
    if (instance == NULL) {
	Py_XDECREF(call_kwargs);
	Py_DECREF(normalizer);
	return NULL;
    }
    PyObject* call_args = PyTuple_Pack(1, instance);
    PyObject* out = normalizer_call(normalizer, call_args, call_kwargs);
    Py_DECREF(call_args);
    Py_XDECREF(call_kwargs);
    Py_DECREF(normalizer);
    return out;
}


////////////
// Module //
////////////

static PyObject*
add_submodule(PyObject* m, const char* cname, PyModuleDef* module_def) {
    PyObject *name = PyUnicode_FromString(cname);
    if (name == NULL)
	return NULL;
    // Mock a ModuleSpec object just good enough for PyModule_FromDefAndSpec():
    // an object with just a name attribute.
    //
    // _imp.__spec__ is overridden by importlib._bootstrap._instal() anyway.
// #ifdef _PyNamespace_New
//     PyObject *attrs = Py_BuildValue("{sO}", "name", name);
//     if (attrs == NULL)
// 	return NULL;
//     PyObject *spec = _PyNamespace_New(attrs);
//     Py_DECREF(attrs);
// #else
    PyObject* importlib = PyImport_ImportModule("importlib");
    if (importlib == NULL)
	return NULL;
    PyObject* machinery = PyObject_GetAttrString(importlib, "machinery");
    Py_DECREF(importlib);
    if (machinery == NULL)
	return NULL;
    PyObject* ModuleSpecCls = PyObject_GetAttrString(machinery, "ModuleSpec");
    Py_DECREF(machinery);
    if (ModuleSpecCls == NULL)
	return NULL;
    PyObject* args = PyTuple_Pack(2, name, Py_None);
    if (args == NULL)
	return NULL;
    PyObject* spec = PyObject_Call(ModuleSpecCls, args, NULL);
    Py_DECREF(ModuleSpecCls);
    Py_DECREF(args);
// #endif
    Py_DECREF(name);
    if (spec == NULL)
	return NULL;
    PyObject* submodule = PyModule_FromDefAndSpec(module_def, spec);
    Py_DECREF(spec);
    if (submodule == NULL)
	return NULL;
    if (PyModule_ExecDef(submodule, module_def) < 0)
	return NULL;
    Py_INCREF(submodule);
    if (PyModule_AddObject(m, cname, submodule) < 0) {
	Py_DECREF(submodule);
	return NULL;
    }
    PyObject *moduleDict = PyImport_GetModuleDict();
    if (moduleDict == NULL)
	return NULL;
    char fullname[200] = "";
    int n = snprintf(fullname, 200, "rapidjson.%s", cname);
    if ((n < 0) || (n > 200))
	return NULL;
    if (PyDict_SetItemString(moduleDict, fullname, submodule) < 0)
	return NULL;
    return submodule;
}


static PyMethodDef functions[] = {
    {"loads", (PyCFunction) loads, METH_VARARGS | METH_KEYWORDS,
     loads_docstring},
    {"load", (PyCFunction) load, METH_VARARGS | METH_KEYWORDS,
     load_docstring},
    {"dumps", (PyCFunction) dumps, METH_VARARGS | METH_KEYWORDS,
     dumps_docstring},
    {"dump", (PyCFunction) dump, METH_VARARGS | METH_KEYWORDS,
     dump_docstring},
    {"validate", (PyCFunction) validate, METH_VARARGS | METH_KEYWORDS,
     validate_docstring},
    {"normalize", (PyCFunction) normalize, METH_VARARGS | METH_KEYWORDS,
     normalize_docstring},
    {"encode_schema", (PyCFunction) encode_schema,
     METH_VARARGS | METH_KEYWORDS,
     encode_schema_docstring},
    {"get_metaschema", (PyCFunction) rj_get_metaschema,
     METH_VARARGS | METH_KEYWORDS,
     get_metaschema_docstring},
    {"compare_schemas", (PyCFunction) compare_schemas,
     METH_VARARGS | METH_KEYWORDS,
     compare_schemas_docstring},
    {"generate_data", (PyCFunction) generate_data,
     METH_VARARGS | METH_KEYWORDS,
     generate_data_docstring},
    {"as_pure_json", (PyCFunction) as_pure_json,
     METH_VARARGS | METH_KEYWORDS,
     as_pure_json_docstring},
    {NULL, NULL, 0, NULL} /* sentinel */
};


static int
module_exec(PyObject* m)
{
    PyObject* datetimeModule;
    PyObject* decimalModule;
    PyObject* uuidModule;

    if (PyType_Ready(&Decoder_Type) < 0)
        return -1;

    if (PyType_Ready(&Encoder_Type) < 0)
        return -1;

    if (PyType_Ready(&Validator_Type) < 0)
        return -1;

    if (PyType_Ready(&Normalizer_Type) < 0)
        return -1;

    if (PyType_Ready(&RawJSON_Type) < 0)
        return -1;

    PyDateTime_IMPORT;
    if(!PyDateTimeAPI)
        return -1;

    datetimeModule = PyImport_ImportModule("datetime");
    if (datetimeModule == NULL)
        return -1;

    decimalModule = PyImport_ImportModule("decimal");
    if (decimalModule == NULL)
        return -1;

    decimal_type = PyObject_GetAttrString(decimalModule, "Decimal");
    Py_DECREF(decimalModule);

    if (decimal_type == NULL)
        return -1;

    timezone_type = PyObject_GetAttrString(datetimeModule, "timezone");
    Py_DECREF(datetimeModule);

    if (timezone_type == NULL)
        return -1;

    timezone_utc = PyObject_GetAttrString(timezone_type, "utc");
    if (timezone_utc == NULL)
        return -1;

    uuidModule = PyImport_ImportModule("uuid");
    if (uuidModule == NULL)
        return -1;

    uuid_type = PyObject_GetAttrString(uuidModule, "UUID");
    Py_DECREF(uuidModule);

    if (uuid_type == NULL)
        return -1;

    astimezone_name = PyUnicode_InternFromString("astimezone");
    if (astimezone_name == NULL)
        return -1;

    hex_name = PyUnicode_InternFromString("hex");
    if (hex_name == NULL)
        return -1;

    timestamp_name = PyUnicode_InternFromString("timestamp");
    if (timestamp_name == NULL)
        return -1;

    total_seconds_name = PyUnicode_InternFromString("total_seconds");
    if (total_seconds_name == NULL)
        return -1;

    utcoffset_name = PyUnicode_InternFromString("utcoffset");
    if (utcoffset_name == NULL)
        return -1;

    is_infinite_name = PyUnicode_InternFromString("is_infinite");
    if (is_infinite_name == NULL)
        return -1;

    is_nan_name = PyUnicode_InternFromString("is_nan");
    if (is_infinite_name == NULL)
        return -1;

    minus_inf_string_value = PyUnicode_InternFromString("-Infinity");
    if (minus_inf_string_value == NULL)
        return -1;

    nan_string_value = PyUnicode_InternFromString("nan");
    if (nan_string_value == NULL)
        return -1;

    plus_inf_string_value = PyUnicode_InternFromString("+Infinity");
    if (plus_inf_string_value == NULL)
        return -1;

    start_object_name = PyUnicode_InternFromString("start_object");
    if (start_object_name == NULL)
        return -1;

    end_object_name = PyUnicode_InternFromString("end_object");
    if (end_object_name == NULL)
        return -1;

    default_name = PyUnicode_InternFromString("default");
    if (default_name == NULL)
        return -1;

    end_array_name = PyUnicode_InternFromString("end_array");
    if (end_array_name == NULL)
        return -1;

    string_name = PyUnicode_InternFromString("string");
    if (string_name == NULL)
        return -1;

    read_name = PyUnicode_InternFromString("read");
    if (read_name == NULL)
        return -1;

    write_name = PyUnicode_InternFromString("write");
    if (write_name == NULL)
        return -1;

    encoding_name = PyUnicode_InternFromString("encoding");
    if (encoding_name == NULL)
        return -1;

#define STRINGIFY(x) XSTRINGIFY(x)
#define XSTRINGIFY(x) #x

    if (PyModule_AddIntConstant(m, "DM_NONE", DM_NONE)
        || PyModule_AddIntConstant(m, "DM_ISO8601", DM_ISO8601)
        || PyModule_AddIntConstant(m, "DM_UNIX_TIME", DM_UNIX_TIME)
        || PyModule_AddIntConstant(m, "DM_ONLY_SECONDS", DM_ONLY_SECONDS)
        || PyModule_AddIntConstant(m, "DM_IGNORE_TZ", DM_IGNORE_TZ)
        || PyModule_AddIntConstant(m, "DM_NAIVE_IS_UTC", DM_NAIVE_IS_UTC)
        || PyModule_AddIntConstant(m, "DM_SHIFT_TO_UTC", DM_SHIFT_TO_UTC)

        || PyModule_AddIntConstant(m, "UM_NONE", UM_NONE)
        || PyModule_AddIntConstant(m, "UM_HEX", UM_HEX)
        || PyModule_AddIntConstant(m, "UM_CANONICAL", UM_CANONICAL)

        || PyModule_AddIntConstant(m, "NM_NONE", NM_NONE)
        || PyModule_AddIntConstant(m, "NM_NAN", NM_NAN)
        || PyModule_AddIntConstant(m, "NM_DECIMAL", NM_DECIMAL)
        || PyModule_AddIntConstant(m, "NM_NATIVE", NM_NATIVE)

        || PyModule_AddIntConstant(m, "PM_NONE", PM_NONE)
        || PyModule_AddIntConstant(m, "PM_COMMENTS", PM_COMMENTS)
        || PyModule_AddIntConstant(m, "PM_TRAILING_COMMAS", PM_TRAILING_COMMAS)

        || PyModule_AddIntConstant(m, "BM_NONE", BM_NONE)
        || PyModule_AddIntConstant(m, "BM_UTF8", BM_UTF8)
        || PyModule_AddIntConstant(m, "BM_SCALAR", BM_SCALAR)

        || PyModule_AddIntConstant(m, "WM_COMPACT", WM_COMPACT)
        || PyModule_AddIntConstant(m, "WM_PRETTY", WM_PRETTY)
        || PyModule_AddIntConstant(m, "WM_SINGLE_LINE_ARRAY", WM_SINGLE_LINE_ARRAY)

        || PyModule_AddIntConstant(m, "IM_ANY_ITERABLE", IM_ANY_ITERABLE)
        || PyModule_AddIntConstant(m, "IM_ONLY_LISTS", IM_ONLY_LISTS)

        || PyModule_AddIntConstant(m, "MM_ANY_MAPPING", MM_ANY_MAPPING)
        || PyModule_AddIntConstant(m, "MM_ONLY_DICTS", MM_ONLY_DICTS)
        || PyModule_AddIntConstant(m, "MM_COERCE_KEYS_TO_STRINGS",
                                   MM_COERCE_KEYS_TO_STRINGS)
        || PyModule_AddIntConstant(m, "MM_SKIP_NON_STRING_KEYS", MM_SKIP_NON_STRING_KEYS)
        || PyModule_AddIntConstant(m, "MM_SORT_KEYS", MM_SORT_KEYS)
	
	|| PyModule_AddIntConstant(m, "YM_BASE64", YM_BASE64)
	|| PyModule_AddIntConstant(m, "YM_READABLE", YM_READABLE)
	|| PyModule_AddIntConstant(m, "YM_PICKLE", YM_PICKLE)

	|| PyModule_AddIntConstant(m, "SIZE_OF_SIZE_T", SIZE_OF_SIZE_T)

        || PyModule_AddStringConstant(m, "__version__",
                                      STRINGIFY(PYTHON_RAPIDJSON_VERSION))
        || PyModule_AddStringConstant(m, "__author__",
                                      "Ken Robbins <ken@kenrobbins.com>"
                                      ", Lele Gaifax <lele@metapensiero.it>")
        || PyModule_AddStringConstant(m, "__rapidjson_version__",
                                      RAPIDJSON_VERSION_STRING)
#ifdef RAPIDJSON_EXACT_VERSION
        || PyModule_AddStringConstant(m, "__rapidjson_exact_version__",
                                      STRINGIFY(RAPIDJSON_EXACT_VERSION))
#endif
        )
        return -1;

    Py_INCREF(&Decoder_Type);
    if (PyModule_AddObject(m, "Decoder", (PyObject*) &Decoder_Type) < 0) {
        Py_DECREF(&Decoder_Type);
        return -1;
    }

    Py_INCREF(&Encoder_Type);
    if (PyModule_AddObject(m, "Encoder", (PyObject*) &Encoder_Type) < 0) {
        Py_DECREF(&Encoder_Type);
        return -1;
    }

    Py_INCREF(&Validator_Type);
    if (PyModule_AddObject(m, "Validator", (PyObject*) &Validator_Type) < 0) {
        Py_DECREF(&Validator_Type);
        return -1;
    }

    Py_INCREF(&Normalizer_Type);
    if (PyModule_AddObject(m, "Normalizer", (PyObject*) &Normalizer_Type) < 0) {
        Py_DECREF(&Normalizer_Type);
        return -1;
    }

    Py_INCREF(&RawJSON_Type);
    if (PyModule_AddObject(m, "RawJSON", (PyObject*) &RawJSON_Type) < 0) {
        Py_DECREF(&RawJSON_Type);
        return -1;
    }

    validation_error = PyErr_NewException("rapidjson.ValidationError",
                                          PyExc_ValueError, NULL);
    if (validation_error == NULL)
        return -1;
    Py_INCREF(validation_error);
    if (PyModule_AddObject(m, "ValidationError", validation_error) < 0) {
        Py_DECREF(validation_error);
        return -1;
    }

    validation_warning = PyErr_NewException("rapidjson.ValidationWarning",
					       PyExc_Warning, NULL);
    if (validation_warning == NULL)
        return -1;
    Py_INCREF(validation_warning);
    if (PyModule_AddObject(m, "ValidationWarning", validation_warning) < 0) {
        Py_DECREF(validation_warning);
        return -1;
    }
    
    normalization_error = PyErr_NewException("rapidjson.NormalizationError",
					     PyExc_ValueError, NULL);
    if (normalization_error == NULL)
        return -1;
    Py_INCREF(normalization_error);
    if (PyModule_AddObject(m, "NormalizationError", normalization_error) < 0) {
        Py_DECREF(normalization_error);
        return -1;
    }

    normalization_warning = PyErr_NewException("rapidjson.NormalizationWarning",
					       PyExc_Warning, NULL);
    if (normalization_warning == NULL)
        return -1;
    Py_INCREF(normalization_warning);
    if (PyModule_AddObject(m, "NormalizationWarning", normalization_warning) < 0) {
        Py_DECREF(normalization_warning);
        return -1;
    }
    
    decode_error = PyErr_NewException("rapidjson.JSONDecodeError",
                                      PyExc_ValueError, NULL);
    if (decode_error == NULL)
        return -1;
    Py_INCREF(decode_error);
    if (PyModule_AddObject(m, "JSONDecodeError", decode_error) < 0) {
        Py_DECREF(decode_error);
        return -1;
    }

    comparison_error = PyErr_NewException("rapidjson.ComparisonError",
					  PyExc_ValueError, NULL);
    if (comparison_error == NULL)
	return -1;
    Py_INCREF(comparison_error);
    if (PyModule_AddObject(m, "ComparisonError", comparison_error) < 0) {
	Py_DECREF(comparison_error);
	return -1;
    }

    generate_error = PyErr_NewException("rapidjson.GenerateError",
					  PyExc_ValueError, NULL);
    if (generate_error == NULL)
	return -1;
    Py_INCREF(generate_error);
    if (PyModule_AddObject(m, "GenerateError", generate_error) < 0) {
	Py_DECREF(generate_error);
	return -1;
    }

    PyObject* units_submodule_def = PyInit_units();
    if (units_submodule_def == NULL)
	return -1;
    units_submodule = add_submodule(m, "units", (PyModuleDef*)units_submodule_def);
    if (units_submodule == NULL) {
	Py_DECREF(units_submodule_def);
	return -1;
    }

    PyObject* geom_submodule_def = PyInit_geom();
    if (geom_submodule_def == NULL)
	return -1;
    geom_submodule = add_submodule(m, "geometry", (PyModuleDef*)geom_submodule_def);
    if (geom_submodule == NULL) {
	Py_DECREF(geom_submodule_def);
	return -1;
    }

    return 0;
}


static struct PyModuleDef_Slot slots[] = {
    {Py_mod_exec, (void*) module_exec},
    {0, NULL}
};


static PyModuleDef module = {
    PyModuleDef_HEAD_INIT,      /* m_base */
    "rapidjson",                /* m_name */
    PyDoc_STR("Fast, simple JSON encoder and decoder. Based on RapidJSON C++ library."),
    0,                          /* m_size */
    functions,                  /* m_methods */
    slots,                      /* m_slots */
    NULL,                       /* m_traverse */
    NULL,                       /* m_clear */
    NULL                        /* m_free */
};


PyMODINIT_FUNC
PyInit_rapidjson()
{
    import_array();
    import_umath();
    PyObject* out = PyModuleDef_Init(&module);
    return out;
}
