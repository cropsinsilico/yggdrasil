#ifndef YGGINTERFACEP_REGEX_HPP
#define YGGINTERFACEP_REGEX_HPP

#include <regex.h>
#include <stdio.h>

bool compile_regex (regex_t * r, const char * regex_text);
int find_match(const char *regex_text, const char *to_match,
               size_t *sind, size_t *eind);


#endif //YGGINTERFACEP_REGEX_HPP
