import requests
# import html
from bs4 import BeautifulSoup as bs
# from subprocess import run
from os.path import dirname, abspath, join#, exists
from sys import argv
from gallery_dl.job import DownloadJob as dl
from gallery_dl import config

def main():
	config.load()
	pwd = dirname(abspath(argv[0]))
	# gallery_dl_path = join(pwd, 'gallery-dl.exe')
	# print('gallery-dl path:', gallery_dl_path)
	# if not exists(gallery_dl_path):
	# 	inp = input('ERR: gallery-dl not found in current directory')
	# 	return
		
	download_location = join(pwd, 'downloads')
	download_format = 'flac'
	# gallery_dl_options = '--write-metadata -o format=flac -d ' + download_location
	config.set(("extractor", "khinsider"), "format", "flac")
	config.set(("extractor", "khinsider"), "base-directory", download_location)

	while True:
		print('Select Mode')
		print('1. Search Khinsider')
		print('2. Paste URL(s)')
		print('3. Change download format (current=' + download_format + ')')
		mode = input('> ')

		if mode.strip() == '3':
			print('Select Format')
			print('1. mp3')
			print('2. flac (if exists, otherwise mp3)')
			inp = input('> ')
			if inp.strip() == '1':
				download_format = 'mp3'
				# gallery_dl_options = '--write-metadata -o format=mp3 -d ' + download_location
				config.set(("extractor", "khinsider"), "format", "mp3")
			elif inp.strip() == '2':
				download_format = 'flac'
				# gallery_dl_options = '--write-metadata -o format=flac -d ' + download_location
				config.set(("extractor", "khinsider"), "format", "flac")
			else:
				print('Invalid input. Nothing changed.')

		if mode.strip() == '2':
			inp = input('URL(s): ')
			urls = inp.split()
			for url in urls:
				print('\nDownloading ' + url)
				# run_command = ' '.join([gallery_dl_path, gallery_dl_options, url])
				# run(run_command)
				dl(url).run()

		elif mode.strip() == '1':
			p=input('Search khinsider: ')
			request = 'https://downloads.khinsider.com/search?search=' + p + '&sort=timestamp'
			r = requests.get(request)
			soup = bs(r.text,'html.parser')
			links = {}
			for link in soup.find_all('a'):
				link_text = link.get('href')
				if link_text.find('/album/') != -1:
					if link.string:
						links[link.string] = link_text

			idx = 0
			urls = []
			url_base = 'https://downloads.khinsider.com'
			for name in links:
				idx += 1
				print(str(idx) + ') ' + name)
				urls.append(url_base + links[name])

			while True:
				p=input('Download (space separated, 0=all, r=reset): ')
				if p=='r':
					break
				if p=='0':
					downloads=urls
				else:
					dl_ids = p.split()
					downloads=[]
					for id in dl_ids:
						try:
							if int(id)<=len(urls) and int(id)>0:
								downloads.append(urls[int(id)-1])
						except:
							pass

				for url in downloads:
					print('\nDownloading ' + url)
					# run_command = ' '.join([gallery_dl_path, gallery_dl_options, url])
					# run(run_command)
					dl(url).run()

				p=input('\nDONE. Press any key...\n')
		print('\n=========================')

main()