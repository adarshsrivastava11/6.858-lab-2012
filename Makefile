ASFLAGS := -m32
CFLAGS  := -m32 -g -std=c99 -Wall -Werror -D_GNU_SOURCE
LDFLAGS := -m32
LDLIBS  := -lcrypto
PROGS   := zookld zookfs zookd zooksvc

all: $(PROGS)
.PHONY: all

zookld zookd zookfs: %: %.o http.o
zooksvc: %: %.o


.PHONY: check
check:
	./check-lab2.py


.PHONY: setup
setup:
	./chroot-setup.sh


.PHONY: clean
clean:
	rm -f *.o *.pyc *.bin $(PROGS)


lab%-handin.tar.gz: clean
	tar cf - `find . -type f | grep -v '^\.*$$' | grep -v '/CVS/' | grep -v '/\.svn/' | grep -v '/\.git/' | grep -v 'lab[0-9].*\.tar\.gz'` | gzip > $@

.PHONY: handin
handin: lab2-handin.tar.gz
	@echo "Please visit http://css.csail.mit.edu/6.858/2012/labs/handin.html"
	@echo "and upload $<.  Thanks!"

.PHONY: submit
submit: lab2-handin.tar.gz
	./submit.py $<
