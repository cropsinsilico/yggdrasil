IDIR = .
CC = gcc
CFLAGS = -I$(IDIR) $(CISCCFLAGS)

ODIR = .
LDIR = .

LIBS = -lm $(CISLDFLAGS)

_DEPS = hellofunc.h
DEPS = $(patsubst %,$(IDIR)/%,$(_DEPS))

_OBJ = gcc_model.o hellofunc.o
OBJ = $(patsubst %,$(ODIR)/%,$(_OBJ))


$(ODIR)/%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

gcc_model: $(OBJ)
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

.PHONY: clean

clean:
	rm -f $(ODIR)/*.o *~ gcc_model $(INCDIR)/*~ 
