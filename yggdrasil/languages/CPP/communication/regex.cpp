//
// Created by friedel on 8/30/22.
//

#include "regex.hpp"

/*!
  @brief Find first match to regex.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @param[out] sind size_t index where match begins.
  @param[out] eind size_t index where match ends.
  @return int Number of matches found. -1 is returned if the regex could not be
  compiled.
*/
int find_match(const char *regex_text, const char *to_match,
               size_t *sind, size_t *eind) {
    int ret;
    int n_match = 0;
    regex_t r;
    // Compile
    ret = compile_regex(&r, regex_text);
    if (ret)
        return -1;
    // Loop until string done
    const char * p = to_match;
    const size_t n_sub_matches = 10;
    regmatch_t m[n_sub_matches];
    int nomatch = regexec(&r, p, n_sub_matches, m, 0);
    if (!(nomatch)) {
        *sind = m[0].rm_so;
        *eind = m[0].rm_eo;
        n_match++;
    }
    regfree(&r);
    return n_match;
}

/*!
  @brief Create a regex from a character array.
  Adapted from https://www.lemoda.net/c/unix-regex/
  @param[out] r pointer to regex_t. Resutling regex expression.
  @param[in] regex_text constant character pointer to text that should be
  compiled.
  @return static int Success or failure of compilation.
*/
bool compile_regex (regex_t * r, const char * regex_text)
{
    int status = regcomp (r, regex_text, REG_EXTENDED);//|REG_NEWLINE);
    if (status != 0) {
        char error_message[2048];
        regerror (status, r, error_message, 2048);
        printf ("Regex error compiling '%s': %s\n",
                regex_text, error_message);
        return false;
    }
    return true;
}

