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
        self.main_window.file_list_widget = QListWidget()
        self.main_window.file_list_widget.setAcceptDrops(True)
        self.main_window.file_list_widget.setDragDropMode(QListWidget.InternalMove)
        self.main_window.file_list_widget.setSelectionMode(QListWidget.SingleSelection)
        # 安装事件过滤器以处理拖放事件
        self.main_window.file_list_widget.installEventFilter(self.main_window)
        self.main_window.file_list_widget.setStyleSheet("""
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
        layout.addWidget(self.main_window.file_list_widget)

        # 创建控制区域
        control_layout = QVBoxLayout()
        
        # 拼接模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("拼接模式："))
        self.main_window.mode_combo = QComboBox()
        self.main_window.mode_combo.addItems(["顺序拼接", "随机拼接"])
        mode_layout.addWidget(self.main_window.mode_combo)
        mode_layout.addStretch()
        control_layout.addLayout(mode_layout)
        
        # 并发功能控制
        concurrency_layout = QHBoxLayout()
        self.main_window.concurrency_checkbox = QCheckBox("启用并发优化")
        self.main_window.concurrency_checkbox.setChecked(True)  # 默认启用并发优化
        self.main_window.concurrency_checkbox.stateChanged.connect(self.main_window.toggle_concurrency)
        concurrency_layout.addWidget(self.main_window.concurrency_checkbox)
        concurrency_layout.addStretch()
        control_layout.addLayout(concurrency_layout)
        
        # 倒计时文件选择
        countdown_layout = QHBoxLayout()
        countdown_layout.addWidget(QLabel("倒计时音频："))
        self.main_window.countdown_label = QLabel("未选择")
        self.main_window.countdown_label.setStyleSheet("color: #666;")
        self.main_window.select_countdown_button = QPushButton("选择文件")
        self.main_window.select_countdown_button.clicked.connect(self.main_window.select_countdown)
        self.main_window.select_countdown_button.setStyleSheet("""
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
        countdown_layout.addWidget(self.main_window.countdown_label)
        countdown_layout.addWidget(self.main_window.select_countdown_button)
        countdown_layout.addStretch()
        control_layout.addLayout(countdown_layout)
        
        # 曲库目录信息（固定为根目录下的"曲库"目录）
        library_info_layout = QHBoxLayout()
        library_info_layout.addWidget(QLabel("曲库目录："))
        self.main_window.library_label = QLabel("曲库")
        self.main_window.library_label.setStyleSheet("color: #000;")
        library_info_layout.addWidget(self.main_window.library_label)
        library_info_layout.addStretch()
        control_layout.addLayout(library_info_layout)
        
        # 控制按钮
        button_layout = QVBoxLayout()

        self.main_window.add_button = QPushButton('添加文件')
        self.main_window.add_button.clicked.connect(self.main_window.add_files)
        self.main_window.add_button.setStyleSheet("""
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
        button_layout.addWidget(self.main_window.add_button)

        self.main_window.auto_load_button = QPushButton('自动读取随舞目录')
        self.main_window.auto_load_button.clicked.connect(self.main_window.auto_load_dance_files)
        self.main_window.auto_load_button.setStyleSheet("""
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
        button_layout.addWidget(self.main_window.auto_load_button)

        self.main_window.remove_button = QPushButton('移除选中文件')
        self.main_window.remove_button.clicked.connect(self.main_window.remove_file)
        self.main_window.remove_button.setStyleSheet("""
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
        button_layout.addWidget(self.main_window.remove_button)

        self.main_window.clear_button = QPushButton('清空歌单')
        self.main_window.clear_button.clicked.connect(self.main_window.clear_playlist)
        self.main_window.clear_button.setStyleSheet("""
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
        button_layout.addWidget(self.main_window.clear_button)

        self.main_window.merge_button = QPushButton('拼接音频')
        self.main_window.merge_button.clicked.connect(self.main_window.merge_audio),
        self.main_window.merge_button.setStyleSheet("""
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
        button_layout.addWidget(self.main_window.merge_button)
        
        control_layout.addLayout(button_layout)
        
        # 预计时长标签
        self.main_window.duration_label = QLabel("预计时长：00:00:00")
        self.main_window.duration_label.setStyleSheet("color: #333; font-weight: bold;")
        control_layout.addWidget(self.main_window.duration_label)
        
        # 进度条
        self.main_window.progress_bar = QProgressBar()
        self.main_window.progress_bar.setVisible(False)
        control_layout.addWidget(self.main_window.progress_bar)
        
        # 状态标签
        self.main_window.status_label = QLabel("就绪")
        self.main_window.status_label.setStyleSheet("color: #666; font-size: 12px;")
        control_layout.addWidget(self.main_window.status_label)

        layout.addLayout(control_layout)
