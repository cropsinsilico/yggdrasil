

#
# Compile for a shared lib
#
INCLUDE = -I../../../interface
LIB = -lrt

PROGS=maxMsgSrv maxMsgCli

ifdef PSI_DEBUG
DEBUG= -DPSI_DEBUG=$(PSI_DEBUG)
endif

all: $(PROGS)

$(PROGS): ../../../interface/PsiInterface.h


%: %.c	
	gcc $(CFLAGS) $(INCLUDE) $(DEBUG) -o $@ $< $(LIB)

%: %.cpp	
	g++ $(CPPFLAGS) $(INCLUDE) $(DEBUG) -o $@ $< $(LIB)

clean:
	rm -f $(PROGS)
