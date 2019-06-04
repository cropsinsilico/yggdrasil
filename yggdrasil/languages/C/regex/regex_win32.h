/*! @brief Flag for checking if regex_win32 has already been included.*/
#ifndef REGEX_WIN32_H_
#define REGEX_WIN32_H_

#ifdef __cplusplus
#define EXTERNC extern "C"
#else
#define EXTERNC
#endif

EXTERNC int count_matches(const char *regex_text, const char *to_match);
EXTERNC int find_matches(const char *regex_text, const char *to_match,
			 size_t **sind, size_t **eind);
EXTERNC int find_match(const char *regex_text, const char *to_match,
		       size_t *sind, size_t *eind);
EXTERNC int regex_replace_nosub(char *buf, const size_t len_buf,
				const char *re, const char *rp,
				const size_t nreplace);
EXTERNC int get_subrefs(const char *buf, size_t **refs);
EXTERNC int regex_replace_sub(char *buf, const size_t len_buf,
			      const char *re, const char *rp,
			      const size_t nreplace);

#undef EXTERNC
#endif /*REGEX_WIN32_H_*/
