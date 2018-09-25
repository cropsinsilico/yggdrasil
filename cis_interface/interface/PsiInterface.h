#include <../tools.h>
#include <../communication/communication.h>
#include <../dataio/AsciiFile.h>
#include <../dataio/AsciiTable.h>
#include <CisInterface.h>

// Old, "psi" styled aliases

/*! @brief Flag for checking if PsiInterface.h has already been included.*/
#ifndef PSIINTERFACE_H_
#define PSIINTERFACE_H_

/*! @brief Aliases to preserve old-stye names. */
#define psiInput_t cisInput_t
#define psiOutput_t cisOutput_t
#define psiInput cisInput
#define psiOutput cisOutput
#define psi_free cis_free
#define psi_input cisInput
#define psi_output cisOutput
#define psiInputFmt cisInputFmt
#define psiOutputFmt cisOutputFmt
#define psi_send cis_send
#define psi_recv cis_recv
#define psi_send_eof cis_send_eof
#define psi_send_nolimit cis_send_nolimit
#define psi_recv_nolimit cis_recv_nolimit
#define vpsiSend vcisSend
#define vpsiRecv vcisRecv
#define psiSend cisSend
#define psiRecv cisRecv
#define vpsiSend_nolimit vcisSend_nolimit
#define vpsiRecv_nolimit vcisRecv_nolimit
#define psiSend_nolimit cisSend_nolimit
#define psiRecv_nolimit cisRecv_nolimit
#define psiRpc_t cisRpc_t
#define psiRpc cisRpc
#define psiRpcClient cisRpcClient
#define psiRpcServer cisRpcServer
#define psi_free_rpc cis_free_rpc
#define psiAsciiFileInput_t cisAsciiFileInput_t
#define psiAsciiFileOutput_t cisAsciiFileOutput_t
#define psiAsciiFileInput cisAsciiFileInput
#define psiAsciiFileOutput cisAsciiFileOutput
#define psiAsciiTableInput_t cisAsciiTableInput_t
#define psiAsciiTableOutput_t cisAsciiTableOutput_t
#define psiAsciiTableInput cisAsciiTableInput
#define psiAsciiTableOutput cisAsciiTableOutput
#define psiAsciiTableInput_local cisAsciiTableInput_local
#define psiAsciiTableOutput_local cisAsciiTableOutput_local
#define psiAsciiArrayInput cisAsciiArrayInput
#define psiAsciiArrayOutput cisAsciiArrayOutput
#define psiAsciiArrayInput_local cisAsciiArrayInput_local
#define psiAsciiArrayOutput_local cisAsciiArrayOutput_local
#define psiPlyInput_t cisPlyInput_t
#define psiPlyOutput_t cisPlyOutput_t
#define psiPlyInput cisPlyInput
#define psiPlyOutput cisPlyOutput
#define psiObjInput_t cisObjInput_t
#define psiObjOutput_t cisObjOutput_t
#define psiObjInput cisObjInput
#define psiObjOutput cisObjOutput


#endif /*PSIINTERFACE_H_*/
