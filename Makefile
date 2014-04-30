all:
	python setup.py build

install:
	python setup.py install --prefix=/usr/local

clean:
	python setup.py clean
	rm -f *~ *.pyc *.swp
	rm -rf build/

commit: clean
	hg addrem
	hg commit




