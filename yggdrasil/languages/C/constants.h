#ifndef YGGCONSTANTS_H_
#define YGGCONSTANTS_H_

/*! @brief Maximum message size. */
#ifdef IPCDEF
#define YGG_MSG_MAX 2048
#else
#define YGG_MSG_MAX 1048576
#endif
/*! @brief End of file message. */
#define YGG_MSG_EOF "EOF!!!"
/*! @brief End of client message. */
#define YGG_CLIENT_EOF "YGG_END_CLIENT"
/*! @brief Client signing on. */
#define YGG_CLIENT_SIGNON "CLIENT_SIGNON::"
#define YGG_CLIENT_SIGNON_LEN 15
/*! @brief Server signing on. */
#define YGG_SERVER_SIGNON "SERVER_SIGNON::"
#define YGG_SERVER_SIGNON_LEN 15
/*! @brief Resonable size for buffer. */
#define YGG_MSG_BUF 2048
/*! @brief Sleep time in micro-seconds */
#define YGG_SLEEP_TIME ((int)250000)
/*! @brief Maximum time to wait for any operation in micro-seconds */
#define YGG_MAX_TIME ((int)54000000000) // 15 minutes
/*! @brief Size for buffers to contain names of Python objects. */
#define PYTHON_NAME_SIZE 1000

/*! @brief Define old style names for compatibility. */
#define PSI_MSG_MAX YGG_MSG_MAX
#define PSI_MSG_BUF YGG_MSG_BUF
#define PSI_MSG_EOF YGG_MSG_EOF

#define MSG_HEAD_SEP "YGG_MSG_HEAD"
/*! @brief Size of COMM buffer. */
#define COMMBUFFSIZ 2000
#define FMT_LEN 100

/*! @brief Bit flags. */
#define HEAD_FLAG_VALID      0x00000001  //!< Set if the header is valid.
#define HEAD_FLAG_MULTIPART  0x00000002  //!< Set if the header is for a multipart message
#define HEAD_META_IN_DATA    0x00000004  //!< Set if the type is stored with the data during serialization
#define HEAD_AS_ARRAY        0x00000008  //!< Set if messages will be serialized arrays
#define HEAD_FLAG_OWNSDATA   0x00000010
#define HEAD_FLAG_ALLOW_REALLOC 0x00000020
#define HEAD_TEMPORARY       0x00000040
#define HEAD_FLAG_EOF        0x00000080
#define HEAD_FLAG_CLIENT_EOF 0x00000100
#define HEAD_FLAG_CLIENT_SIGNON 0x00000200
#define HEAD_FLAG_SERVER_SIGNON 0x00000400
#define HEAD_FLAG_REPEAT 0x00000800

#endif // YGGCONSTANTS_H_
