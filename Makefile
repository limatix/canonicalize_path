all:
	python setup.py build

install:
	python setup.py --prefix=/usr/local install
	python setup.py --prefix=/usr/local install_data

clean:
	python setup.py clean
	rm -f *~ *.pyc *.swp */*~ */*.pyc */*.swp
	rm -rf build/
	rm -rf dist/
	rm -rf canonicalize_path.egg-info
	rm -rf canonicalize_path/__pycache__

commit: clean
	hg addrem
	hg commit




