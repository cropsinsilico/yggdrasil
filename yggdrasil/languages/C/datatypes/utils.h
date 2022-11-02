#ifndef DATATYPES_UTILS_H_
#define DATATYPES_UTILS_H_

#include "../tools.h"

#include <stdexcept>
#include <iostream>
#include <iomanip>
#include <map>
#include <vector>
#include <functional>
#include <cstring>


/*!
  @brief Throw an error and long it.
  @param[in] fmt char* Format string.
  @param[in] ... Parameters that should be formated using the format string.
 */
static inline
void ygglog_throw_error(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  yggError_va(fmt, ap);
  va_end(ap);
  throw std::exception();
};


/*! C++ wrapper to get a pointer from the variable argument list and
  advancing the position.
  @param[in] ap va_list_t Variable argument list.
  @param[in] allow_null int If 0, an error will be raised if the
  selected pointer is null, otherwise the null pointer will be returned.
  @returns void* Pointer.
*/
static inline
void* get_va_list_ptr_cpp(va_list_t *ap, int allow_null = 0) {
  void *out = NULL;
  if (ap->nargs[0] == 0) {
    ygglog_throw_error("get_va_list_ptr: No more arguments");
  }
  if (ap->ptrs == NULL) {
    ygglog_throw_error("get_va_list_ptr: Variable argument list is not stored in pointers.");
  }
  out = ap->ptrs[ap->iptr];
  ap->iptr++;
  if (ap->nargs[0] > 0)
    ap->nargs[0]--;
  if ((out == NULL) && (allow_null == 0)) {
    ygglog_throw_error("get_va_list_ptr: Argument %d is NULL.", ap->iptr - 1);
  }
  return out;
};


/*! C++ wrapper to get a pointer to a pointer from the variable
  argument list and advancing the position.
  @param[in] ap va_list_t Variable argument list.
  @param[in] allow_null int If 0, an error will be raised if the
  selected pointer is null, otherwise the null pointer will be returned.
  @returns void* Pointer.
*/
static inline
void** get_va_list_ptr_ref_cpp(va_list_t *ap, int allow_null = 0) {
  void **out = NULL;
  if (ap->nargs[0] == 0) {
    ygglog_throw_error("get_va_list_ptr_ref_cpp: No more arguments");
  }
  if (ap->ptrs == NULL) {
    ygglog_throw_error("get_va_list_ptr_ref: Variable argument list is not stored in pointers.");
  }
  out = ap->ptrs + ap->iptr;
  ap->iptr++;
  if (ap->nargs[0] > 0)
    ap->nargs[0]--;
  if (((out == NULL) || (*out == NULL)) && (allow_null == 0)) {
    ygglog_throw_error("get_va_list_ptr_ref: Argument is NULL.");
  }
  return out;
};

template<typename T>
bool pop_va_list(va_list_t &ap, T& dst, int allow_null = 0) {
  try {
    if (ap.nargs[0] == 0) {
      ygglog_throw_error("pop_va_list: No more arguments");
    }
    if (ap.ptrs) {
      dst = ((T*)get_va_list_ptr_cpp(&ap, allow_null))[0];
    } else {
      dst = va_arg(ap.va, T);
      if (ap.nargs[0] > 0)
	ap.nargs[0]--;
    }
  } catch(...) {
    return false;
  }
  return true;
}
#define POP_SPECIAL_(type, type_cast)					\
  template<>								\
  bool pop_va_list(va_list_t &ap, type& dst, int allow_null) {		\
    try {									\
      if (ap.nargs[0] == 0) {						\
	ygglog_throw_error("pop_va_list: No more arguments");		\
      }									\
      if (ap.ptrs) {							\
	dst = ((type*)get_va_list_ptr_cpp(&ap, allow_null))[0];		\
      } else {								\
	type_cast tmp;							\
	if (!pop_va_list(ap, tmp, allow_null))				\
	  return false;							\
	dst = (type)tmp;						\
      }									\
    } catch(...) {							\
      return false;							\
    }									\
    return true;							\
  }
POP_SPECIAL_(bool, int)
POP_SPECIAL_(int8_t, int)
POP_SPECIAL_(int16_t, int)
POP_SPECIAL_(uint8_t, int)
POP_SPECIAL_(uint16_t, int)
POP_SPECIAL_(float, double)
#undef POP_SPECIAL_

template<typename T>
bool get_va_list(va_list_t &ap, T& dst, int allow_null = 0) {
  va_list_t ap_copy = copy_va_list(ap);
  return pop_va_list(ap_copy, dst, allow_null);
}

template<typename T>
bool set_va_list_mem(T*& dst, T**& dst_ref, size_t& dst_len,
		     const T* src, const size_t src_len,
		     int allow_realloc = 0) {
  if (src_len > dst_len || dst == NULL) {
    if (!allow_realloc)
      ygglog_throw_error("set_va_list_mem: Buffer is not large enough");
    dst = (T*)realloc(dst, src_len * sizeof(T));
    dst_ref[0] = dst;
  }
  dst_len = src_len;
  memcpy(dst, src, src_len * sizeof(T));
  return true;
}
template<>
bool set_va_list_mem(char*& dst, char**& dst_ref, size_t& dst_len,
		     const char* src, const size_t src_len,
		     int allow_realloc) {
  if ((src_len + 1) > dst_len || dst == NULL) {
    if (!allow_realloc)
      ygglog_throw_error("set_va_list_mem: Buffer is not large enough");
    dst = (char*)realloc(dst, (src_len + 1) * sizeof(char));
    dst_ref[0] = dst;
  }
  dst_len = src_len;
  memcpy(dst, src, src_len * sizeof(char));
  dst[src_len * sizeof(char)] = '\0';
  return true;
}
  
template<typename T>
bool get_va_list_mem(va_list_t &ap, T*& dst, T**& dst_ref, int allow_realloc = 0) {
  try {
    if (ap.nargs[0] == 0) {
      ygglog_throw_error("set_va_list: No more arguments");
    }
    if (allow_realloc) {
      if (ap.ptrs) {
	dst_ref = (T**)get_va_list_ptr_ref_cpp(&ap);
      } else {
	dst_ref = va_arg(ap.va, T**);
	if (ap.nargs[0] > 0)
	  ap.nargs[0]--;
      }
      dst = dst_ref[0];
    } else {
      if (ap.ptrs) {
	dst = (T*)get_va_list_ptr_cpp(&ap);
      } else {
	dst = va_arg(ap.va, T*);
	if (ap.nargs[0] > 0)
	  ap.nargs[0]--;
      }
      dst_ref = &dst;
    }
  } catch(...) {
    return false;
  }
  return true;
}
template<typename T>
bool set_va_list(va_list_t &ap, T& src, int allow_realloc = 0) {
  try {
    T** p = NULL;
    T* arg = NULL;
    if (ap.nargs[0] == 0) {
      ygglog_throw_error("set_va_list: No more arguments");
    }
    if (!get_va_list_mem(ap, arg, p, allow_realloc))
      return false;
    if (allow_realloc) {
      if (ap.for_fortran) {
	arg = *p;
      } else {
	arg = (T*)realloc(*p, sizeof(T));
      }
      p[0] = arg;
    }
    arg[0] = src;
  } catch(...) {
    return false;
  }
  return true;
}


/*!
  @brief Count the number of times a regular expression is matched in a string.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @return size_t Number of matches found.
*/
static inline
size_t count_matches_raise(const char *regex_text, const char *to_match) {
  int out = count_matches(regex_text, to_match);
  if (out < 0) {
    ygglog_throw_error("count_matches_raise: Error in count_matches. regex = '%s', string = '%s'",
                       regex_text, to_match);
  }
  return (size_t)out;
};

/*!
  @brief Find first match to regex and any sub-matches.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @param[out] sind size_t ** indices of where matches begin.
  @param[out] eind size_t ** indices of where matches ends.
  @return size_t Number of matches/submatches found.
*/
size_t find_matches_raise(const char *regex_text, const char *to_match,
        size_t **sind, size_t **eind) {
  int out = find_matches(regex_text, to_match, sind, eind);
  if (out < 0) {
    ygglog_throw_error("find_matches_raise: Error in find_matches. regex = '%s', string = '%s'",
                       regex_text, to_match);
  }
  return (size_t)out;
};

/*!
  @brief Find first match to regex.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @param[out] sind size_t index where match begins.
  @param[out] eind size_t index where match ends.
  @return size_t Number of matches found. -1 is returned if the regex could not be
  compiled.
*/
size_t find_match_raise(const char *regex_text, const char *to_match,
            size_t *sind, size_t *eind) {
  int out = find_match(regex_text, to_match, sind, eind);
  if (out < 0) {
    ygglog_throw_error("find_match_raise: Error in find_match. regex = '%s', string = '%s'",
                       regex_text, to_match);
  }
  return (size_t)out;
};

/*!
  @brief String comparison structure.
 */
struct strcomp : public std::binary_function<const char*, const char*, bool> 
{
  /*!
    @brief Comparison operator.
    @param[in] a char const * First string for comparison.
    @param[in] b char const * Second string for comparison.
    @returns bool true if the strings are equivalent, false otherwise.
   */
  bool operator()(const char *a, const char *b) const
  {
    return std::strcmp(a, b) < 0;
  }
};

#endif /*DATATYPES_UTILS_H_*/
// Local Variables:
// mode: c++
// End:
