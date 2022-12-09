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


/*! 
  @brief C++ wrapper to get a pointer from the variable argument list and
    advance the position.
  @param[in] ap Variable argument list.
  @param[in] allow_null If 0, an error will be raised if the
    selected pointer is null, otherwise the null pointer will be returned.
  @returns Popped pointer.
*/
static inline
void* pop_va_list_ptr_cpp(va_list_t *ap, int allow_null = 0) {
  void *out = NULL;
  if (ap->nargs[0] == 0) {
    ygglog_throw_error("pop_va_list_ptr_cpp: No more arguments");
  }
  if (ap->ptrs == NULL) {
    ygglog_throw_error("pop_va_list_ptr_cpp: Variable argument list is not stored in pointers.");
  }
  out = ap->ptrs[ap->iptr];
  ap->iptr++;
  if (ap->nargs[0] > 0)
    ap->nargs[0]--;
  if ((out == NULL) && (allow_null == 0)) {
    ygglog_throw_error("pop_va_list_ptr_cpp: Argument %d is NULL.", ap->iptr - 1);
  }
  return out;
};


/*!
  @brief C++ wrapper to get a pointer to a pointer from the variable
    argument list and advance the position.
  @param[in] ap Variable argument list.
  @param[in] allow_null If 0, an error will be raised if the
    selected pointer is null, otherwise the null pointer will be returned.
  @returns Popped pointer.
*/
static inline
void** pop_va_list_ptr_ref_cpp(va_list_t *ap, int allow_null = 0) {
  void **out = NULL;
  if (ap->nargs[0] == 0) {
    ygglog_throw_error("pop_va_list_ptr_ref_cpp: No more arguments");
  }
  if (ap->ptrs == NULL) {
    ygglog_throw_error("pop_va_list_ptr_ref_cpp: Variable argument list is not stored in pointers.");
  }
  out = ap->ptrs + ap->iptr;
  ap->iptr++;
  if (ap->nargs[0] > 0)
    ap->nargs[0]--;
  if ((out == NULL) || ((*out == NULL) && (allow_null == 0))) {
    ygglog_throw_error("pop_va_list_ptr_ref_cpp: Argument is NULL.");
  }
  return out;
};

/*! 
  @brief Pop a value from the variables argument list.
  @tparam T Type of value to pop.
  @param[in] ap Variable argument list.
  @param[out] dst Variable to assign the popped value to.
  @param[in] allow_null If 0, an error will be raised if the popped value's
    pointer is null. Otherwise the null pointer will be returned.
  @returns true if successful, false otherwise.
*/
template<typename T>
bool pop_va_list(va_list_t &ap, T*& dst, int allow_null = 0) {
  try {
    if (ap.nargs[0] == 0) {
      ygglog_throw_error("pop_va_list: No more arguments");
    }
    if (ap.ptrs) {
      dst = ((T*)pop_va_list_ptr_cpp(&ap, allow_null));
    } else {
      dst = va_arg(ap.va, T*);
      if (ap.nargs[0] > 0)
	ap.nargs[0]--;
    }
  } catch(...) {
    return false;
  }
  return true;
}
template<typename T>
bool pop_va_list(va_list_t &ap, T& dst, int allow_null = 0) {
  try {
    if (ap.nargs[0] == 0) {
      ygglog_throw_error("pop_va_list: No more arguments");
    }
    if (ap.ptrs) {
      dst = ((T*)pop_va_list_ptr_cpp(&ap, allow_null))[0];
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
    try {								\
      if (ap.nargs[0] == 0) {						\
	ygglog_throw_error("pop_va_list: No more arguments");		\
      }									\
      if (ap.ptrs) {							\
	dst = ((type*)pop_va_list_ptr_cpp(&ap, allow_null))[0];		\
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
POP_SPECIAL_(char, int)
POP_SPECIAL_(int8_t, int)
POP_SPECIAL_(int16_t, int)
POP_SPECIAL_(uint8_t, int)
POP_SPECIAL_(uint16_t, int)
POP_SPECIAL_(float, double)
#undef POP_SPECIAL_

/*! 
  @brief Skip a value from the variables argument list.
  @tparam T Type of value to skip.
  @param[in] ap Variable argument list.
  @param[in] pointers If True, a pointer value will be skipped.
  @returns true if successful, false otherwise.
*/
template<typename T>
bool skip_va_list(va_list_t &ap, bool pointers) {
  if (pointers) {
    T* tmp = NULL;
    T** tmp_ref = NULL;
    return pop_va_list_mem(ap, tmp, tmp_ref);
  } else {
    T tmp;
    return pop_va_list(ap, tmp);
  }
}

/*! 
  @brief Get a value from the variables argument list without removing any
    values.
  @tparam T Type of value to get.
  @param[in] ap Variable argument list.
  @param[out] dst Variable to assign the value to.
  @param[in] allow_null If 0, an error will be raised if the value's
    pointer is null. Otherwise the null pointer will be returned.
  @returns true if successful, false otherwise.
*/
template<typename T>
bool get_va_list(va_list_t &ap, T& dst, int allow_null = 0) {
  va_list_t ap_copy = copy_va_list(ap);
  return pop_va_list(ap_copy, dst, allow_null);
}

/*!
  @brief Assign to memory for a pointer retrieved from a variable argument
    list via pop_va_list_mem or get_va_list_mem.
  @tparam T Type of value to assign.
  @param[in] ap Variable argument list.
  @param[in,out] dst Pointer to memory that should be assigned.
  @param[in,out] dst_ref Pointer to dst that can be updated if dst is 
    reallocated.
  @param[in,out] dst_len Current number of elements allocated for in dst.
    This will be updated to the new number of elements in dst after assigment.
  @param[in] src Value(s) to assign to dst.
  @param[in] src_len Number of values in src.
  @param[in] allow_realloc If 1, dst will be reallocated if it is not large
    enough to contain the value(s) in src.
  @return true if successful, false otherwise.
 */
template<typename T>
bool set_va_list_mem(const va_list_t &ap,
		     T*& dst, T**& dst_ref, size_t& dst_len,
		     const T* src, const size_t src_len,
		     int allow_realloc = 0) {
  if (src_len > dst_len || dst == NULL) {
    if (!allow_realloc)
      ygglog_throw_error("set_va_list_mem: Buffer is not large enough");
    // if (!ap.for_fortran)
    dst = (T*)realloc(dst, src_len * sizeof(T));
    dst_ref[0] = dst;
  }
  dst_len = src_len;
  memcpy(dst, src, src_len * sizeof(T));
  return true;
}
template<>
bool set_va_list_mem(const va_list_t &ap,
		     char*& dst, char**& dst_ref, size_t& dst_len,
		     const char* src, const size_t src_len,
		     int allow_realloc) {
  if ((src_len + 1) > dst_len || dst == NULL) {
    if (!allow_realloc)
      ygglog_throw_error("set_va_list_mem: Buffer is not large enough");
    size_t src_len_alloc = src_len;
    if (!ap.for_fortran)
      src_len_alloc++;
    dst = (char*)realloc(dst, src_len_alloc * sizeof(char));
    dst_ref[0] = dst;
  }
  dst_len = src_len;
  memcpy(dst, src, src_len * sizeof(char));
  if (!ap.for_fortran)
    dst[src_len * sizeof(char)] = '\0';
  return true;
}
  
/*! 
  @brief Pop a pointer from the variables argument list.
  @tparam T Type of pointer to pop.
  @param[in] ap Variable argument list.
  @param[out] dst Variable that will be assigned the pointer to the
    underlying value.
  @param[out] dst_ref Variable that will be assigned the pointer to the
    address of the underlying value (the pointer to dst) so that the
    pointer may be updated if dst is reallocated.
  @param[in] allow_realloc If 1, the variable argument list is assumed to
    contain a pointer to the value address (such that the value may be
    reallocated).
  @returns true if successful, false otherwise.
*/
template<typename T>
bool pop_va_list_mem(va_list_t &ap, T*& dst, T**& dst_ref, int allow_realloc = 0) {
  try {
    if (ap.nargs[0] == 0) {
      ygglog_throw_error("set_va_list: No more arguments");
    }
    if (allow_realloc) {
      if (ap.ptrs) {
	dst_ref = (T**)pop_va_list_ptr_ref_cpp(&ap, 1);
      } else {
	dst_ref = va_arg(ap.va, T**);
	if (ap.nargs[0] > 0)
	  ap.nargs[0]--;
      }
      dst = dst_ref[0];
    } else {
      if (ap.ptrs) {
	dst = (T*)pop_va_list_ptr_cpp(&ap);
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

/*! 
  @brief Get a pointer from the variables argument list without removing any
    values.
  @tparam T Type of pointer to get.
  @param[in] ap Variable argument list.
  @param[out] dst Variable that will be assigned the pointer to the
    underlying value.
  @param[out] dst_ref Variable that will be assigned the pointer to the
    address of the underlying value (the pointer to dst) so that the
    pointer may be updated if dst is reallocated.
  @param[in] allow_realloc If 1, the variable argument list is assumed to
    contain a pointer to the value address (such that the value may be
    reallocated).
  @returns true if successful, false otherwise.
*/
template<typename T>
bool get_va_list_mem(va_list_t &ap, T*& dst, T**& dst_ref, int allow_realloc = 0) {
  va_list_t ap_copy = copy_va_list(ap);
  return pop_va_list_mem(ap_copy, dst, dst_ref, allow_realloc);
}

/*!
  @brief Assign to the next variable in a variable argument list.
  @tparam T Type of value to assign.
  @param[in] ap Variable argument list.
  @param[in] src Value to assign to the next variable in ap.
  @param[in] allow_realloc If 1, the destination variable will be assumed to
    be the address of a pointer and the memory indicated by the pointer will
    be reallocated if it is not large enough to contain the value in src.
  @returns true if successful, false otherwise.
 */
template<typename T>
bool set_va_list(va_list_t &ap, const T& src, int allow_realloc = 0) {
  try {
    T** p = NULL;
    T* arg = NULL;
    if (ap.nargs[0] == 0) {
      ygglog_throw_error("set_va_list: No more arguments");
    }
    if (!pop_va_list_mem(ap, arg, p, allow_realloc))
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
