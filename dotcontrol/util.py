FILE_READ_CHUNK_SIZE = 4096


def now():
	from time import time
	return int(time())


def mkdirp(dest):
	'''
	Create directory, and its parent(s) if they did't exist,
	like `mkdir -p`.
	'''

	if not dest.exists():
		for path in reversed(dest.parents):
			if not path.exists():
				path.mkdir()
		dest.mkdir()


def iterdirp(path, files_only=False, ignore_errors=False):
	'''Recursively iterate over directories and files under `path`.'''

	dirs = [item for item in path.iterdir() if item.is_dir()]
	dir = None
	while dirs:
		dir = dirs.pop(0)
		try:
			for item in dir.iterdir():
				if item.is_dir():
					dirs.append(item)
					if files_only:
						continue
				yield item
		except Exception as e:
			if ignore_errors:
				pass
			else:
				raise e


class keep_cwd:
	'''
	Use `with keep_cwd(optional_target_path)` to go back to `cwd` after
	working in other directory(-ies).
	'''
	from os import getcwd, chdir

	def __init__(self, to=None):
		self.to = to

	def __enter__(self):
		self.cwd = self.getcwd()
		if self.to:
			self.chdir(self.to)
	
	def __exit__(self, *args, **kwargs):
		self.chdir(self.cwd)


def link_dir(source, target):
	'''Recursively create directory structure and hard link files.'''

	from os import link

	for item in iterdirp(source):
		if item.is_dir():
			target_item = target.joinpath(item.relative_to(source))			
			if not target_item.exists():
				mkdirp(target_item)
		else:
			link(item, target.joinpath(item.relative_to(source)))


def sha1_hash(object):
	'''
	Calculate hex digest for input.
	Argument may be a string, bytes object, or a path-like object.
	'''

	from hashlib import sha1
	from pathlib import Path
	
	if type(object) in (str, bytes):
		return sha1(object).hexdigest()
	elif Path(object).exists():
		with open(object, 'rb') as f:
			hash = sha1()
			buf = f.read(FILE_READ_CHUNK_SIZE)
			while buf:
				hash.update(buf)
				buf = f.read(FILE_READ_CHUNK_SIZE)
			return hash.hexdigest()


def sha1_hash_dir(path):
	'''
	Calculate sha1 hash for all files under given directory.
	Argument is instance of pathlib.Path.
	'''

	hashes = {}
	for item in iterdirp(path):
		if item.is_file():
			hashes[item.relative_to(path).as_posix()] = sha1_hash(item)
	return hashes


def compare_files_in_chunks(a, b):
	'''Compare two files in chunks to determine if they differ.'''

	with open(a, 'rb') as a, open(b, 'rb') as b:
		buf_a, buf_b = None, None
		while buf_a == buf_b and len(buf_a) > 0:
			buf_a = a.read(FILE_READ_CHUNK_SIZE)
			buf_b = b.read(FILE_READ_CHUNK_SIZE)
		if len(buf_a) == 0 and len(buf_b) == 0:
			return False
		elif buf_a != buf_b:
			return True


def delete_git_submodule(repo_root, path):
	'''
	Delete a submodule from a Git repository.
	Solution is from https://stackoverflow.com/a/16162000 . Thanks @VonC !
	'''

	from os import getcwd, chdir, path
	import subprocess as sp
	from shutil import rmtree
	with keep_cwd(repo_root):
		sp.run(['git', 'submodule', 'deinit', '-f', '--', path])
		rmtree(path.join(repo_root, path))
		sp.run(['git', 'rm', path])
