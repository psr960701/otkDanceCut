#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import timedelta

from PyQt5.QtWidgets import (
    QMainWindow, QListWidget, QPushButton, QVBoxLayout, QWidget, 
    QFileDialog, QMessageBox, QHBoxLayout, QLabel, QComboBox, QProgressBar, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class UiComponents:
    # 定义组件访问接口
    @property
    def file_list_widget(self):
        return self._file_list_widget

    @property
    def mode_combo(self):
        return self._mode_combo

    @property
    def concurrency_checkbox(self):
        return self._concurrency_checkbox

    @property
    def countdown_label(self):
        return self._countdown_label

    @property
    def select_countdown_button(self):
        return self._select_countdown_button

    @property
    def library_label(self):
        return self._library_label

    @property
    def add_button(self):
        return self._add_button

    @property
    def auto_load_button(self):
        return self._auto_load_button

    @property
    def remove_button(self):
        return self._remove_button

    @property
    def clear_button(self):
        return self._clear_button

    @property
    def merge_button(self):
        return self._merge_button

    @property
    def duration_label(self):
        return self._duration_label

    @property
    def progress_bar(self):
        return self._progress_bar

    @property
    def save_progress_bar(self):
        return self._save_progress_bar

    @property
    def status_label(self):
        return self._status_label

    def __init__(self, main_window):
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        # 设置窗口标题和大小
        self.main_window.setWindowTitle('音乐剪辑器 - otkDanceCut')
        self.main_window.setGeometry(100, 100, 800, 600)

        # 创建主布局
        main_widget = QWidget()
        self.main_window.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 创建文件列表
        self._file_list_widget = QListWidget()
        self._file_list_widget.setAcceptDrops(True)
        self._file_list_widget.setDragDropMode(QListWidget.InternalMove)
        self._file_list_widget.setSelectionMode(QListWidget.SingleSelection)
        # 事件过滤器将在main_window初始化完成后安装
        self._file_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                min-height: 200px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 4px 0;
                background-color: white;
                border-radius: 3px;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
                border-radius: 3px;
            }
            QListWidget::item:selected:!active {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(self._file_list_widget)

        # 创建控制区域
        control_layout = QVBoxLayout()
        
        # 拼接模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("拼接模式："))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["顺序拼接", "随机拼接"])
        mode_layout.addWidget(self._mode_combo)
        mode_layout.addStretch()
        control_layout.addLayout(mode_layout)
        
        # 并发功能控制
        concurrency_layout = QHBoxLayout()
        self._concurrency_checkbox = QCheckBox("启用并发优化")
        self._concurrency_checkbox.setChecked(True)  # 默认启用并发优化
        self._concurrency_checkbox.stateChanged.connect(self.main_window.toggle_concurrency)
        concurrency_layout.addWidget(self._concurrency_checkbox)
        concurrency_layout.addStretch()
        control_layout.addLayout(concurrency_layout)
        
        # 倒计时文件选择
        countdown_layout = QHBoxLayout()
        countdown_layout.addWidget(QLabel("倒计时音频："))
        self._countdown_label = QLabel("未选择")
        self._countdown_label.setStyleSheet("color: #666;")
        self._select_countdown_button = QPushButton("选择文件")
        self._select_countdown_button.clicked.connect(self.main_window.select_countdown)
        self._select_countdown_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        countdown_layout.addWidget(self._countdown_label)
        countdown_layout.addWidget(self._select_countdown_button)
        countdown_layout.addStretch()
        control_layout.addLayout(countdown_layout)
        
        # 曲库目录信息（固定为根目录下的"曲库"目录）
        library_info_layout = QHBoxLayout()
        library_info_layout.addWidget(QLabel("曲库目录："))
        self._library_label = QLabel("曲库")
        self._library_label.setStyleSheet("color: #000;")
        library_info_layout.addWidget(self._library_label)
        library_info_layout.addStretch()
        control_layout.addLayout(library_info_layout)
        
        # 控制按钮
        button_layout = QVBoxLayout()

        self._add_button = QPushButton('添加文件')
        self._add_button.clicked.connect(self.main_window.add_files)
        self._add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self._add_button)

        self._auto_load_button = QPushButton('自动读取随舞目录')
        self._auto_load_button.clicked.connect(self.main_window.auto_load_dance_files)
        self._auto_load_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        button_layout.addWidget(self._auto_load_button)

        self._remove_button = QPushButton('移除选中文件')
        self._remove_button.clicked.connect(self.main_window.remove_file)
        self._remove_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(self._remove_button)

        self._clear_button = QPushButton('清空歌单')
        self._clear_button.clicked.connect(self.main_window.clear_playlist)
        self._clear_button.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        button_layout.addWidget(self._clear_button)

        self._merge_button = QPushButton('拼接音频')
        self._merge_button.clicked.connect(self.main_window.merge_audio),
        self._merge_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                margin: 5px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        button_layout.addWidget(self._merge_button)
        
        control_layout.addLayout(button_layout)
        
        # 预计时长标签
        self._duration_label = QLabel("预计时长：00:00:00")
        self._duration_label.setStyleSheet("color: #333; font-weight: bold;")
        control_layout.addWidget(self._duration_label)
        
        # 主进度条（用于整体拼接过程）
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        control_layout.addWidget(self._progress_bar)
        
        # 保存进度条（用于音频保存过程）
        self._save_progress_bar = QProgressBar()
        self._save_progress_bar.setVisible(False)
        self._save_progress_bar.setStyleSheet("background-color: #e3f2fd;")
        control_layout.addWidget(self._save_progress_bar)
        
        # 状态标签
        self._status_label = QLabel("就绪")
        self._status_label.setStyleSheet("color: #666; font-size: 12px;")
        control_layout.addWidget(self._status_label)

        layout.addLayout(control_layout)
