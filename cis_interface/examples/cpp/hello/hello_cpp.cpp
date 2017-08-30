
#include "PsiInterface.hpp"
#include <string>
#include <iostream>

int main(int argc, char *argv[]) {
	const int bufsz = 512;
    char buf[bufsz];
    std.cout << "hello C++\n";

    /* Matching with the the model yaml */
    PSi_Input inf("infile"); 
    PSi_Output outf("outfile");
    PSi_Input inq("helloQueue");
    PSi_Output outq("helloQueue");

    inf.recv(buf, bufsz);
    outq.send(buf, bufsz);
    inq.recv(buf,   bufsz);
    outf.send(buf, bufsz);

    std.cout << "bye\n";
    
}
