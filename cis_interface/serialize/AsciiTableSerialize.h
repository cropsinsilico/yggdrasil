#ifndef YGGASCIITABLESERIALIZE_H_
#define YGGASCIITABLESERIALIZE_H_

#include <../tools.h>
#include <SerializeBase.h>
#include <../dataio/AsciiTable.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*!
  @brief Serialize arguments to create a table row.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[out] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz size_t Size of memory allocated to buf.
  @param[out] args_used int Number of arguments formatted.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error.
 */
static inline
int serialize_ascii_table(const seri_t s, char *buf, const size_t buf_siz,
          int *args_used, va_list ap) {
  asciiTable_t *table = (asciiTable_t*)s.info;
  args_used[0] = table->ncols;
  int ret = at_vrow_to_bytes(*table, buf, buf_siz, ap);
  return ret;
};

/*!
  @brief Deserialize table row to populate arguments.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[in] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize_ascii_table(const seri_t s, const char *buf, const size_t buf_siz,
			    va_list ap) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  buf_siz;
#endif
  asciiTable_t *table = (asciiTable_t*)s.info;
  int ret = at_vbytes_to_row(*table, buf, ap);
  return ret;
};

/*!
  @brief Serialize column arrays to create table.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[out] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz size_t Size of memory allocated to buf.
  @param[out] args_used int Number of arguments formatted.
  @param[in] ap va_list Arguments to be formatted. These should be pointers to
  arrays, one for each column in the table. The first argument should be the number
  of rows in each column.
  returns: int The length of the serialized message or -1 if there is an error.
 */
static inline
int serialize_ascii_table_array(const seri_t s, char *buf, const size_t buf_siz,
				int *args_used, va_list ap) {
  asciiTable_t *table = (asciiTable_t*)s.info;
  args_used[0] = table->ncols + 1;
  int ret = at_varray_to_bytes(*table, buf, buf_siz, ap);
  return ret;
};

/*!
  @brief Deserialize table to populate column arrays.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[in] ap va_list Pointers to pointers where column arrays should be stored.
  These should not be allocated prior to passing them as they will be allocated.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize_ascii_table_array(const seri_t s, const char *buf,
				  const size_t buf_siz, va_list ap) {
  asciiTable_t *table = (asciiTable_t*)s.info;
  int ret = at_vbytes_to_array(*table, buf, buf_siz, ap);
  return ret;
};

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGASCIITABLESERIALIZE_H_*/
