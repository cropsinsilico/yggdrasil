// https://snorfalorpagus.net/blog/2016/07/17/compiling-python-extensions-for-old-glibc-versions/
__asm__(".symver memcpy,memcpy@GLIBC_2.2.5");
