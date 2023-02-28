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
static inline
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
static inline
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
