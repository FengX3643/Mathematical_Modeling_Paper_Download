from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QMessageBox, QFileDialog, QWidget,
                               QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout)
from PySide6.QtUiTools import QUiLoader
import shutil
import requests
from lxml import etree
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import webbrowser
from PySide6.QtCore import Signal,QObject
class mySignal(QObject):
    speed_of_progress_Refresh = Signal(int)
    button_enable = Signal(bool)
    info_tip = Signal(QWidget,str,str)
class paper_downloader:

    def __init__(self):
        # 从文件中加载UI定义

        # 从 UI 定义中动态 创建一个相应的窗口对象
        # 注意：里面的控件对象也成为窗口对象的属性了
        # 比如 self.ui.button , self.ui.textEdit
        self.ui = QUiLoader().load('download.ui')
        self.img_temp_folder = '图片'
        self.check_and_create_folder(self.img_temp_folder)
        self.folder_address = None
        self.ui.pushButton.clicked.connect(self.handleCalc)
        self.ui.pushButton_2.clicked.connect(self.fill_in_the_text_box)
        self.ui.progressBar.setRange(0,100)
        self.ui.pushButton_3.clicked.connect(lambda: webbrowser.open("https://dxs.moe.gov.cn/zx/hd/sxjm/sxjmlw/qkt_sxjm_lw_lwzs.shtml"))
        self.ui.label_3.setOpenExternalLinks(True)
        self.workers = 1
        self.mySignal = mySignal()
        self.mySignal.speed_of_progress_Refresh.connect(self.ui.progressBar.setValue)
        self.mySignal.button_enable.connect(self.ui.pushButton.setEnabled)
        self.mySignal.info_tip.connect(QMessageBox.warning)
    def fill_in_the_text_box(self):
        self.ui.lineEdit_2.setText(self.select_folder())
    def handleCalc(self):
        # 处理按钮点击事件
        url = self.ui.lineEdit.text()
        pdf_path = self.ui.lineEdit_2.text()
        if not url:
            self.mySignal.info_tip.emit(self.ui, '警告', '请输入下载链接')

        else:
            if not pdf_path:
                self.mySignal.info_tip.emit(self.ui, '警告', '请输入保存路径')
                return
            else:
                t = threading.Thread(target=self.down_, args=(url,))
                t.start()


    def get_imgs_thread(self, i, v):
        r = requests.get(v)
        print(f'正在下载第{i}张图片,图片地址为{v}')

        with open(f'{self.img_temp_folder}/{i}.png', 'wb') as f:
            # 对于图片类型的通过r.content方式访问响应内容，将响应内容写入baidu.png中
            f.write(r.content)
    def down_(self, url):
        self.mySignal.button_enable.emit(False)
        txt_url, name = self.get_img_urls(url)
        for index,i in enumerate(txt_url):
            if i[:5] == 'https':
                pass
            else:
                txt_url[index] = 'https://dxs.moe.gov.cn/' + i
        self.txt_url = txt_url
        # 创建线程池
        completed_count = 0
        if self.ui.checkBox.isEnabled:
            self.workers = self.ui.spinBox.value()
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            print("workers:", self.workers)
            future = {executor.submit(self.get_imgs_thread, index, i): index for index, i in enumerate(txt_url)}
            for future_ in as_completed(future):
                try:
                    future_.result()
                except Exception as e:
                    # 窗口提示任务出错

                    self.mySignal.info_tip.emit(self.ui, '警告', f'任务出错: {e}')
                    print(f'任务出错: {e}')
                else:

                    completed_count += 1
                    print(f'已完成 {completed_count} 个任务')
                    self.mySignal.speed_of_progress_Refresh.emit(completed_count/len(txt_url)*99)

        folder_path = self.img_temp_folder
        folder_address = self.ui.lineEdit_2.text()

        output_path = f'{folder_address}//{name}.pdf'
        images = self.get_images(folder_path)
        print(f'正在生成{name}.pdf')
        self.images_to_pdf( images, output_path)
        self.delete_folder_contents(folder_path)
        self.ui.progressBar.setValue(100)
        self.mySignal.info_tip.emit(self.ui, '提示', '下载完成')
        self.mySignal.button_enable.emit(True)
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self.ui, "选择文件夹")
        print(folder_path)
        if folder_path:
            return folder_path
        else:
            return None
    def delete_folder_contents(self,folder_path):
        """删除指定文件夹的全部内容"""
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # 删除文件或链接
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # 递归删除文件夹


    def get_images(self,folder_path):
        imgs = []
        d = len(os.listdir(folder_path))
        for i in range(d):
            imgs.append(f'{folder_path}//{i}.png')
        return imgs


    def images_to_pdf(self, images, output_path):
        """将图片列表输出为PDF文件"""
        c = canvas.Canvas(output_path, pagesize=letter)
        for image_path in images:
            with Image.open(image_path, mode='r') as image:
                width, height = image.size
                aspect_ratio = height / float(width)
                new_height = aspect_ratio * letter[0]
                c.setPageSize((letter[0], new_height))
                c.drawImage(image_path, 0, 0, letter[0], new_height)
                c.showPage()
        c.save()

    def get_img_urls(self,url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Referer": "https://www.google.com/",
            "Accept-Encoding": "gzip, deflate, br"
        }
        response = requests.get(url, headers=headers)
        html = etree.HTML(response.text)
        links = html.xpath('//div[@class="imgslide-wra"]/img/@src')
        name = html.xpath('//html/body/div/div[3]/div[1]/div[2]')
        return links,name[0].text.strip()

    def check_and_create_folder(self,folder_name):
        """
        检查当前文件夹下是否存在指定名称的文件夹，如果不存在则创建它。

        参数:
        folder_name (str): 要检查和创建的文件夹名称，默认为"imgs_temp"。
        """
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print(f"文件夹 '{folder_name}' 已创建。")
        else:
            print(f"文件夹 '{folder_name}' 已存在。")
if __name__ == '__main__':
    app = QApplication([])
    app.setWindowIcon(QIcon('f.ico'))
    paper_downloader = paper_downloader()
    paper_downloader.ui.show()
    app.exec()
    # 打包
    ## pyinstaller 数学建模国赛论文下载器.py --noconsole --icon="f.ico"