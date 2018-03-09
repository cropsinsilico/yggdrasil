/* Example include file. */
#ifndef HELLOFUNC_H_
#define HELLOFUNC_H_

#ifdef __cplusplus
#define EXTERNC extern "C"
#else
#define EXTERNC
#endif

EXTERNC void myPrint(const char * msg);

#undef EXTERNC
#endif /*HELLOFUNC_H_*/
