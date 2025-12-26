#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pathlib

# 将项目根目录添加到Python路径中，解决模块导入问题
if getattr(sys, 'frozen', False):
    # 打包后的环境
    project_root = os.path.dirname(sys.executable)
else:
    # 开发环境
    project_root = str(pathlib.Path(__file__).parent.parent)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 首先导入并调用抑制功能，确保在任何子进程调用之前执行
from src.utils import utils
utils.suppress_libpng_warnings()
utils.suppress_subprocess_windows()

# 然后再导入其他模块
import random
from datetime import timedelta

# 导入模块化组件
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread

# 导入自定义模块
from src.utils import cache_utils
from src.threads import worker_threads
from src.core import audio_processor
from src.ui import ui_components

# 在抑制子进程窗口后再导入pydub
from pydub import AudioSegment

# 获取程序运行的目录（处理打包后的情况）
if getattr(sys, 'frozen', False):
    # 打包后的环境
    program_dir = os.path.dirname(sys.executable)
else:
    # 开发环境 - 获取src目录的父目录作为项目根目录
    src_dir = os.path.dirname(os.path.abspath(__file__))
    program_dir = os.path.dirname(src_dir)

# 切换到程序运行目录
os.chdir(program_dir)

class MusicCutterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 初始化UI组件
        self.ui = ui_components.UiComponents(self)
        
        # 初始化应用程序状态
        self.file_list = []
        self.countdown_file = None
        self.splicing_thread = None
        
        # 并发功能控制 - 默认为启用
        self.use_concurrency = True  # 控制是否使用并发功能的实例变量
        
        # 音频缓存 - 存储已加载和处理的音频段，使用LRU缓存限制最大100个文件
        self.audio_cache = cache_utils.LRUCache(capacity=100)
        
        # 时长缓存 - 存储音频文件的时长信息
        self.duration_cache_file = os.path.join(program_dir, "duration_cache.json")
        
        # 先加载时长缓存
        self.duration_cache = cache_utils.load_duration_cache(self.duration_cache_file)
        
        # 曲库目录相关属性
        self.library_dir = os.path.join(program_dir, "曲库")  # 根目录下固定名为"曲库"的目录
        self.library_files = set()  # 曲库中的所有音频文件路径（使用集合以便快速查找）
        
        # 初始化音频处理器
        self.audio_processor = audio_processor.AudioProcessor(
            audio_cache=self.audio_cache,
            duration_cache=self.duration_cache,
            duration_cache_file=self.duration_cache_file,
            program_dir=program_dir
        )
        
        # 自动加载根目录下的倒计时音频
        self.auto_load_countdown()
        
        # 启动后台线程加载曲库和随舞文件，避免阻塞UI
        self.start_background_loading()
        
    def auto_load_countdown(self):
        """自动加载当前目录下的倒计时音频文件"""
        # 获取当前工作目录
        current_dir = os.getcwd()
        
        # 检查所有可能的倒计时文件名和扩展名
        countdown_filenames = [
            "倒计时.mp3", "倒计时.MP3"
        ]
        
        for filename in countdown_filenames:
            countdown_path = os.path.join(current_dir, filename)
            if os.path.exists(countdown_path):
                self.countdown_file = countdown_path
                self.countdown_label.setText(filename)
                self.countdown_label.setStyleSheet("color: #000;")
                self.status_label.setText("已自动加载当前目录下的倒计时音频")
                break
                
    def load_duration_cache(self):
        """从JSON文件加载时长缓存"""
        self.duration_cache = cache_utils.load_duration_cache(self.duration_cache_file)
        self.status_label.setText(f"已加载时长缓存，共 {len(self.duration_cache)} 个文件")
        
    def start_background_loading(self):
        """启动后台线程加载曲库文件，避免阻塞UI（移除随舞目录自动加载）"""
        # 创建后台加载线程
        self.background_thread = QThread()
        self.background_worker = worker_threads.BackgroundLoader(
            load_library_func=self.load_library_files,
            load_dance_func=None  # 移除随舞目录自动加载
        )
        
        # 将工作对象移动到线程中
        self.background_worker.moveToThread(self.background_thread)
        
        # 连接信号和槽
        self.background_thread.started.connect(self.background_worker.run)
        self.background_worker.finished.connect(self.background_thread.quit)
        self.background_worker.finished.connect(self.background_worker.deleteLater)
        self.background_thread.finished.connect(self.background_thread.deleteLater)
        
        # 连接进度和状态信号
        self.background_worker.progress_updated.connect(self.progress_bar.setValue)
        self.background_worker.status_updated.connect(self.status_label.setText)
        
        # 加载完成后隐藏进度条
        self.background_worker.finished.connect(self.hide_progress_bar)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        
        # 启动线程
        self.background_thread.start()
    
    def hide_progress_bar(self):
        """加载完成后隐藏进度条"""
        self.progress_bar.setVisible(False)

    def load_library_files(self, progress_signal=None, status_signal=None):
        """加载根目录下固定名为"曲库"的目录中的所有音频文件"""
        self.audio_processor.load_library_files(progress_signal, status_signal)
        
    def auto_load_dance_files(self, show_dialogs=True, progress_signal=None, status_signal=None):
        """自动读取随舞目录下的所有音频文件并随机排序"""
        try:
            dance_files = self.audio_processor.auto_load_dance_files(progress_signal, status_signal, self.use_concurrency)
            
            if dance_files:
                # 清空当前列表
                self.file_list_widget.clear()
                self.file_list = []
                
                # 优化：直接添加文件到列表，不预加载完整音频
                for file_path in dance_files:
                    # 只添加到列表和列表控件，不预加载完整音频
                    self.file_list.append(file_path)
                    self.file_list_widget.addItem(os.path.basename(file_path))
                
                # 计算预计总时长并更新状态栏
                total_seconds = self.audio_processor.calculate_total_duration(
                    dance_files, 
                    self.countdown_file
                )
                duration_str = str(timedelta(seconds=int(total_seconds)))
                
                if show_dialogs:
                    self.status_label.setText(f"已加载{len(dance_files)}个音频文件，预计总时长：{duration_str}")
                    QMessageBox.information(self, "加载完成", f"已自动加载{len(dance_files)}个音频文件")
                else:
                    self.status_label.setText(f"已加载{len(dance_files)}个音频文件")
                
                # 无论是否显示对话框，都更新预计时长标签
                self.update_duration_label()
            else:
                if show_dialogs:
                    QMessageBox.warning(self, "加载失败", "随舞目录下未找到音频文件")
        except Exception as e:
            error_msg = f"加载随舞文件失败：{e}"
            self.status_label.setText(error_msg)
            if show_dialogs:
                QMessageBox.critical(self, "加载失败", error_msg)

    def toggle_concurrency(self, state):
        """切换并发功能的启用状态"""
        self.use_concurrency = (state == Qt.Checked)
        self.status_label.setText(f"并发功能{'已启用' if self.use_concurrency else '已禁用'}")
    
    def add_files(self):
        """添加音频文件到列表"""
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", "", 
            "音频文件 (*.mp3 *.wav *.flac *.ogg *.aac *.m4a *.wma);;所有文件 (*)",
            options=options
        )
        
        if files:
            added_count = 0
            for file_path in files:
                if self.add_to_list(file_path):
                    added_count += 1
            
            # 更新状态
            self.status_label.setText(f"已添加{added_count}个音频文件")
            self.update_duration_label()
    
    def add_to_list(self, file_path):
        """将单个文件添加到列表"""
        try:
            # 预加载音频文件
            self.audio_processor.preload_audio(file_path)
            
            # 添加到列表
            self.file_list.append(file_path)
            self.file_list_widget.addItem(os.path.basename(file_path))
            return True
        except Exception as e:
            print(f"添加文件失败 {os.path.basename(file_path)}: {e}")
            return False
    
    def remove_file(self):
        """移除选中的文件"""
        current_item = self.file_list_widget.currentItem()
        if current_item:
            row = self.file_list_widget.row(current_item)
            self.file_list_widget.takeItem(row)
            del self.file_list[row]
            self.status_label.setText("已移除选中文件")
            self.update_duration_label()
    
    def clear_playlist(self):
        """清空播放列表"""
        if self.file_list_widget.count() > 0:
            self.file_list_widget.clear()
            self.file_list = []
            self.status_label.setText("已清空播放列表")
            self.update_duration_label()
    
    def update_duration_label(self):
        """更新预计时长标签"""
        print(f"更新时长标签，文件列表：{self.file_list}")
        print(f"文件列表长度：{len(self.file_list)}")
        total_seconds = self.audio_processor.calculate_total_duration(
            self.file_list, 
            self.countdown_file
        )
        print(f"计算得到的总时长：{total_seconds}")
        duration_str = str(timedelta(seconds=int(total_seconds)))
        print(f"格式化后的时长：{duration_str}")
        self.duration_label.setText(f"预计时长：{duration_str}")
    
    def eventFilter(self, obj, event):
        """处理拖放事件"""
        if obj == self.file_list_widget:
            if event.type() == event.DragEnter:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True
            elif event.type() == event.Drop:
                urls = event.mimeData().urls()
                added_count = 0
                for url in urls:
                    file_path = url.toLocalFile()
                    if self.add_to_list(file_path):
                        added_count += 1
                
                # 更新状态
                if added_count > 0:
                    self.status_label.setText(f"已添加{added_count}个音频文件")
                    self.update_duration_label()
                return True
        return super().eventFilter(obj, event)
    
    def select_countdown(self):
        """选择倒计时音频文件"""
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(
            self, "选择倒计时音频", "", "音频文件 (*.mp3 *.wav *.flac *.ogg *.aac *.m4a *.wma);;所有文件 (*)",
            options=options
        )
        
        if file:
            self.countdown_file = file
            self.countdown_label.setText(os.path.basename(file))
            self.countdown_label.setStyleSheet("color: #000;")
            self.status_label.setText("已选择倒计时音频文件")
            self.update_duration_label()
    
    def merge_audio(self):
        """拼接音频文件"""
        if not self.file_list:
            QMessageBox.warning(self, "拼接失败", "请先添加音频文件")
            return
        
        # 选择输出文件
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(
            self, "保存拼接后的音频", "output.mp3", "MP3文件 (*.mp3);;所有文件 (*)",
            options=options
        )
        
        if file:
            # 确保输出文件是MP3格式
            if not file.lower().endswith('.mp3'):
                file += '.mp3'
            
            # 禁用按钮避免重复点击
            self.merge_button.setEnabled(False)
            self.status_label.setText("开始拼接音频...")
            
            # 获取拼接模式
            mode = "sequential"
            if self.mode_combo.currentText() == "随机拼接":
                mode = "random"
            
            # 创建并启动拼接线程
            self.splicing_thread = worker_threads.SplicingThread(
                file_list=self.file_list,
                mode=mode,
                countdown_file=self.countdown_file,
                output_file=file,
                cache=self.audio_cache,
                use_concurrency=self.use_concurrency
            )
            
            # 连接信号
            self.splicing_thread.progress_updated.connect(self.progress_bar.setValue)
            self.splicing_thread.progress_updated.connect(self.handle_progress_for_save_bar)
            self.splicing_thread.save_progress_updated.connect(self.save_progress_bar.setValue)
            self.splicing_thread.status_updated.connect(self.status_label.setText)
            self.splicing_thread.finished.connect(self.on_merge_finished)
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            
            # 启动线程
            self.splicing_thread.start()
    
    def handle_progress_for_save_bar(self, progress):
        """根据主进度条的值控制保存进度条的显示和隐藏"""
        if progress == 80:
            # 开始保存，显示保存进度条
            self.save_progress_bar.setValue(0)
            self.save_progress_bar.setVisible(True)
        elif progress == 90:
            # 保存完成，隐藏保存进度条
            self.save_progress_bar.setVisible(False)
    
    def on_merge_finished(self, success, message):
        """拼接完成后的处理"""
        # 启用按钮
        self.merge_button.setEnabled(True)
        
        # 隐藏所有进度条
        self.progress_bar.setVisible(False)
        self.save_progress_bar.setVisible(False)
        
        # 更新状态并显示消息
        if success:
            self.status_label.setText("拼接完成")
            QMessageBox.information(self, "拼接完成", message)
        else:
            self.status_label.setText("拼接失败")
            QMessageBox.critical(self, "拼接失败", message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MusicCutterApp()
    main_window.show()
    sys.exit(app.exec_())
