#!/usr/bin/python
# __*__ coding: utf-8 _*_

# Dependencies:
# pip install pycrypto


from Crypto.PublicKey import RSA

import sys, keyring, keyring.backend, base64, clipboard, datetime, base64
from splinter import Browser
from base64 import b64decode

import glob
import os
import ConfigParser, io, shutil
import string, random

# Reading and writing the configuration file =============================================
config_file="config.ini"
if os.path.exists(config_file): 
	with open(config_file) as f:
		config_contents = f.read()
		config = ConfigParser.RawConfigParser(allow_no_value=True)
		config.readfp(io.BytesIO(config_contents))
else:
    f = open(config_file, 'w')
    config = ConfigParser.ConfigParser()
    config.add_section('notes')
    config.set('notes', 'notes_backup_path', './backups')
    config.add_section('keys')
    config.set('keys', 'public_path', './keys')
    config.set('keys', 'private_path', '/Volumes/KEY/keys')
    config.add_section('passwords')
    config.set('passwords', 'length', '12')
    config.write(f)
    f.close()

notes_backup_path=config.get('notes', 'notes_backup_path')		
public_keys_dir=config.get('keys', 'public_path')		
private_keys_dir=config.get('keys', 'private_path')	
password_length=int(config.get('passwords', 'length'))	
print(private_keys_dir)

if not os.path.exists(notes_backup_path):
	os.makedirs(notes_backup_path)
if not os.path.exists(public_keys_dir):
	os.makedirs(public_keys_dir)
if not os.path.exists(private_keys_dir):
	os.makedirs(private_keys_dir)

# Styling ================================================================================
def color_it(content, style=False):
	styles={"greenbg":'\33[102m',"red":'\33[91m', "blue":'\33[94m', "bw":'\33[7m', "green":'\33[92m'}
	if not style or style not in styles.keys(): return content
	return styles[style]+content+'\33[0m'

# Encryption =============================================================================
from Crypto.PublicKey import RSA

def backup():
	backup_file=notes_backup_path+"/notes_"+get_latest_keys_file_number()+".txt"
	print backup_file
	if os.path.exists('./notes.txt'): shutil.copy("./notes.txt", backup_file)

def generate_new_key():
	backup()
	private_key = RSA.generate(1024)	
	public_key = private_key.publickey()

	now=str(datetime.datetime.now().microsecond)

	with open (private_keys_dir+"/private_key_"+now+".pem", "wb") as f:
		f.write("{0}".format(private_key.exportKey()))

	with open (public_keys_dir+"/public_key_"+now+".pem", "wb") as f:
		f.write("{0}".format(public_key.exportKey()))
	
	try:
		os.remove("notes.txt")
		print "notes.txt was removed"	
	except:
		print "could not remove notes.txt"
	return public_key, private_key
    
def get_latest_keys_file_number():
	list_of_files = glob.glob(public_keys_dir+'/*') 
	if len(list_of_files)==0: return False
	latest_file = max(list_of_files, key=os.path.getctime)
	return latest_file.split(".")[1].split("_")[2]

	
# Printing tables ========================================================================
def table(dict, title=False, style="greenbg"):
	print color_it("")
	max_length=0
	content=""

	for key, val in dict.items():
		if len(val)+len(key)>max_length:
			max_length=len(val)+len(key)
		content=content+color_it(str(key)+'\t',style)+color_it(val+'\n',style)
	
	if content=="": 
		content=color_it("Empty contents loaded\n", style)
		devider=color_it("="*35+'\t\n',style)
	else:
		devider=color_it("="*(max_length*2+1)+'\t\n',style)
	if title: content=devider+color_it(title+'\n',style)+devider+content+devider
	else: content=devider+content+devider
	return content
	

class Secrets(keyring.backend.KeyringBackend):
	_keys={}
	_links={"google":"https:accounts.google.com"}
	_private_key=""
	_public_key=""
	
	def __init__(self, new=False):
		#return
		if new:
			generate_new_key()
		
		key_file=get_latest_keys_file_number()
		if not key_file:
			generate_new_key()
			key_file=get_latest_keys_file_number()
			
		print color_it("Using %s key file"%key_file, "blue")
		self._private_key = RSA.importKey(open(private_keys_dir+"/private_key_"+key_file+".pem", "rb"))
		self._public_key = RSA.importKey(open(public_keys_dir+"/public_key_"+key_file+".pem", "rb"))
		try:
		
			with open('notes.txt', 'rb') as f:
				for line in f:
					text=self._private_key.decrypt(b64decode(line)) 
					#print "THIS",text
					service, user, password = text.strip().split(':')

					self._keys[(service, user)] = password

		except IOError:
			print color_it("Cannot find notes.txt","red")

	def clear(self):
		self._keys.clear()
		self.update_all()
		self._public_key, self._private_key=generate_new_key()	
	
	def delete(self, service, user):
		try:
			if (service, user) in self._keys:
				self._keys.pop((service, user))	
				self.update_all()
				print color_it("Deleted: %s %s"%(service, user),"red")	
			else:
				print color_it("The key does not exist: %s %s"%(service, user),"red")	
		except IndexError:
			raise keyring.errors.PasswordDeleteError()
	
	def get_password(self, service, user):
		#return keyring.get_password(service, user)
		if (service, user) in self._keys.keys():
			return self._keys.get((service, user))
		else:
			print color_it("The key does not exist: %s %s"%(service, user),"red")	
			return ""

	def get_password_in_clip(self, service, user):
		clipboard.copy(self.get_password(service, user))
	
	def update_all(self):
		try:
			with open("notes.txt", "wb") as f:
				for key, value in self._keys.items():
					text=self._public_key.encrypt(key[0] +":" +key[1]  +":" +value, 57)
					text=base64.b64encode(text[0])
					f.write(text+'\n')
		except Exception, e:
			print "Could not save! ", str(e)
	
	def update_key(self, service, user, password):
		self._keys[(service, user)]=password
		self.update_all()

	def generate_password(self):
		characters = string.ascii_letters + string.digits + '!@#$%^&*()'
		randomness = random.SystemRandom()
		return ''.join(randomness.choice(characters) for i in range(password_length))
	
	def set_password(self, service, user, password):
		# keyring.set_password('twitter', 'ElenaD__', getpass.getpass())
		# keyring.set_password(service, user, password)
		
		if password=="":
			password=self.generate_password()
			print color_it("New password: %s"%password, "blue")
			clipboard.copy(password)
        	
		if (service, user) in self._keys:
			return self.update_key(service, user, password)
			
		self._keys[(service, user)]=password
		try:
			with open("notes.txt", "ab") as f:
				text=self._public_key.encrypt(service+':'+user+':'+password, 57)
				text=base64.b64encode(text[0])
				f.write(text+'\n')
				
			print "Saved: %s"%(str((service, user)))
		except Exception, e:
			print "Could not save! ", str(e)
	
	def browser(self, service):
		print "Opening ",service
		
		try:
			with Browser() as my_browser:
				link=self._links[service]
				my_browser.visit(link)
				if link=='google':
					username_field='username' # identifier
					password_field='password'
		except Exception, e:
			print str(e)
	
	def help(self):
		d={}
		d['Help                  		']="notes.py help"
		d['Get a key             		']="notes.py key"
		d['Get a key in clipboard		']="notes.py key -c"
		d['Set a key             		']="notes.py service key password"
		d['Delete a key             	']="notes.py delete key"
		d['Delete all keys            	']="notes.py clear"
		d['Creating new key files       	']="notes.py new"
		print table(d, "Command line arguments")
		
	def show_all(self):
		print table(self._keys, "Keys stored")
	

def main(argv):

	if argv[0]=="backup" and len(argv)==1:
		backup()
		sys.exit(0)

	if argv[0] in ["new", "n"] and len(argv)==1:
		notes=Secrets(new=True)
		notes.clear()
	else:
		notes=Secrets(new=False)
	keyring.set_keyring(notes)
	# deleting all keys from the keyring
	if len(argv)==0:
		notes.show_all()
	elif argv[0] in ["browser", "open"] and len(argv)==2:
		notes.browser(argv[1])
	elif argv[0] in ["list", "-l"] and len(argv)==1:
		notes.show_all()
	elif argv[0] in ["help", "-h"] and len(argv)==1:
		notes.help()
	elif argv[0] in ["clear", "empty", "cls"] and len(argv)==1:
		notes.clear()
	# deleting one key from the keywring
	elif argv[0] in ["delete","del"] and len(argv)==3:
		notes.delete(argv[1],argv[2])
	elif len(argv)==3 and argv[2] in ["gen", "generate", "-p", "password"]:
		print notes.set_password(argv[0],argv[1], "")
	elif len(argv)==3 and '-c' not in argv:
		print notes.set_password(argv[0],argv[1], argv[2])
	elif len(argv)==3:
		notes.get_password_in_clip(argv[0], argv[1])
	elif len(argv)==2:
		print notes.get_password(argv[0], argv[1])
	else:
		notes.help()	

if __name__=="__main__":
	if len(sys.argv)==1: 
		main(["help"])
	else:
		main(sys.argv[1:])