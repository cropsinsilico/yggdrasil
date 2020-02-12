#ifndef YGG_FC_WRAPPERS_H_
#define YGG_FC_WRAPPERS_H_

#include "../C/YggInterface.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif
  
void * ygg_input_ff(const char *name);

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif


#endif /*YGG_FC_WRAPPERS_H_*/
