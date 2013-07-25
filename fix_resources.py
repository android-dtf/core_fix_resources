#!/usr/bin/python

from lxml import etree
import os
import sys
import re

# Python script to resolve resource identifiers in disassembled Android applications.
# Jake Valletta, 2013

# ###########################
# Printing Functions

# Print message if debugging is enabled
def debug(msg):
   if DEBUGGING:
      print "[DEBUG] %s" % (msg)

# Print error and exit
def error(msg):
   print "[ERROR] %s" % (msg)
   exit(-1)

# Print a warning and continue
def warning(msg):
   print "[WARNING] %s" % (msg)

# ###########################
# Configurable Parameters

DEBUGGING = False	# Enable verbose messages
STR_DISPLAY_LEN = 25 	# Set string message display truncation

# ############################
# Main Program

if len( sys.argv ) != 2: exit("Usage: %s <project_root>" % sys.argv[0])

project_dir             = sys.argv.pop().rstrip("/")

public_file_path	= "/res/values/public.xml"
string_file_path	= "/res/values/strings.xml"
smali_file_path		= "/smali"

public_file             = project_dir + public_file_path
string_file 		= project_dir + string_file_path
smali_files 		= project_dir + smali_file_path

public_dict		= {}
has_strings		= False

print "Parsing ./res/values/public.xml..."
try:
   for _, element in etree.iterparse(public_file):
      if element.tag == "public":

         try:
            res_id = element.attrib['id']
			   
	    debug("Adding new public resource value %s" % (res_id))
	    public_dict[int(res_id, 16)] = [element.attrib['name'], element.attrib['type']]
			   
	    if element.attrib['type'] == "string":
	       has_strings = True
			
         except KeyError:
            warning("KeyError exception iterating public.xml. Skipping entry.")
		
      # Clear the element from memory
      element.clear()

except IOError:
   error("\"%s\" file not found!" % (public_file_path))

if has_strings:
   
   try:
      print "Parsing ./res/values/strings.xml..."
   
      for _, element in etree.iterparse(string_file):
   
         if element.tag == "string":
            
            try:
               string_name = element.attrib['name']
               for pub in public_dict.keys(): 
                  if public_dict[pub][0] == string_name and public_dict[pub][1] == "string":
                     debug("Adding string details to resource %s (0x%08x)" % (string_name, pub))
	             public_dict[pub].append(element.text)
            
            except KeyError:
               warning("KeyError exception iterating strings.xml. Skipping entry.")
         
         # Clear the element from memory
         element.clear()   

   except IOError:
      error("\"%s\" file not found!" % (string_file_path))

print "Making modifications to files in ./smali/*..."
for root, subFolders, files in os.walk(smali_files):

   for filename in files:
      file_path = os.path.join(root, filename)

      if re.search(".*\.smali$", file_path) and file_path != 'R.smali':

         data=''
         file_modded = False

         for line in re.split("\n", open(file_path).read()):

            # First do "const-string" instances
            if re.search("const[ \/\-].*0x[a-fA-F0-9]{4,8}$", line):

               # Get the actual value
               res_value = line[line.find(",")+2: len(line)]

               # To save space, some are const/high16
               if line.find("high16") != -1:
                  res_value_int = int(res_value+"0000", 16)

               else:
                  res_value_int = int(res_value, 16)

               # Determine if this is a value in our list
               if res_value_int in public_dict.keys():
                  debug("We found a resource identifier: %s [%s]" % (res_value, file_path))

                  line_len = len(line)
                  line = line +"\t#Public value \'%s\' (type=%s)" % (public_dict[res_value_int][0], public_dict[res_value_int][1])

                  if len( public_dict[res_value_int] ) == 3:
                     string_value = public_dict[res_value_int][2]
                     formatted_string_value = string_value[0:STR_DISPLAY_LEN] + ("..." if len(string_value) > STR_DISPLAY_LEN else "")
                     line += "\n%s\t#%s = \"%s\"" % (" " * line_len, public_dict[res_value_int][0], formatted_string_value)

                  file_modded = True

            # Now check for "packed-switch" instances
            elif re.search("\.packed-switch 0x[a-fA-F0-9]{4,8}$", line):
               
               res_value = line[line.find("0x"): len(line)]
               res_value_int = int(res_value, 16)

               # Determine if this is a value in our list
               if res_value_int in public_dict.keys():
                  debug("We found a packed-switch resource identifier: %s [%s]" % (res_value, file_path))

                  line = line +"\t#Public value \'%s\' (type=%s)" % (public_dict[res_value_int][0], public_dict[res_value_int][1])

                  file_modded = True
     
            # Add the new data to a buffer
            data+=line+"\n"

         if file_modded == True:
            output = open(file_path, 'w')
            output.write(data.encode('utf-8'))
            debug("Changes applied to file \'%s\'" % (file_path))
            output.close()

print "Complete!"
