import os, sys, requests, piexif, pymysql, hashlib, pytz, datetime
from PIL import Image
from pytz import timezone

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

#from PyQt5 import QtGui, QtWidgets
from PyQt5 import *




class MainWindow(QMainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.setWindowTitle("Crawling Web")
		self.browser = QWebEngineView()
		self.browser.setUrl(QUrl("http://www.google.co.kr"))
		self.setCentralWidget(self.browser)
		self.webpage = QWebEnginePage()

		toolbar = QToolBar("Toolbar")
		self.addToolBar(toolbar)

		#add capture
		capture_screen_action = QAction(QIcon(), "Capture", self)
		capture_screen_action.setToolTip("Capture")
		toolbar.addAction(capture_screen_action)
		capture_screen_action.triggered.connect(self.capture_screen_on)

		#add capture all
		capture_all_screen_action = QAction(QIcon(), "Capture All", self)
		capture_all_screen_action.setToolTip("Capture All")
		toolbar.addAction(capture_all_screen_action)
		capture_all_screen_action.triggered.connect(self.capture_all_screen_on)

		#add lineEdit
		self.le_urlbar = QLineEdit()
		self.le_urlbar.returnPressed.connect(self.no_receive_le_urlbar)
		toolbar.addSeparator()

		toolbar.addWidget(self.le_urlbar)
		self.browser.urlChanged.connect(self.update_le_urlbar)

	#event
	def no_receive_le_urlbar(self):
		q = QUrl(self.le_urlbar.text())
		if q.scheme() == "":
			q.setScheme("http")
		self.browser.setUrl(q)

	def update_le_urlbar(self, q):
		global curURL
		curURL = q.toString()
		self.le_urlbar.setText(q.toString())
		self.le_urlbar.setCursorPosition(0)

	def capture_screen_on(self):
		opt = 0
		self.get_web_data(opt)

	def capture_all_screen_on(self):
		opt = 1
		self.get_web_data(opt)

	#crawling web data
	def get_web_data(self, opt):
		#print(opt)
		self.get_web_src()
		self.capture_web_page(opt)
		self.get_time()
		self.add_exif_field()
		self.hash_jpg_file()
		self.connect_db()  

	#get web source
	def get_web_src(self):
		html = ""
		response = requests.get(curURL)
		if response.status_code == 200:
			html = response.text
		f = open("./html_source.txt", "w", encoding='utf8')
		data = str(html).replace(">",">\n")
		f.write(data)
		f.close()

	#capture web page
	def capture_web_page(self, opt):
		global jpg_name
		if opt == 0:
			size = self.browser.size()
		else:
			print("give me size")
			#size = self.browser.frameGeometry()
			#bsize = self.browser.size()
			#fsize = self.browser.frameSize()
			#msize = self.frameSize()
			#size = self.frameSize()
			#print(size)
			#print(bsize)
			#print(fsize)
			#print(msize)
			#command = "document.body.scrollHeight"
			#print(self.browser.page().runJavaScript("document.body.scrollHeight"))
			#height = self.browser.page().runJavaScript("height = document.body.scrollHeight; alert(height);")
		image = QtGui.QImage(size.width(), size.height(), QtGui.QImage.Format_ARGB32)
		painter = QPainter()
		painter.begin(image)
		self.browser.render(painter)
		painter.end()
		jpg_name = str((str(datetime.datetime.now().year)+ str(datetime.datetime.now().month) + str(datetime.datetime.now().day) + '.jpg'))
		image.save(jpg_name)  

	#get time
	def get_time(self):
		global today, stime
		fmt = '%Y:%m:%d %H:%M:%S'
		seoul = pytz.timezone('Asia/Seoul')
		local_time = seoul.localize(datetime.datetime.now())
		today = str(local_time.strftime(fmt))
		stime = datetime.datetime.now(timezone('Asia/Seoul'))

	#save screenshot
	def add_exif_field(self):
		exif_ifd = {piexif.ExifIFD.DateTimeOriginal: today,
			piexif.ExifIFD.LensMake: u"LensMake",
			piexif.ExifIFD.Sharpness: 65535,
			piexif.ExifIFD.LensSpecification: ((1, 1), (1, 1), (1, 1), (1, 1)),
			}

		exif_dict = {"Exif":exif_ifd}
		exif_bytes = piexif.dump(exif_dict)
		piexif.insert(exif_bytes, jpg_name)

	def connect_db(self):
		conn = pymysql.connect(host='localhost', user='root', password='apmsetup', db='evidence', charset='utf8')
		try:
			with conn.cursor() as cursor:
				print("insert into")
				sql = 'INSERT INTO get_web_data (time, filename, md5, sha1) VALUES (%s, %s, %s, %s)'
				cursor.execute(sql, (stime, jpg_name, md5Hashed, sha1Hashed))
			conn.commit()
		finally:
			conn.close()	

	def hash_jpg_file(self):
		global md5Hashed, sha1Hashed
		of = open(jpg_name, 'rb')
		rf = of.read()
		md5Hash = hashlib.md5(rf)
		md5Hashed = md5Hash.hexdigest()
		sha1Hash = hashlib.sha1(rf)
		sha1Hashed = sha1Hash.hexdigest()


if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	app.exec_()
