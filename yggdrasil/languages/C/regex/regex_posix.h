/*! @brief Flag for checking if regex_posix has already been included.*/
#ifndef REGEX_POSIX_H_
#define REGEX_POSIX_H_

#include <regex.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*!
  @brief Create a regex from a character array.
  Adapted from https://www.lemoda.net/c/unix-regex/
  @param[out] r pointer to regex_t. Resutling regex expression.
  @param[in] regex_text constant character pointer to text that should be
  compiled.
  @return static int Success or failure of compilation.
*/
static inline
int compile_regex (regex_t * r, const char * regex_text)
{
  int status = regcomp (r, regex_text, REG_EXTENDED);//|REG_NEWLINE);
  if (status != 0) {
    char error_message[2048];
    regerror (status, r, error_message, 2048);
    printf ("Regex error compiling '%s': %s\n",
	    regex_text, error_message);
    return 1;
  }
  return 0;
};

/*!
  @brief Count the number of times a regular expression is matched in a string.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @return int Number of matches found. -1 is returned if the regex could not be
  compiled.
*/
static inline
int count_matches(const char *regex_text, const char *to_match) {
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
  while (1) {
    int nomatch = regexec(&r, p, n_sub_matches, m, 0);
    if (nomatch)
      break;
    n_match++;
    p += m[0].rm_eo;
  }
  regfree(&r);
  return n_match;
};


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
static inline
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
};


/*!
  @brief Find first match to regex and any sub-matches.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @param[out] sind size_t ** indices of where matches begin.
  @param[out] eind size_t ** indices of where matches ends.
  @return int Number of matches/submatches found. -1 is returned if the regex
  could not be compiled.
*/
static inline
int find_matches(const char *regex_text, const char *to_match,
		 size_t **sind, size_t **eind) {
  int ret;
  int n_match = 0;
  regex_t r;
  // Compile
  ret = compile_regex(&r, regex_text);
  if (ret)
    return -1;
  // Loop until string done
  const size_t n_sub_matches = 50;
  regmatch_t m[n_sub_matches];
  int nomatch = regexec(&r, to_match, n_sub_matches, m, 0);
  if (!(nomatch)) {
    // Count
    while (n_match < (int)n_sub_matches) {
      if ((m[n_match].rm_so == -1) && (m[n_match].rm_eo == -1)) {
	break;
      }
      n_match++;
    }
    // Realloc
    *sind = (size_t*)realloc(*sind, n_match*sizeof(size_t));
    *eind = (size_t*)realloc(*eind, n_match*sizeof(size_t));
    // Record
    int i;
    for (i = 0; i < n_match; i++) {
      (*sind)[i] = m[i].rm_so;
      (*eind)[i] = m[i].rm_eo;
    }
  }
  regfree(&r);
  return n_match;
};


/*!
  @brief Make a replacement of regex matches, ignoring captured substrings.
  @param[in,out] buf Characer pointer to buffer that replacements should be
  made to.
  @param[in] len_buf const size_t length of buf.
  @param[in] re Constant character pointer to regex string.
  @param[in] rp Constant character pointer to the replacement text.
  @param[in] nreplace Constant size_t number of replacements to make. If 0, all
  matches are replaced.
  @return int -1 on failure if the regex could not be compiled or the buffer 
  is not big enough to contain the result. If succesful, the new length of buf
  is returned.
 */
static inline
int regex_replace_nosub(char *buf, const size_t len_buf,
			const char *re, const char *rp,
			const size_t nreplace) {
  /* printf("regex_replace_nosub(%s, %s, %s)\n", buf, re, rp); */
  // Compile
  regex_t r;
  int ret = compile_regex(&r, re);
  if (ret)
    return -1;
  // Loop making replacements
  size_t len_rp = strlen(rp);
  char * p = buf;
  const size_t ngroups = r.re_nsub + 1;
  regmatch_t *m = (regmatch_t*)malloc(ngroups * sizeof(regmatch_t));
  size_t len_m, rem_s, rem_l, delta_siz;
  size_t cur_pos = 0;
  size_t cur_siz = strlen(buf);
  size_t creplace = 0;
  while (1) {
    if ((nreplace > 0) && (creplace >= nreplace)) {
      printf("regex_replace_nosub: Maximum of %d replacements reached\n",
      	     (int)creplace);
      break;
    }
    int nomatch = regexec(&r, p, ngroups, m, 0);
    if (nomatch) {
      /* printf("regex_replace_nosub: nomatch for %s in %s\n", re, p); */
      break;
    }
    // Ensure replacement will not exceed buffer
    len_m = m[0].rm_eo - m[0].rm_so;
    delta_siz = len_rp - len_m;
    if ((cur_siz + delta_siz + 1) > len_buf) {
      printf("regex_replace_nosub: Relacement will exceed buffer.\n");
      cur_siz = -1;
      break;
    }
    // Move trailing
    rem_l = cur_siz - (cur_pos + m[0].rm_eo);
    rem_s = m[0].rm_so + len_rp;
    memmove(p + rem_s, p + m[0].rm_eo, rem_l + 1);
    // Copy replacement
    strncpy(p + m[0].rm_so, rp, len_rp);
    // Advance
    p += rem_s;
    cur_pos += rem_s;
    cur_siz += delta_siz;
    creplace += 1;
  }
  /* printf("regex_replace_nosub() = %s\n", buf); */
  free(m);
  regfree(&r);
  return cur_siz;
};


/*!
  @brief Extract substring references from a string.
  @param[in] buf Constant character pointer to buffer that references should be
  extracted from.
  @param[out] refs Pointer to pointer to memory where reference numbers should
  be stored. This function will reallocate it to fit the number of references
  returned. (Should be freed by calling program.)
  @return int Number of refs found. -1 indicates an error.
*/
static inline
int get_subrefs(const char *buf, size_t **refs) {
  // Compile
  regex_t r;
  int ret = compile_regex(&r, "\\$([[:digit:]])");
  if (ret)
    return -1;
  // Allocate;
  const size_t ngroups = r.re_nsub + 1;
  if (ngroups != 2) {
    printf("ERROR: regex could not find subgroup\n");
    regfree(&r);
    return -1;
  }
  regmatch_t *m = (regmatch_t*)malloc(ngroups * sizeof(regmatch_t));
  // Prepare "bitmap"
  const size_t max_ref = 10; //99;
  size_t i;
  uint8_t *ref_bytes = (uint8_t*)malloc((max_ref + 1)*sizeof(uint8_t));
  for (i = 0; i <= max_ref; i++)
    ref_bytes[i] = 0;
  // Locate matches
  const char *p = buf;
  const size_t max_grp = 2;  // Digits in max_ref
  size_t igrp_len;
  char igrp[max_grp];
  size_t iref;
  while (1) {
    int nomatch = regexec(&r, p, ngroups, m, 0);
    if (nomatch) {
      break;
    }
    // Lone $ without digit
    /* printf("so = %d, eo = %d\n", m[1].rm_so, m[1].rm_eo); */
    if ((m[1].rm_so == -1) && (m[1].rm_eo == -1)) {
      p += m[0].rm_eo;
      continue;
    }
    // Substring
    igrp_len = m[1].rm_eo - m[1].rm_so;
    if (igrp_len > max_grp) {
      printf("Number longer than %d digits unlikely.\n", (int)max_grp);
      free(m);
      free(ref_bytes);
      regfree(&r);
      return -1;
    }
    strncpy(igrp, p + m[1].rm_so, igrp_len);
    igrp[igrp_len] = 0;
    // Extract ref number
    iref = atoi(igrp);
    if (iref > max_ref) {
      printf("Reference to substr %d exceeds limit (%d)\n",
	     (int)iref, (int)max_ref);
      free(m);
      free(ref_bytes);
      regfree(&r);
      return -1;
    }
    ref_bytes[iref] = 1;
    p += m[0].rm_eo;
  }
  // Get unique refs
  int nref = 0;
  for (i = 0; i <= max_ref; i++) {
    if (ref_bytes[i])
      nref++;
  }
  *refs = (size_t*)realloc(*refs, nref*sizeof(size_t));
  size_t ir;
  for (i = 0, ir = 0; i <= max_ref; i++) {
    if (ref_bytes[i]) {
      (*refs)[ir] = i;
      ir++;
    }
  }
  free(m);
  free(ref_bytes);
  regfree(&r);
  // printf("%d refs in %s\n", nref, buf);
  return nref;
};


/*!
  @brief Make a replacement of regex matches, allowing for captured substrings.
  @param[in,out] buf Characer pointer to buffer that replacements should be
  made to.
  @param[in] len_buf const size_t length of buf.
  @param[in] re Constant character pointer to regex string.
  @param[in] rp Constant character pointer to the replacement text.
  @param[in] nreplace Constant size_t number of replacements to make. If 0, all
  matches are replaced.
  @return int -1 on failure if the regex could not be compiled or the buffer 
  is not big enough to contain the result. If succesful, the new length of buf
  is returned.
 */
static inline
int regex_replace_sub(char *buf, const size_t len_buf,
		      const char *re, const char *rp,
		      const size_t nreplace) {
  // Compile
  regex_t r;
  int ret = compile_regex(&r, re);
  if (ret)
    return -1;
  // Loop making replacements
  char * p = buf;
  const size_t ngroups = r.re_nsub + 1;
  regmatch_t *m = (regmatch_t*)malloc(ngroups * sizeof(regmatch_t));
  char rp_sub[2*len_buf];
  char re_sub[len_buf];
  char igrp[len_buf];
  size_t len_m, rem_s, rem_l, delta_siz, len_rp;
  size_t cur_pos = 0;
  size_t cur_siz = strlen(buf);
  size_t creplace = 0;
  size_t i;
  int j;
  while (1) {
    if ((nreplace > 0) && (creplace >= nreplace)) {
      printf("regex_replace_nosub: Maximum of %d replacements reached\n",
	     (int)creplace);
      break;
    }
    int nomatch = regexec(&r, p, ngroups, m, 0);
    if (nomatch) {
      /* printf("regex_replace_sub: nomatch for %s in %s\n", re, p); */
      break;
    }
    // Get list of subrefs
    size_t *refs = NULL;
    int nref = get_subrefs(rp, &refs);
    if (nref < 0) {
      printf("Error gettings subrefs\n");
      free(m);
      regfree(&r);
      return -1;
    }
    // For each subref complete replacements
    strcpy(rp_sub, rp);
    for (j = 0; j < nref; j++) {
      i = refs[j];
      strcpy(igrp, p + m[i].rm_so);
      igrp[m[i].rm_eo - m[i].rm_so] = 0; // terminate
      sprintf(re_sub, "\\$%d", (int)i);
      ret = regex_replace_nosub(rp_sub, 2*len_buf, re_sub, igrp, 0);
      if (ret < 0) {
	printf("regex_replace_sub: Error replacing substring $%d.\n", (int)i);
	free(m);
	regfree(&r);
	return -1;
      }
    }
    // Ensure replacement will not exceed buffer
    len_rp = ret;
    len_m = m[0].rm_eo - m[0].rm_so;
    delta_siz = len_rp - len_m;
    if ((cur_siz + delta_siz + 1) > len_buf) {
      printf("regex_replace_sub: Relacement will exceed buffer.\n");
      free(m);
      regfree(&r);
      return -1;
    }
    // Move trailing
    rem_l = cur_siz - (cur_pos + m[0].rm_eo);
    rem_s = m[0].rm_so + len_rp;
    memmove(p + rem_s, p + m[0].rm_eo, rem_l + 1);
    // Copy replacement
    strncpy(p + m[0].rm_so, rp_sub, len_rp);
    // Advance
    p += m[0].rm_so + len_rp;
    cur_pos += m[0].rm_so + len_rp;
    cur_siz += delta_siz;
    creplace += 1;
  }
  free(m);
  regfree(&r);
  return (int)cur_siz;
};

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*REGEX_POSIX_H_*/
