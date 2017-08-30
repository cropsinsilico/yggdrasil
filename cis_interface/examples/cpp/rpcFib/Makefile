

#
# Compile for a shared lib
#
INCLUDE = -I../../../interface
LIB = -lrt

PROGS=rpcFibCli rpcFibSrv rpcFibCliPar 

ifdef PSI_DEBUG
DEBUG= -DPSI_DEBUG=$(PSI_DEBUG) -g -O0 -Wall
endif

all: $(PROGS)


%: %.c	
	gcc $(CFLAGS) $(INCLUDE) $(DEBUG) -o $@ $< $(LIB)

%: %.cpp	
	g++ $(CPPFLAGS) $(INCLUDE) $(DEBUG) -o $@ $< $(LIB)

clean:
	rm -f $(PROGS)
