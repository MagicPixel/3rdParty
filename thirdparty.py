#!/usr/bin/python

import os, sys, subprocess, shutil

from multiprocessing import cpu_count
import json

import platform
import zipfile




def mkdir(d):
	if not os.path.isdir(d):
		os.mkdir(d)

def copy_dir_to(src, dst):
	mkdir(dst)
	for filename in os.listdir(src):
		if os.path.isdir(src + "/" + filename):
			copy_dir_to(src + "/" + filename, dst + "/" + filename)
		else:
			shutil.copy(src + "/" + filename,  dst + "/" + filename)

def remove_dir(src):
	for filename in os.listdir(src):
		if os.path.isdir(src + "/" + filename):
			shutil.rmtree(src + "/" + filename)
	
def move_dir_to(src, dst):
	mkdir(dst)
	for filename in os.listdir(src):
		if not os.path.isdir(src + "/" + filename):
			shutil.move(src + "/" + filename,  dst + "/" + filename)

def download_file(url, dst):
	if os.path.exists(dst):
		return
	response = requests.get(url, stream=True)
	status = response.status_code
	if status == 200:
		#total_size = int(response.headers['Content-Length'])
		with open(dst, 'wb') as of:
			for chunk in response.iter_content(chunk_size=1024):
				if chunk:
					of.write(chunk)
		of.close()

class ThirdParty:
	def __init__(self, root):
		self.root = root
		self.platform = platform.system() 
		self.source_root = root + "/sources"
		self.build_root = root + "/projects"
		self.install_root = root + "/install"

		self.out_root = root + "/" + self.platform
		mkdir(self.source_root)
		mkdir(self.build_root)
		mkdir(self.install_root)
		mkdir(self.out_root)

		self.config = json.load(file(root + "/3rdParty.json"))

	def clone_lib_git(self, lib):
		source_root = self.source_root + "/" + lib["version_root"]
		mkdir(source_root)
		if os.path.exists(source_root + "/.git"):
			return

		clone_cmd = ["git", "clone", lib["git"], source_root]
		subprocess.call(clone_cmd)

		os.chdir(source_root)
		try:
			subprocess.call(["git", "submodule", "update", "--init", "--recursive"])
		except:
			pass

		subprocess.call(["git", "checkout", lib["version"]])

	def clone_lib_zip(self, lib):

		try :
			import requests
		except:
			subprocess.call(["pip", "install" "requests"])
			import requests

		filepath = self.source_root + "/" + lib["version_root"] + ".zip"
		if not os.path.isfile(filepath):
			download_file(lib["zip"], filepath)

		file_zip = zipfile.ZipFile(filepath, 'r')

		for filename in file_zip.namelist():
			file_zip.extract(filename, self.source_root)
		file_zip.close()

	def clone_lib(self, lib):
		if lib.has_key("zip"):
			self.clone_lib_zip(lib)
		else:
			self.clone_lib_git(lib)

	def cmake_build_lib(self, lib, build_model, build_type):
		model = 64
		if build_model == "x86":
			model = 32

		build_root  = self.build_root + "/" + lib["version_root"]
		source_root = self.source_root + "/" + lib["version_root"]

		mkdir(build_root)
		os.chdir(build_root)


		cmake_cmd = [
			"cmake",
			"-DCMAKE_BUILD_TYPE=%s" % build_type,
			"-DMAGIC_BUILD_MODEL=%d" % model,
			"-DMAGIC_BUILD_ROOT=%s" % build_root,
			"-DWITH_CUDA=OFF",
			"-DCMAKE_INSTALL_PREFIX=%s" % self.install_root,
			"-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY=lib/%s" % build_model,
			"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=lib/%s" % build_model,
			"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=bin/%s" % build_model
			]

		for cmd in self.config["cmake"][self.platform]["Generator"][build_model]:
				cmake_cmd.append(cmd)

		cmake_cmd.append(source_root)

		print  cmake_cmd

		subprocess.call(cmake_cmd)

		bin = self.config["cmake"][self.platform]["Build"]["bin"]
		target = self.config["cmake"][self.platform]["Build"]["target"]
		multi_thread = self.config["cmake"][self.platform]["Build"]["multi_thread"] % cpu_count()
		build_cmd = [bin]
		for cmd in target:
			build_cmd.append(cmd)
		build_cmd.append(multi_thread)

		print build_cmd
		subprocess.call(build_cmd)

	def cmake_install_lib(self, lib, build_model, build_type):
		print("install lib %s" % lib["name"])
		if self.find_lib(lib, self.install_root):
			return

		self.cmake_build_lib(lib, build_model, build_type)

		print("install")
		bin = self.config["cmake"][self.platform]["Install"]["bin"]
		target = self.config["cmake"][self.platform]["Install"]["target"]
		multi_thread = self.config["cmake"][self.platform]["Install"]["multi_thread"] % cpu_count()
		
		
		if True:#os.path.exists(self.build_root + "/" + lib["name"] + "/install_manifest.txt"):
			install_cmd = [bin]
			for cmd in target:
				install_cmd.append(cmd)
			install_cmd.append(multi_thread)
			print(install_cmd)
			subprocess.call(install_cmd)

		else:
			print("no cmake_install.cmake, install by manuls")
			#if lib have no install , copy the the files by manul
			#copy include bin lib
			#copy_dir_to(self.source_root + "/" + lib["version_root"] + "/include",  self.install_root + "/include")
			#copy_dir_to(self.build_root + "/" + lib["version_root"] + "/bin",  self.install_root + "/bin")
			#copy_dir_to(self.build_root + "/" + lib["version_root"] + "/lib",  self.install_root + "/lib")

	def python_install_lib(self, lib, build_model, build_type):
			os.chdir(self.root)
			source_root = self.source_root + "/" + lib["version_root"]
			build_root = self.build_root + "/" + lib["version_root"]
			install_root = self.install_root

			subprocess.call(["python", lib["name"] + ".py", source_root, build_root, install_root, build_model, build_type])

	def install_dev(self, build_model, build_type):
		libs = self.config["3rdParty"]

		for lib in libs:
			install_lib(
				lib, 
				build_model, build_type)

	def install_dep(self, build_model, build_type):
		libs = self.config["3rdParty"]

		for lib in libs:
			if not self.find_lib(lib, self.install_root):
				self.install_lib(lib, build_model, build_type)



		#remove dir
		#remove_dir(self.install_root + "/lib")

		#copy bin lib to  bin/build_model  lib/build_model
		#move_dir_to(self.install_root + "/bin",  self.install_root + "/bin/" + build_model)
		#move_dir_to(self.install_root + "/lib",  self.install_root + "/lib/" + build_model)
	
	def install_lib(self, lib, build_model, build_type):
		self.clone_lib(lib)

		if os.path.exists(self.source_root + "/" + lib["version_root"] + "/CMakeLists.txt"):
			self.cmake_install_lib(lib, build_model, build_type)
		else:
			self.python_install_lib(lib, build_model, build_type)

	def find_lib(self, libname, install_root):
		return os.path.isdir(install_root + "/include/" + libname["name"])
	
	
if __name__ == "__main__":

	root = os.getcwd()
	build_model = "x64"
	build_type = "Release"

	if len(sys.argv) == 4:
		root = sys.argv[1]
		build_model = sys.argv[2]
		build_type = sys.argv[3]

	p = ThirdParty(root)
	p.install_dep(build_model, build_type)


