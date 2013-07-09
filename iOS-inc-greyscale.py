#!/usr/bin/env python

#-------------------------------------------------------------------------------
# All credits for research that made this tool possible go to
# the oringinal iOS artwork extractor tool from Dave Peck.
# 
# Twitter: @DangerDave
# Website: davepeck.org
# 
# Oringinal tool: http://github.com/davepeck/iOS-artwork/
# 
# To support Dave and keep yourself safe on public wifi on your apple devices
# go to www.getcloak.com.  Cloak is the best way to encrypt your network traffic
# while on open public wireless hotspots
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# iOS-inc-greyscale
# 
# This tool was made to allow for greyscale images to be imported into the iOS
# artwork file.
# 
# It has only been well tested with the Shared@2x.artwork file but should work with
# different artwork files that are layed out the same.
# 
# Please use this tool at your own risk, although we tested it with multiple iOS devices
# including iphone's 4 and 5 and Ipads it could still be improved beyond its current state and
# is not assumed to be anywhere near perfect.
# 
# To run this tool:
# 
#   iOS-inc-greyscale.py "Path/To/artwork.file" "Path/To/New/Artwork/Images" 
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# About the author:
# 
# I made this script to help a theme designer @Jato_BZ and it is functional but
# by no means a reflection of clean and abstracted code, it was made and may be
# maintained in my spare time or by the community.
# 
# If you have any questions feel free to email me at digi.doc.doug@gmail.com, depending on
# my free time I will get back to you as soon as i can.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Thanks to:
# 
# Dave Peck
# @DangerDave
# Initial Research
# Made an awesome tool to base this off
# Dev @ getcloak.com
# 
# Matt Smith
# @Jato_BZ
# Initial tester
# Theme Designer
# iOS advice
# 
# Brian aka King
# @brianmacl
# Initial tester
# 
# Alex aka Alfroggy
# @chezfroggy
# Initial tester
#-------------------------------------------------------------------------------

import os
import sys
import PIL
import struct
import time
from PIL import Image

def tuple_grouper(n, iterable):
    args = [iter(iterable)] * n
    return zip(*args)

def write_bytes(format, value, file):
	#Pack up the byets (B) or Longs (L) etc
	data = struct.pack(format, value)
	file.write(data)
	return 1

def bail(message):
	#Took this from Dave Peck's tool too, thanks Dave
    print "\n%s\n" % message
    sys.exit(-1)

def main():	

	#Vars
	working_dir = os.getcwd()
	dave_pecked_artwork_path = sys.argv[1]
	os_path_seperator = os.sep
	artwork_filename = os.path.basename(dave_pecked_artwork_path)
	new_artwork_file_dir_name = "artwork_greyscale_removed"
	new_artwork_file_dir_path = os.path.join(working_dir, new_artwork_file_dir_name)	
	path_to_new_theme_images = sys.argv[2]
	image_extension_change_from = ".png"
	image_extension_change_to = "@2x.png"

	#Create a new dir to store new .artwork file if it doesnt already exist
	if not os.path.exists(new_artwork_file_dir_path):
		os.makedirs(new_artwork_file_dir_path)

	#Create the new artwork file
	new_file = open(os.path.join(new_artwork_file_dir_path, artwork_filename), 'wb')

	#Open the recompiled artowrk file
	old_file = open(dave_pecked_artwork_path, 'rb')
	old_file_data = old_file.read()

	#Get some core variables
	total_img_count = struct.unpack('L',old_file_data[0:4])[0]
	offset_to_information_array = struct.unpack('L',old_file_data[4:8])[0]
	offset_to_name_array = struct.unpack('L',old_file_data[8:12])[0]

	#Write the name array information up until one byte before the first image data offset
	first_image_offset = struct.unpack("L", old_file_data[offset_to_information_array + 8:offset_to_information_array + 12])[0]
	
	#Write header to new file
	write_bytes("L", total_img_count, new_file)
	write_bytes("L", offset_to_information_array, new_file)
	write_bytes("L", offset_to_name_array, new_file)

	#Write unknown part of header before information array
	bcount = 0
	while bcount < (offset_to_information_array - 12):
		b = struct.unpack("B",  old_file_data[(12+bcount):(12+bcount+1)])[0]
		write_bytes("B", b, new_file)
		bcount += 1

	#Get a list of filenames
	image_names = ()
	image_name = ""
	incount = 0
	bcount = 0
	while incount < total_img_count:
		iname = struct.unpack("c", old_file_data[(offset_to_name_array + bcount):(offset_to_name_array + bcount + 1)])
		bcount += 1
		#If the byte isnt a \x00 (Seperates image names) then add the image name letter to the last name
		if iname[0] != "\x00":
			image_name += iname[0]
		else:
			image_names = image_names + (image_name,)
			image_name = ""
			incount += 1

	#Read the old information array
	offset_addition = 0
	icount = 0
	rioacount = 0
	greyscale_image_names = ()
	new_offset = 0
	previous_bytes_written = 0
	pad_byte_test = 0
	bytes_to_pad = 4

	while icount < total_img_count:

		#Vars
		rgba_pixel_count = 0
		greyscale_pixel_count = 0

		#Get image meta
		flags, width, height, offset = struct.unpack("LHHL", old_file_data[(offset_to_information_array+(12*icount)):(offset_to_information_array+(12*icount)+12)])

		#See if the replacement image exists
		ipath = os.path.join(path_to_new_theme_images, image_names[icount].replace(image_extension_change_from, image_extension_change_to))
		
		if(os.path.isfile(ipath)):
			
			#Check if the replacement image is greyscale or not
			img = Image.open(ipath)
			
			#Dave pecks tool seems to export all as images as RGBA
			#so you should be fine but just to double check the mode
			if(img.mode == "RGBA"):

				#Change the flag to RGBA
				flags = 0
				
				#Work out the amount of bytes needed for an RGBA version of this image
				rgba_pixel_count = (width * height) * 4				
				
				#Work out the amount to add to the new_offset for the extra pixels
				if icount == 0:
					
					#For the first image add nothing as no pixel data has come before it
					new_offset = first_image_offset

				else:

					#Add up the first image offset plus all previous pixel data to get the new offset
					new_offset = first_image_offset + previous_bytes_written
				
				#Update the previous_bytes_written for the next image's new_offset
				previous_bytes_written = previous_bytes_written + rgba_pixel_count
 
			else:

				#For non greyscale image store all of there names to throw an error
				greyscale_image_names = greyscale_image_names + (image_names[icount],)

		#If there are any greyscale images throw an error echo'ing out the names of the greyscale images
		if len(greyscale_image_names) > 0:
			print "\r\nSome images being imported are not in RGBA"
			print "All images being imported must be in RGBA"
			print "\r\nImages:\r\n"
			for giname in greyscale_image_names:
				print giname
			bail("")
				

		#Write the information array bytes
		write_bytes("L", flags, new_file)
		write_bytes("H", width, new_file)
		write_bytes("H", height, new_file)
		write_bytes("L", new_offset, new_file)
		icount += 1

	#End information array loop
	
	#Fill in the unknown bytes leading up to the name array (Seemingly always just empty padding) until the name array.
	#These bytes might not even matter.  Get the current byte count of new file so we know
	#where to start adding in bytes then write the unknown (seemingly empty padding space)
	#bytes up until the name array
	start_at_offset = new_file.tell()
	bcount = 0
	while bcount < (offset_to_name_array - start_at_offset):
		b = struct.unpack("B",  old_file_data[(start_at_offset+bcount):(start_at_offset+bcount+1)])[0]
		write_bytes("B", b, new_file)
		bcount += 1	

	#Do the same as above for all unknown bytes before the first image offset
	start_at_offset = new_file.tell()
	bcount = 0
	while bcount < ((first_image_offset - start_at_offset)):
		b = struct.unpack("B",  old_file_data[(start_at_offset+bcount):(start_at_offset+bcount+1)])[0]
		write_bytes("B", b, new_file)
		bcount += 1

	#Loop through the images in the image name array
	icount = 0
	for iname in image_names:
		#Make sure the image exists
		ipath = os.path.join(path_to_new_theme_images, image_names[icount].replace(image_extension_change_from, image_extension_change_to))
		if(os.path.isfile(ipath)):

			#Open the image to import and get its size
			img = Image.open(ipath)
			width, height = img.size
			
			for y in xrange(height):
				for x in xrange(width):
					r, g, b, a = img.getpixel((x, y))
					#handle premultiplied alpha - this came from Dave Pecks tool from one of his users
					#as per normal credit goes out to Dave Peck (https://github.com/davepeck) and his user
					#that posted a comment to fix this (https://github.com/cwalther)
					r = (r * a + 127) // 255
					g = (g * a + 127) // 255
					b = (b * a + 127) // 255									
					write_bytes("B", b, new_file)
					write_bytes("B", g, new_file)
					write_bytes("B", r, new_file)
					write_bytes("B", a, new_file)

			#About time to give the user some feedback
			print "Adding " + str(icount+1) + "/" + str(total_img_count) + ", name: " + image_names[icount]

		else:
			bail("Image " + iname + " not found :( Had to exit, soz")
		icount += 1

	print '\r\n--All done adding colour pixel data in-place of greyscale pixel data--\r\n'
	time.sleep(10)

if __name__ == "__main__":
    main()