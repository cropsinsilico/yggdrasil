#include "PsiInterface.hpp"
#include <string>
#include <iostream>
using namespace std;

int main(int argc, char *argv[]) {
  int ret = 1;
  const int bufsz = 512;
  char buf[bufsz];

  cout << "Hello from C++\n";
  
  /* Matching with the the model yaml */
  PSi_Input inf("inFile"); 
  PSi_Output outf("outFile");
  PSi_Input inq("helloQueueIn");
  PSi_Output outq("helloQueueOut");
  cout << "hello_cpp: Created I/Os\n";

  // Receive input from the local file
  ret = inf.recv(buf, bufsz);
  if (ret < 0)
    perror("psi_recv");
  cout << "hello_cpp: Received " << ret << " bytes: " << buf << "\n";

  // Send output to queue
  ret = outq.send(buf, ret);
  if (ret < 0)
    perror("psi_send:");
  cout << "hello_cpp: Send returns " << ret << "\n";

  // Receive input from queue
  ret = inq.recv(buf, bufsz);
  if (ret < 0)
    perror("psi_recv");
  cout << "hello_cpp: Received " << ret << " bytes: " << buf << "\n";

  // Send output to local file
  outf.send(buf, ret);
  if (ret < 0)
    perror("psi_send:");
  cout << "hello_cpp: Send returns " << ret << "\n";

  cout << "Goodbye from C++\n";
    
}
