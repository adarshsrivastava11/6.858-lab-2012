ASFLAGS := -m32
CFLAGS  := -m32 -g -std=c99 -Wall -Werror -D_GNU_SOURCE
LDFLAGS := -m32
LDLIBS  := -lcrypto
PROGS   := zookld zookfs zookd zooksvc

all: $(PROGS)
.PHONY: all

zookld zookd zookfs: %: %.o http.o
zooksvc: %: %.o




.PHONY: setup
setup:
	./chroot-setup.sh


.PHONY: clean
clean:
	rm -f *.o *.pyc *.bin $(PROGS)


lab%-handin.tar.gz: clean
	tar cf - `find . -type f | grep -v '^\.*$$' | grep -v '/CVS/' | grep -v '/\.svn/' | grep -v '/\.git/' | grep -v 'lab[0-9].*\.tar\.gz' | grep -v ^./pypy-sandbox.tar | grep -v '/submit.key$$'` | gzip > $@

.PHONY: submit
submit: lab5-handin.tar.gz
	./submit.py $<
