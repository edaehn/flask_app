#!/usr/bin/python
# __*__ coding: utf-8 _*_

# Dependencies:
# 1. brew:
# /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
# 2. geckodriver:
# brew install geckodriver

import sys, keyring, keyring.backend, base64, clipboard
from splinter import Browser

# Styling
def color_it(content, style=False):
	styles={"greenbg":'\33[102m',"red":'\33[91m', "blue":'\33[94m', "bw":'\33[7m', "green":'\33[92m'}
	if not style or style not in styles.keys(): return content
	return styles[style]+content+'\33[0m'

# Printing table
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
	
	def __init__(self):
		try:
		
			with open('notes.txt', 'r') as f:
				for line in f:
					service, user, password = base64.decodestring(line).strip().split(':')
					self._keys[(service, user)] = password


		except IOError:
			print color_it("Cannot find notes.txt","red")

	def clear(self):
		self._keys.clear()
		self.update_all()
	
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
			with open("notes.txt", "w") as f:
				for key, value in self._keys.items():
					f.write(base64.encodestring(key[0] +":" +key[1]  +":" +value))
		except Exception, e:
			print "Could not save! ", str(e)
	
	def update_key(self, service, user, password):
		self._keys[(service, user)]=password
		self.update_all()
	
	def set_password(self, service, user, password):
		# keyring.set_password('twitter', 'ElenaD__', getpass.getpass())
		# keyring.set_password(service, user, password)
        
		if (service, user) in self._keys:
			return self.update_key(service, user, password)
			
		self._keys[(service, user)]=password
		try:
			with open("notes.txt", "a") as f:
				f.write(base64.encodestring(service+":"+user+":"+password))
				
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
		print table(d, "Command line arguments")
		
	def show_all(self):
		print table(self._keys, "Keys stored")
	

def main(argv):
	notes=Secrets()
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
	elif len(argv)==3 and '-c' not in argv:
		print notes.set_password(argv[0],argv[1], argv[2])
	elif len(argv)==3:
		notes.get_password_in_clip(argv[0], argv[1])
	elif len(argv)==2:
		print notes.get_password(argv[0], argv[1])
	else:
		notes.help()	

if __name__=="__main__":
	main(sys.argv[1:])