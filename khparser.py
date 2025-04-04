import requests
# import html
from bs4 import BeautifulSoup as bs
# from subprocess import run
from os.path import dirname, abspath, join#, exists
from os import system
from os import environ, startfile
import sys
from sys import argv
from subprocess import run, PIPE, Popen
from gallery_dl.job import DownloadJob as dl
from gallery_dl import config
from gallery_dl.job import DataJob as DJ

def fzf_filter(input_func, fzf_options:str=''):
	# set fzf option env var and spawn fzf process
	env = environ.copy()
	env['FZF_DEFAULT_OPTS'] = fzf_options
	process = Popen('fzf --layout=reverse', text=True, env=env, stdin=PIPE, stdout=PIPE, encoding='utf-8')

	# save original sys.stdout and redirect sys.stdout to fzf.stdin
	original_stdout = sys.stdout
	sys.stdout = process.stdin

	input_func()	# print input_func results to stdout (currently fzf.stdin)

	# pipe to fzf done: close fzf.stdin and return sys.stdout to original
	process.stdin.close()
	sys.stdout = original_stdout

	# read fzf.stdout and return the results
	results = process.stdout.read().splitlines()
	process.stdout.close()
	return results

def change_format(current_format):
	inp = fzf_filter(
		lambda: print('\n'.join([
			'1. mp3',
			'2. flac (if exists, fallback to mp3 otherwise)'])),
		fzf_options='--reverse --header="Select Format (current=%s)" --bind=\'esc:clear-query\'' % current_format)
	if not len(inp):
		return current_format
	inp = inp[0][0:1]
	match inp:
		case '1':
			download_format = 'mp3'
			config.set(("extractor", "khinsider"), "format", "mp3")
		case '2':
			download_format = 'flac'
			# gallery_dl_options = '--write-metadata -o format=flac -d ' + download_location
			config.set(("extractor", "khinsider"), "format", "flac")
	return download_format

def dl_loc(name=''):
	pwd = dirname(abspath(argv[0]))
	download_location = join(pwd, 'downloads', 'khinsider', name)
	return download_location

def download(url):
	print('\033[96m' + '\nDOWNLOADING ' + '\033[0m' + url)
	tmp_file = join(environ['TMP'], 'khparser_tmp')
	with open(tmp_file, 'w') as file:
		DJ(url, file=file).run()
		# print('urljob done')

	urls = []
	with open(tmp_file, 'r') as file:
		from json import load
		data = load(file)
		for item in data:
			if item[0] == 2:
				name = item[1]['album']['name']
				name = "".join(i for i in name if i not in "\\/:*?<>|")
			elif item[0] == 3 and type(item[1]) == type(''):
				urls.append(item[1])

	with open(tmp_file, 'w') as file:
		file.write('\n'.join(urls))

	run(['aria2c', 
		'--dir=%s' % dl_loc(name), 
		'--max-concurrent-downloads=1', 
		'--connect-timeout=60', 
		'--max-connection-per-server=16',
		'--split=16',
		'--min-split-size=1M',
		'--human-readable=true',
		'--download-result=full',
		'--file-allocation=none',
		'--conditional-get',
		'-i %s' % tmp_file])
	system('del "%s"' % tmp_file)
	startfile(dl_loc(name))

def main():
	config.load()
	# gallery_dl_path = join(pwd, 'gallery-dl.exe')
	# print('gallery-dl path:', gallery_dl_path)
	# if not exists(gallery_dl_path):
	# 	inp = input('ERR: gallery-dl not found in current directory')
	# 	return
		
	download_format = 'flac'
	# gallery_dl_options = '--write-metadata -o format=flac -d ' + download_location
	config.set(("extractor", "khinsider"), "format", "flac")
	# config.set(("extractor", "khinsider"), "base-directory", download_location)

	while True:
		system('cls')
		modes = fzf_filter(
			lambda: print('\n'.join([
				'1. Search Khinsider',
				'2. Paste URL(s)',
				'3. Change download format (current=%s)' % download_format])),
			fzf_options='--reverse --header="Select Mode" --bind=\'esc:clear-query\'')

		if len(modes)==0:
			return
		mode = modes[0][0:1]

		match mode:
			case '3':
				download_format = change_format(download_format)
			case '2':
				inp = input('URL(s): ')
				inp = inp.strip()
				if not inp:
					continue
				urls = inp.split()
				for url in urls:
					download(url)
			case '1':
				inp = input('Search khinsider: ')
				inp = inp.strip()
				if not inp:
					continue
				request = 'https://downloads.khinsider.com/search?search=%s&sort=timestamp' % inp
				r = requests.get(request)
				soup = bs(r.text,'html.parser')
				links = {}
				url_base = 'https://downloads.khinsider.com'
				for link in soup.find_all('a'):
					link_text = link.get('href')
					if link_text and link_text.find('/album/') != -1:
						if link.string:
							links[link.string] = url_base + link_text

				selected = fzf_filter(
						lambda: print('\n'.join([file for file in links])),
						fzf_options='\
							--reverse \
							--header="Select album(s) to download:" \
							--wrap \
							--multi \
							--bind=\'esc:clear-query,ctrl-a:select-all,ctrl-d:deselect-all\'')
				if len(selected) == 0:
					continue
				for file in selected:
					download(links[file])

				p=input('\nDONE. Press any key...\n')

try:
	main()
except KeyboardInterrupt:
	pass