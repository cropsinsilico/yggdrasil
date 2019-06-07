/*! @brief Flag for checking if CisInterface.h has already been included.*/
#ifndef CISINTERFACE_H_
#define CISINTERFACE_H_

#include "YggInterface.h"

/*! @brief Aliases to preserve names of original structures. */
#define cisOutput_t yggOutput_t
#define cisInput_t yggInput_t
#define cis_free ygg_free
#define cisOutputFmt yggOutputFmt
#define cisInputFmt yggInputFmt
#define cisOutput yggOutput
#define cisInput yggInput
#define cis_send ygg_send
#define cis_send_eof ygg_send_eof
#define cis_recv ygg_recv
#define cis_send_nolimit ygg_send_nolimit
#define cis_send_nolimit_eof ygg_send_nolimit_eof
#define cis_recv_nolimit ygg_recv_nolimit
#define cisSend yggSend
#define cisRecv yggRecv
#define cisRecvRealloc yggRecvRealloc
#define vcisSend vyggSend
#define vcisRecv vyggRecv
#define vcisSend_nolimit vyggSend_nolimit
#define vcisRecv_nolimit vyggRecv_nolimit
#define cisSend_nolimit yggSend_nolimit
#define cisRecv_nolimit yggRecv_nolimit
#define cisRpc_t yggRpc_t
#define cisRpcClient yggRpcClient
#define cisRpcServer yggRpcServer
#define cisAsciiFileInput_t yggAsciiFileInput_t
#define cisAsciiFileOutput_t yggAsciiFileOutput_t
#define cisAsciiFileOutput yggAsciiFileOutput
#define cisAsciiFileInput yggAsciiFileInput
#define cisAsciiTableInput_t yggAsciiTableInput_t
#define cisAsciiTableOutput_t yggAsciiTableOutput_t
#define cisAsciiArrayInput_t yggAsciiArrayInput_t
#define cisAsciiArrayOutput_t yggAsciiArrayOutput_t
#define cisAsciiTableOutput yggAsciiTableOutput
#define cisAsciiTableInput yggAsciiTableInput
#define cisAsciiArrayOutput yggAsciiArrayOutput
#define cisAsciiArrayInput yggAsciiArrayInput
#define cisPlyInput_t yggPlyInput_t
#define cisPlyOutput_t yggPlyOutput_t
#define cisPlyOutput yggPlyOutput
#define cisPlyInput yggPlyInput
#define cisObjInput_t yggObjInput_t
#define cisObjOutput_t yggObjOutput_t
#define cisObjOutput yggObjOutput
#define cisObjInput yggObjInput

#endif /*CISINTERFACE_H_*/
