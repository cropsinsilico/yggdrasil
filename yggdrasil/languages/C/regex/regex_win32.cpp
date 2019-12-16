#ifndef _CRT_SECURE_NO_WARNINGS
#define _CRT_SECURE_NO_WARNINGS 1
#endif

#include <string>
#include <regex>
#include <cstdint>
#include "regex_win32.h"


typedef std::regex_iterator<const char *> Myiter;


/*!
  @brief Count the number of times a regular expression is matched in a string.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @return int Number of matches found. -1 is returned if the regex could not be
  compiled.
*/
int count_matches(const char *regex_text, const char *to_match) {
  try {
    Myiter::regex_type r(regex_text);
    int ret = 0;
    Myiter next(to_match, to_match + strlen(to_match), r);
    Myiter end;
    for (; next != end; ++next)
      ret++;
    return ret;
  } catch (const std::regex_error& rerr) {
    rerr;
    return -1;
  }
}


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
int find_matches(const char *regex_text, const char *to_match,
		 size_t **sind, size_t **eind) {
  try {
    std::regex r(regex_text);
    std::cmatch m;
    int ret = 0;
    if (regex_search(to_match, to_match + strlen(to_match), m, r)) {
      ret += (int)(m.size());
      *sind = (size_t*)realloc(*sind, ret*sizeof(size_t));
      *eind = (size_t*)realloc(*eind, ret*sizeof(size_t));
      int i, j;
      for (i = 0, j = 0; i < ret; i++) {
        if (m.length(i) > 0) {
        	(*sind)[j] = m.position(i);
        	(*eind)[j] = (*sind)[j] + m.length(i);
          j++;
        }
      }
      ret = j;
    }
    return ret;
  } catch (const std::regex_error& rerr) {
    rerr;
    return -1;
  }
}


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
  try {
    std::regex r(regex_text);
    std::cmatch m;
    int ret = 0;
    if (regex_search(to_match, to_match + strlen(to_match), m, r)) {
      ret++;
      *sind = m.position();
      *eind = *sind + m.length();
    }
    return ret;
  } catch (const std::regex_error& rerr) {
    rerr;
    return -1;
  }
}


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
int regex_replace_nosub(char *buf, const size_t len_buf,
			const char *re, const char *rp,
			const size_t nreplace) {
  try {
    std::regex r(re);
    size_t len_rp = strlen(rp);
    size_t len_m, rem_s, rem_l, delta_siz;
    size_t cur_pos = 0;
    size_t cur_siz = strlen(buf);
    size_t creplace = 0;
    int ret = 0;
    std::cmatch m;
    while (1) {
      if ((nreplace > 0) && (creplace >= nreplace)) {
	printf("regex_replace_nosub: Maximum of %d replacements reached\n",
	       (int)creplace);
	break;
      }
      const char *first = buf + cur_pos;
      const char *last = buf + cur_siz;
      if (!(regex_search(first, last, m, r))) {
	break;
      }
      // Ensure replacement will not exceed buffer
      len_m = m.length();
      delta_siz = len_rp - len_m;
      if ((cur_siz + delta_siz + 1) > len_buf) {
	printf("regex_replace_nosub: Relacement will exceed buffer.\n");
	ret = -1;
	break;
      }
      // Move trailing
      rem_l = cur_siz - (cur_pos + m.position() + len_m);
      rem_s = m.position() + len_rp;
      char *p = buf + cur_pos;
      memmove(p + rem_s, p + m.position() + len_m, rem_l + 1);
      // Copy replacement
      strncpy(p + m.position(), rp, len_rp);
      // Advance
      cur_pos += rem_s;
      cur_siz += delta_siz;
      creplace += 1;
    }
    /* printf("regex_replace_nosub() = %s\n", buf); */
    if (ret < 0) {
      return -1;
    } else {
      return (int)cur_siz;
    }
  } catch (const std::regex_error& rerr) {
    rerr;
    return -1;
  }
}
  
/*!
  @brief Extract substring references from a string.
  @param[in] buf Constant character pointer to buffer that references should be
  extracted from.
  @param[out] refs Pointer to pointer to memory where reference numbers should
  be stored. This function will reallocate it to fit the number of references
  returned. (Should be freed by calling program.)
  @return int Number of refs found. -1 indicates an error.
*/
int get_subrefs(const char *buf, size_t **refs) {
  // Compile
  try {
    // TODO: check this on windows regex
    std::regex r("\\$([[:digit:]])");
    // Prepare "bitmap"
    const size_t max_ref = 10; //99;
    size_t i;
    uint8_t *ref_bytes = (uint8_t*)malloc((max_ref + 1)*sizeof(uint8_t));
    for (i = 0; i <= max_ref; i++)
      ref_bytes[i] = 0;
    // Locate matches
    std::cmatch m;
    const size_t max_grp = 2;  // Digits in max_ref
    size_t igrp_len;
    char igrp[max_grp];
    size_t iref;
    const char *first = buf;
    const char *last = buf + strlen(buf);
    while (1) {
      if (!(regex_search(first, last, m, r))) {
	break;
      }
      // Lone $ without digit
      /* printf("so = %d, eo = %d\n", (int)m[1].rm_so, (int)m[1].rm_eo); */
      if (m.size() == 1) {
	first += m.position() + m.length();
	continue;
      }
      // Substring
      igrp_len = m.length(1);
      if (igrp_len > max_grp) {
	printf("Number longer than %d digits unlikely.\n", (int)max_grp);
	free(ref_bytes);
	return -1;
      }
      strncpy(igrp, first + m.position(1), igrp_len);
      igrp[igrp_len] = 0;
      // Extract ref number
      iref = atoi(igrp);
      if (iref > max_ref) {
	printf("Reference to substr %d exceeds limit (%d)\n",
	       (int)iref, (int)max_ref);
	free(ref_bytes);
	return -1;
      }
      ref_bytes[iref] = 1;
      first += m.position() + m.length();
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
    free(ref_bytes);
    // printf("%d refs in %s\n", nref, buf);
    return nref;
  } catch (const std::regex_error& rerr) {
    rerr;
    return -1;
  }
}


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
int regex_replace_sub(char *buf, const size_t len_buf,
		      const char *re, const char *rp,
		      const size_t nreplace) {
  // Compile
  try {
    std::regex r(re);
    // Loop making replacements
    std::cmatch m;
    char *rp_sub = (char*)malloc(2*len_buf*sizeof(char));
    char *re_sub = (char*)malloc(len_buf*sizeof(char));
    char *igrp = (char*)malloc(len_buf*sizeof(char));
    size_t len_m, rem_s, rem_l, delta_siz, len_rp;
    size_t cur_pos = 0;
    size_t cur_siz = strlen(buf);
    size_t creplace = 0;
    size_t i;
    int j;
    int ret = 0;
    while (1) {
      if ((nreplace > 0) && (creplace >= nreplace)) {
	printf("regex_replace_nosub: Maximum of %d replacements reached\n",
	       (int)creplace);
	break;
      }
      const char *first = buf + cur_pos;
      const char *last = buf + cur_siz;
      if (!(regex_search(first, last, m, r))) {
	/* printf("regex_replace_sub: nomatch for %s in %s\n", re, p); */
	break;
      }
      // Get list of subrefs
      size_t *refs = NULL;
      int nref = get_subrefs(rp, &refs);
      if (nref < 0) {
	printf("Error gettings subrefs\n");
	ret = -1;
	break;
      }
      // For each subref complete replacements
      strncpy(rp_sub, rp, 2*len_buf);
      for (j = 0; j < nref; j++) {
	i = refs[j];
	strncpy(igrp, buf + cur_pos + m.position(i), len_buf);
	igrp[m.length(i)] = '\0'; // terminate
	sprintf(re_sub, "\\$%d", (int)i);
	ret = regex_replace_nosub(rp_sub, 2*len_buf, re_sub, igrp, 0);
	if (ret < 0) {
	  printf("regex_replace_sub: Error replacing substring $%d.\n", (int)i);
	  free(refs);
	  free(rp_sub);
	  free(re_sub);
	  free(igrp);
	  return -1;
	}
      }
      // Ensure replacement will not exceed buffer
      len_rp = (size_t)ret;
      len_m = m.length();
      delta_siz = len_rp - len_m;
      if ((cur_siz + delta_siz + 1) > len_buf) {
	printf("regex_replace_sub: Relacement will exceed buffer.\n");
	ret = -1;
	break;
      }
      // Move trailing
      rem_l = cur_siz - (cur_pos + m.position() + m.length());
      rem_s = m.position() + len_rp;
      memmove(buf + cur_pos + rem_s,
	      buf + cur_pos + m.position() + m.length(), rem_l + 1);
      // Copy replacement
      strncpy(buf + cur_pos + m.position(), rp_sub, len_rp);
      // Advance
      cur_pos += m.position() + len_rp;
      cur_siz += delta_siz;
      creplace += 1;
      free(refs);
    }
    free(rp_sub);
    free(re_sub);
    free(igrp);
    if (ret < 0) {
      return -1;
    } else {
      return (int)(cur_siz);
    }
  } catch (const std::regex_error& rerr) {
    rerr;
    return -1;
  }
}
