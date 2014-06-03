all:
	python setup.py build

install:
	python setup.py install --prefix=/usr/local

clean:
	python setup.py clean
	rm -f *~ *.pyc *.swp */*~ */*.pyc */*.swp
	rm -rf build/
	rm -rf canonicalize_path/__pycache__

commit: clean
	hg addrem
	hg commit




