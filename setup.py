import shutil
import os.path
from setuptools import setup
from setuptools.command.install_lib import install_lib
from setuptools.command.install import install
import setuptools.command.bdist_egg
import sys

config_files=["canonical_paths.conf.example","tag_index_paths.conf.example"]
package_files=["canonical_paths.conf","tag_index_paths.conf"]

# NOTE ***: config files will be installed to prefix/etc/canonicalize_path/
# By default, prefix is /usr so configfiles to be found in
# /usr/etc/canonicalize_path!

# Apply hotfix to setuptools issue #130, from 
# https://bitbucket.org/pypa/setuptools/issues/130/install_data-doesnt-respect-prefix
# hotfix applies at least to all setuptools versions prior to 20.2

def setuptools_command_bdist_egg_call_command_hotfix(self, cmdname, **kw):
    """Invoke reinitialized command `cmdname` with keyword args"""
    if cmdname != 'install_data':
        for dirname in INSTALL_DIRECTORY_ATTRS:
            kw.setdefault(dirname, self.bdist_dir)
    kw.setdefault('skip_build', self.skip_build)
    kw.setdefault('dry_run', self.dry_run)
    cmd = self.reinitialize_command(cmdname, **kw)
    self.run_command(cmdname)
    return cmd

setuptools_version=tuple([int(versionpart) for versionpart in setuptools.__version__.split(".")])

# Apply hotfix to all versions prior to 20.2
if setuptools_version < (20,2):
    setuptools.command.bdist_egg.call_command=setuptools_command_bdist_egg_call_command_hotfix
    pass




class install_lib_save_prefix(install_lib):
    """Save a file install_prefix.txt with the install prefix"""
    def run(self):
        install_lib.run(self)
        
        #sys.stderr.write("\nprefix:" + str((self.distribution.command_obj["install"].prefix))+"\n\n\n")
        
        #sys.stderr.write("\ninstall_dir:" + self.install_dir+"\n\n\n")
        #sys.stderr.write("\npackages:" + str(self.distribution.command_obj["build_py"].packages)+"\n\n\n")

        for package in self.distribution.command_obj["build_py"].packages:
            install_dir=os.path.join(*([self.install_dir] + package.split('.')))
            fh=open(os.path.join(install_dir,"install_prefix.txt"),"w")
            fh.write(self.distribution.command_obj["install"].prefix)
            fh.close()
            pass
        pass
    pass


#class install_config_files(install):
#    """store config files in PREFIX/etc"""
#    def run(self):
#        install.run(self)
        
#        #sys.stderr.write("\nprefix:" + str((self.distribution.command_obj["install"].prefix))+"\n\n\n")
#        
#        if self.prefix=="/usr": 
#            config_dir='/etc/canonicalize_path'
#            pass
#        else:
#            config_dir=os.path.join(self.prefix,"etc","canonicalize_path")
#            pass
#
#        if not os.path.exists(config_dir):
#            os.mkdir(config_dir)
#            pass
#
#        for configfile in config_files:
#            if os.path.exists(os.path.join(config_dir,configfile)):
#                os.remove(os.path.join(config_dir,configfile))
#                pass
#            shutil.copyfile(configfile,os.path.join(config_dir,configfile))
#            pass
#            
#        pass
#    pass

setup(name="canonicalize_path",
      description="path canonicalization",
      author="Stephen D. Holland",
      # url="http://limatix.org/dataguzzler",
      packages=["canonicalize_path"],
      cmdclass={"install_lib": install_lib_save_prefix},
      data_files=[ (os.path.join('etc','canonicalize_path'),config_files) ],
      package_data={"canonicalize_path": package_files })

#"install": install_config_files



