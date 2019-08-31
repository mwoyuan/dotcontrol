import os
from pathlib import Path
from .util import link_dir


class Dot:
	def __init__(self, profile, path, create=True):
		self.profile = profile
		self.resolve_path(path)

		if self.normalized_origin_path in profile.config['dots']:
			self.load()
		else:
			if create:
				self.create()
	
	def load(self):
		self.data = self.profile.config['dots'][self.normalized_origin_path]
	
	def save(self):
		self.profile.save()
	
	def create(self):
		from .const import DOT_DATA_TEMPLATE
		self.data = self.profile.config['dots'][self.normalized_origin_path] = DOT_DATA_TEMPLATE.copy()
		if self.absolute_origin_path.is_dir():
			self.type = 'dir'
		elif self.absolute_origin_path.is_file():
			self.type = 'file'
		self.update_sha1_check()


	def resolve_path(self, raw_origin_path):
		self.raw_origin_path = raw_origin_path
		self.absolute_origin_path = Path(raw_origin_path).expanduser().resolve()
		
		try:
			relative_to_home = self.absolute_origin_path.relative_to(self.profile.control.user_home)
			self.normalized_origin_path = Path('~').joinpath(relative_to_home).as_posix()
			self.dot_path = self.profile.dot_home_path.joinpath(relative_to_home)
		except:
			self.normalized_origin_path = self.absolute_origin_path.as_posix()
			self.dot_path = self.profile.dot_root_path.joinpath(self.normalized_origin_path)

	def link_dot(self):
		'''Link origin to dot path.'''
		from .util import mkdirp

		mkdirp(self.dot_path.parent)

		if self.dot_exists:
			self.dot_path.unlink()
		
		if self.type == 'file':
			os.link(self.absolute_origin_path, self.dot_path)
		elif self.type == 'dir':
			link_dir(self.absolute_origin_path, self.dot_path)

		self.update_sha1_check()

	def link_back(self, overwrite=False):
		'''Link dot back to origin, for actions like activating a profile.'''

		if self.origin_exists:
			if overwrite:
				self.absolute_origin_path.unlink()
			else:
				raise Exception('Origin {} already exists!'.format(self.normalized_origin_path))

		if self.type == 'file':
			os.link(self.dot_path, self.absolute_origin_path)
		elif self.type == 'dir':
			link_dir(self.dot_path, self.absolute_origin_path)

	def unlink(self):
		if self.dot_exists():
			if self.type == 'file':
				self.unlink()
			elif self.type == 'dir':
				from shutil import rmtree
				rmtree(self.dot_path)

	def delete(self):
		if self.dot_exists:
			self.dot_path.unlink()
		self.profile.config['dots'].pop(self.normalized_origin_path, None)
		self.profile.save()

	def sha1_hash(self):
		if self.type == 'file':
			from .util import sha1_hash
			return sha1_hash(self.absolute_origin_path)
		elif self.type == 'dir':
			from .util import sha1_hash_dir
			return sha1_hash_dir(self.absolute_origin_path)
	
	def update_sha1_check(self):
		from .util import now
		self.data['sha1'] = self.sha1_hash()
		self.data['last_sha1_check'] = now()
		self.save()

	@property
	def changed(self):
		return self.sha1_hash() != self.data['sha1']

	@property
	def origin_exists(self):
		return self.absolute_origin_path.exists()
	
	@property
	def dot_exists(self):
		return self.dot_path.exists()

	def __getattr__(self, name):
		return self.data[name]
