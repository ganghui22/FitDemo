# 这是一个示例 Python 脚本。

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。
import sys
import cv2
import json
import os
import pickle
import numpy as np
import colorsys
from PyQt5.QtCore import QTimer, QSize, QDateTime, Qt, QPoint, QRect
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from QtCustomComponents.qnchatmessage import QNChatMessage
from QtCustomComponents.MainWindow import Ui_MainWindow
from water_api import WaterApi


class DemoWindows(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(DemoWindows, self).__init__(parent)
        self.setupUi(self)

        # 加载当前屏幕的分辨率
        current_screenNumber = qApp.desktop().screenNumber()
        desktop_w, desktop_h = qApp.desktop().screenGeometry(current_screenNumber).width(), \
                               qApp.desktop().screenGeometry(current_screenNumber).height()

        # 设置全屏显示
        self.setGeometry(self.centralwidget.x() + 0, self.centralwidget.height() + 0, desktop_w, desktop_h)
        self.centralwidget.setGeometry(0, 0,
                                       self.width(), self.height() - self.menubar.height() - self.statusbar.height())
        self.water_api_isConnect = True
        # 加载water api
        try:
            self.water_api = WaterApi("81.70.197.166", 7102)
        except:
            self.water_api_isConnect = False
        # 加载地图
        self._map = QPixmap("data/map/fit4_5/mapDealing.png")
        self._map_cv2 = cv2.imread("data/map/fit4_5/mapDealing.png")
        self._map_w, self._map_h = self._map.width(), self._map.height()

        # 加载机器人头像
        self._robot = QPixmap("data/head_png/robot.png") \
            .scaled(50, 50, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        # map scene 设置, 长宽为map的分辨率
        self.map_scene = QGraphicsScene(0, 0, self._map_w, self._map_h)
        # 向map scene中添加地图
        self.map_scene_map_item = self.map_scene.addPixmap(self._map)
        # 向map scene中添加机器人
        self.map_scene_robot_item = self.map_scene.addPixmap(self._robot)
        # 设置机器人的图层为2
        self.map_scene_robot_item.setZValue(2)
        # 获取机器人随机位置
        if self.water_api_isConnect:
            self.RobotCurrentPoint, self.RobotCurrentPoint_pix, _ = self.water_api.get_pose_real_and_pix_and_isRunning()
        else:
            self.RobotCurrentPoint, self.RobotCurrentPoint_pix = [0, 0], [0, 0]
            self.map_scene_robot_item.setVisible(False)
        # 设置机器人位置
        self.map_scene_robot_item.setPos(int((self.RobotCurrentPoint_pix[0] - self._robot.width() / 2)),
                                         int(self.RobotCurrentPoint_pix[1] - self._robot.height() / 2))

        # map_scene real view 即局部地图的view设置
        self.map_view_real.setScene(self.map_scene)

        # map_scene real view 即全局小地图的view设置
        self.map_view_mini.setScene(self.map_scene)
        self.map_view_mini.hide()

        # 路径画笔定义
        path_pen = QPen()
        path_pen.setColor(QColor(255, 0, 0))
        path_pen.setStyle(Qt.DotLine)
        path_pen.setWidth(5)
        self._map_scene_path = QPainterPath()
        self._map_scene_path.moveTo(self.RobotCurrentPoint_pix[0], self.RobotCurrentPoint_pix[1])
        self._map_scene_path_item = self.map_scene.addPath(self._map_scene_path, path_pen)
        self._map_scene_path_item.setPen(path_pen)
        # 设置路径的图层为1
        self._map_scene_path_item.setZValue(1)

        # 布局设计
        # 局部地图的view大小和位置设置,以及聚焦机器人
        self.map_view_real.setGeometry(self.centralwidget.x() + 4 * int(self.centralwidget.width() / 9) + 10,
                                       self.centralwidget.y() + 10,
                                       5 * int(self.centralwidget.width() / 9 - 10),
                                       self.centralwidget.height() - 20)
        self.map_view_real_scale_w = 0.99 * self.map_view_real.width() / self._map_w
        self.map_view_real_scale_h = 0.99 * self.map_view_real.height() / self._map_h * (self._map_h / self._map_w)
        self.map_view_real.scale(self.map_view_real_scale_w,
                                 self.map_view_real_scale_h)
        self.map_view_real.centerOn(self.map_scene_robot_item)

        # 聊天框大小及位置设置
        self.listWidget.setGeometry(self.centralwidget.x() + 10,
                                    self.centralwidget.y() + 10,
                                    2 * int(self.centralwidget.width() / 9) - 10,
                                    3 * int(self.centralwidget.height() / 4) - 20)

        # 清空按钮的大小及位置设置
        self.cleartrackbutton.move(self.map_view_mini.x(), self.map_view_mini.y() + self.map_view_mini.height() + 10)
        self.cleartrackbutton.setFixedWidth(self.map_view_mini.width() + self.map_view_real.width())
        self.cleartrackbutton.hide()

        # 对话框嵌入
        self.send_text = QTextEdit(self.window())
        self.send_text.setGeometry(self.listWidget.x(), self.y() + self.listWidget.height() + 10,
                                   2 * int(self.centralwidget.width() / 9) - 10 - 110 - 10 - 10,
                                   1 * int(self.centralwidget.height() / 4) - 10)
        self.send_text.setStyleSheet("border-radius:6px;\n"
                                     "padding:2px 4px;\n"
                                     "border-style: outset;\n"
                                     "border:2px groove gray;\n"
                                     "background-color: rgb(251, 251, 251);\n"
                                     "border-top-color:rgb(186, 189, 182);\n"
                                     "border:none;")
        self.send_button = QPushButton(self.window())
        self.send_button.setText("发送")
        self.send_button.setGeometry(self.send_text.x() + self.send_text.width() + 10,
                                     self.send_text.y() + self.send_text.height() - 50,
                                     110,
                                     50)

        self.send_button.setStyleSheet("border-radius:6px;\n"
                                       "padding:2px 4px;\n"
                                       "border-style: outset;\n"
                                       "border:2px groove gray;\n"
                                       "border:none;\n"
                                       "background-color: rgb(229, 234, 233);\n"
                                       "color: rgb(37, 194, 118);")
        # 头像框嵌入
        self.userhead = QLabel(self.window())
        self.userhead.setGeometry(self.listWidget.x() + self.send_text.width() + 10,
                                  self.y() + self.listWidget.height() + 10,
                                  110,
                                  110)
        self.userhead.setAutoFillBackground(False)
        self.userhead.setStyleSheet("border-radius:6px;\n"
                                    "padding:2px 4px;\n"
                                    "border-style: outset;\n"
                                    "border:2px groove gray;")
        self.userhead.setText("")

        # 加载地点列表
        with open('data/Location_list.json', 'r', encoding='utf-8') as f:
            self._location_list: dict = json.load(f)
        self.loc_color_list = []

        # 一些槽函数的连接
        self.cleartrackbutton.clicked.connect(self.__clearTrackFunction)

        # 向statusbar添加map_view_real的信息打印
        self.map_view_real_status = QLabel()
        self.map_view_real_status.setMinimumWidth(150)
        self.statusbar.addWidget(self.map_view_real_status)
        # 重写map_view_real 的mouseMoveEvent函数
        self.map_view_real.mouseMoveEvent = self._map_view_real_mouseMoveEvent
        # 打开map_view_real 的鼠标跟踪功能
        self.map_view_real.setMouseTracking(True)

        # 一些Qt组件的属性设置
        self.RobotTargetPoint_pix = None

        # 初始化动作扫描服务
        if self.water_api_isConnect:
            self.__moveTimer = QTimer(self)
            self.__moveTimer.timeout.connect(self.__moveScanf)
            self.__moveSpeed = 100
            self.__waitForPathPlanning = False
            self.__moveTimer.start(self.__moveSpeed)

        # 画框标志位
        self.isDragRect = False
        self.dragStartPt = QPoint()
        self.dragRectPressFlag = False

        self.actionTag_location.setCheckable(True)
        self.actionTag_location.triggered.connect(self._Tag_location_fun)
        self.action_exit.triggered.connect(self.action_exit_fun)

        # 初始化标注的房间item列表
        self.room_item_list = []
        self.map_scene_room_item_dict = {}
        self._load_map_room_item()

        # tag location槽函数连接
        self.map_view_real.mouseReleaseEvent = self._map_view_real_ReleaseEvent
        self.map_view_real.mousePressEvent = self._map_view_real_PressEvent

        # save TagLocation槽函数连接
        self.actionsave_Tag_Location.triggered.connect(self.save_map_scene_room_item_dict)
        self.actionsave_mapView.triggered.connect(self.__save_map_view)
        self.actionshowRoomLabel.setCheckable(True)
        self.actionshowRoomLabel.setChecked(True)
        self.actionshowRoomLabel.triggered.connect(self.__showRoomLabel_view)

    def __showRoomLabel_view(self, check: bool):
        """
        显示房间Label
        :param check:
        :return:
        """
        if check:
            for name in self.map_scene_room_item_dict:
                self.map_scene_room_item_dict[name]['name_label'].setVisible(True)
        else:
            for name in self.map_scene_room_item_dict:
                self.map_scene_room_item_dict[name]['name_label'].setVisible(False)

    def __dealMessageTime(self, curMsgTime: int):
        """
        处理对话时时间显示函数
        """
        isShowTime = False
        if self.listWidget.count() > 0:
            lastItem = self.listWidget.item(self.listWidget.count() - 1)
            messageW = self.listWidget.itemWidget(lastItem)
            lastTime = messageW.m_time
            curTime = curMsgTime
            isShowTime = ((curTime - lastTime) > 60)  # 两个消息相差一分钟
        else:
            isShowTime = True
        if isShowTime:
            messageTime = QNChatMessage(self.listWidget.parentWidget())
            itemTime = QListWidgetItem(self.listWidget)
            size = QSize(self.width(), 40)
            messageTime.resize(size)
            itemTime.setSizeHint(size)
            messageTime.setText(str(curMsgTime), curMsgTime, "", size, QNChatMessage.User_Type.User_Time)
            self.listWidget.setItemWidget(itemTime, messageTime)

    def __save_map_view(self):
        geometry = self.map_view_real.geometry()
        path = QFileDialog.getSaveFileName(self.window(), '选择保存的路径', filter='png(*.png)')
        self.map_view_real.setGeometry(0, 0, int(self.map_scene.width()), int(self.map_scene.height()))
        self.map_view_real.scale(1 / self.map_view_real_scale_w, 1 / self.map_view_real_scale_h)
        map_view = self.map_view_real.grab()
        self.map_view_real.setGeometry(geometry)
        self.map_view_real.scale(0.99 * self.map_view_real.width() / self._map_w,
                                 0.99 * self.map_view_real.height() / self._map_h * (self._map_h / self._map_w))

        map_view.save(path[0])

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        """
        重写键盘按下事件
        :param a0: QKeyEvent
        :return:
        """
        if a0.key() == Qt.Key.Key_Escape:
            self.close()
        if a0.key() == Qt.Key.Key_Delete:
            QGraphicsItemList = self.map_scene.selectedItems()
            if QGraphicsItemList:
                for item in QGraphicsItemList:
                    self.map_scene.removeItem(item)

        return QMainWindow.keyPressEvent(self, a0)

    def __clearTrackFunction(self):
        """
        清除轨迹
        """
        self._map_scene_path.clear()
        self._map_scene_path_item.setPath(self._map_scene_path)
        self._map_scene_path.moveTo(self.RobotCurrentPoint_pix[0], self.RobotCurrentPoint_pix[1])

    def _map_view_real_mouseMoveEvent(self, event: QMouseEvent):
        """
        重写map_view_real的鼠标移动事件，打印鼠标指向的地图像素点
        """
        view_pos = event.pos()
        scene_pos = self.map_view_real.mapToScene(view_pos)

        real_x, real_y = self.water_api.pix_to_real(scene_pos.x(), scene_pos.y()) if self.water_api_isConnect else 0, 0

        self.window().map_view_real_status.setText("<font color='red'>P_X</font>:<font color='blue'>{:.0f}</font>, "
                                                   "<font color='red'>P_Y</font>:<font color='blue'>{:.0f}</font>   "
                                                   "<font color='green'>R_X</font>:<font color='blue'>{:.2f}</font>,"
                                                   "<font color='green'>R_Y</font>:<font color='blue'>{:.2f}</font>"
                                                   .format(scene_pos.x(), scene_pos.y(), real_x, real_y))
        return QGraphicsView.mouseMoveEvent(self.map_view_real, event)

    def _map_view_real_PressEvent(self, e: QMouseEvent):
        """
        重写map_view_real的鼠标按压事件，若是dragRect的模式则置位dragRectPressFlag标记位
        """
        if self.actionTag_location.isChecked():
            self.dragRectPressFlag = True
        return QGraphicsView.mousePressEvent(self.map_view_real, e)

    def _Tag_location_fun(self, check: bool):
        """
        Tag_location动作调用的函数
        """
        if check:
            self.map_view_real.setDragMode(QGraphicsView.RubberBandDrag)
            self.map_view_real.setCursor(Qt.CrossCursor)
            for name in self.map_scene_room_item_dict:
                self.map_scene_room_item_dict[name]['name_label'].setFlag(QGraphicsItem.ItemIsMovable, False)
        else:
            self.map_view_real.setCursor(Qt.ArrowCursor)
            self.map_view_real.setDragMode(QGraphicsView.NoDrag)
            for name in self.map_scene_room_item_dict:
                self.map_scene_room_item_dict[name]['name_label'].setFlag(QGraphicsItem.ItemIsMovable, True)

    def __dealMessageShow(self, messageW: QNChatMessage, item: QListWidgetItem,
                          text: str, name: str, time: int, usertype: QNChatMessage.User_Type):
        """
        处理消息气泡显示效果的函数
        """
        messageW.setFixedWidth(self.width())
        size = messageW.fontRect(text, name)
        item.setSizeHint(size)
        messageW.setText(text, time, name, size, usertype)
        self.listWidget.setItemWidget(item, messageW)

    def __dealMessageTime(self, curMsgTime: int):
        """
        处理对话时时间显示函数
        """
        isShowTime = False
        if self.listWidget.count() > 0:
            lastItem = self.listWidget.item(self.listWidget.count() - 1)
            messageW = self.listWidget.itemWidget(lastItem)
            lastTime = messageW.m_time
            curTime = curMsgTime
            isShowTime = ((curTime - lastTime) > 60)  # 两个消息相差一分钟
        else:
            isShowTime = True
        if isShowTime:
            messageTime = QNChatMessage(self.listWidget.parentWidget())
            itemTime = QListWidgetItem(self.listWidget)
            size = QSize(self.listWidget.width(), 40)
            messageTime.resize(size)
            itemTime.setSizeHint(size)
            messageTime.setText(str(curMsgTime), curMsgTime, "", size, QNChatMessage.User_Type.User_Time)
            self.listWidget.setItemWidget(itemTime, messageTime)

    def UserTalk(self, message: str) -> None:
        """
        用户说话

        :param message: 消息文本
        :return:
        """
        t = QDateTime.currentDateTime().toTime_t()
        self.__dealMessageTime(t)
        messageW = QNChatMessage(self.listWidget.parentWidget())
        userHead = self.CurrentUser['head_QPixmap']
        messageW.setPixUser(userHead)
        item = QListWidgetItem(self.listWidget)
        self.__dealMessageShow(messageW, item, message, self.CurrentUser['name'], t, QNChatMessage.User_Type.User_She)
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)

    def RobotTalk(self, message: str) -> None:
        """
        机器人说话

        :param message: 消息文本
        :return:
        """
        t = QDateTime.currentDateTime().toTime_t()
        self.__dealMessageTime(t)
        messageW = QNChatMessage(self.listWidget.parentWidget())
        item = QListWidgetItem(self.listWidget)
        self.__dealMessageShow(messageW, item, message, "Robot", t, QNChatMessage.User_Type.User_Me)
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)

    def __moveScanf(self):
        """
        动作序列的扫描函数

        """
        self.RobotCurrentPoint, self.RobotCurrentPoint_pix, isRunning = self.water_api.get_pose_real_and_pix_and_isRunning()

        self.map_scene_robot_item.setPos(int((self.RobotCurrentPoint_pix[0] - self._robot.width() / 2)),
                                         int(self.RobotCurrentPoint_pix[1] - self._robot.height() / 2))
        if isRunning:
            self._map_scene_path.lineTo(self.RobotCurrentPoint_pix[0], self.RobotCurrentPoint_pix[1])
            self._map_scene_path_item.setPath(self._map_scene_path)
        else:
            self._map_scene_path.clear()
            self._map_scene_path.moveTo(self.RobotCurrentPoint_pix[0], self.RobotCurrentPoint_pix[1])
            self._map_scene_path_item.setPath(self._map_scene_path)

    def action_exit_fun(self):
        """
        程序退出时调用的函数
        """
        if QMessageBox(QMessageBox.Icon.Question, "确认退出", "是否退应用程序？",
                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) \
                .exec_() == QMessageBox.StandardButton.Yes:
            self.close()

    def _load_map_room_item(self):
        """
        加载保存的房间标注信息
        """
        if os.path.exists("data/fit4_5Dealing.pkl"):
            with open("data/fit4_5Dealing.pkl", 'rb') as f:
                d = pickle.load(f)
            self.loc_color_list = d.pop('color_list')
            for r in d:
                # 加载room信息
                rect = d[r]['argument']['rect']
                room = d[r]['argument']['room']
                room_color = d[r]['argument']['color']
                # color = (255 - room_color).tolist() + [200]
                color = [0, 0, 0, 255]
                room_name_label_pos = d[r]['argument']['label_pos']

                name = d[r]['argument']['name']
                # room标签设置
                room_name_label: QGraphicsTextItem = self.map_scene.addText(name)
                room_name_label.setDefaultTextColor(QColor(color[0], color[1], color[2], color[3]))
                font = QFont("Times", 36)
                room_name_label.setFont(font)
                room_name_label.setPos(room_name_label_pos[0], room_name_label_pos[1])
                room_name_label.setFlags(QGraphicsItem.ItemIsSelectable |
                                         QGraphicsItem.ItemIsMovable |
                                         QGraphicsItem.ItemIsFocusable)
                room_name_label.setZValue(4)
                room[:, :, 3] = np.where(room[:, :, 3] != 0, 60, room[:, :, 3])
                Q_room_Image = QImage(room.data, room.shape[1], room.shape[0], room.shape[1] * 4,
                                      QImage.Format_RGBA8888)
                Q_room = QPixmap().fromImage(Q_room_Image)
                map_room_item: QGraphicsPixmapItem = self.map_scene.addPixmap(Q_room)
                map_room_item.setPos(rect[0], rect[1])
                map_room_item.setZValue(1)
                map_room_item.setShapeMode(QGraphicsPixmapItem.MaskShape)
                map_room_item.setFlags(QGraphicsItem.ItemIsSelectable |
                                       QGraphicsItem.ItemIsFocusable |
                                       QGraphicsItem.ItemClipsToShape
                                       )
                map_room_item.setData(0, name)  # 自定义map_room_item的值
                map_room_item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
                self.map_scene_room_item_dict[r] = d[r]
                self.map_scene_room_item_dict[r]['item'] = map_room_item
                self.map_scene_room_item_dict[r]['name_label'] = room_name_label
            is_over = True
            for key in self._location_list:
                if key not in d:
                    is_over = False
            if is_over:
                self.actionTag_location.setCheckable(False)
                self.actionTag_location.setVisible(False)
        else:
            self.loc_color_list = self._get_colors(len(self._location_list))

    def _map_view_real_ReleaseEvent(self, e: QMouseEvent):
        """
        重写 map_view_real的鼠标释放事件。
        释放时若是DragRec模式读取 RubberBandDrag所选中区域进行区域内房间选择，该功能待优化，效果不是太好。
        """
        if self.dragRectPressFlag & self.actionTag_location.isChecked():
            # 获取roi 区域
            r = self.map_view_real.mapToScene(self.map_view_real.rubberBandRect())  # [0左上角，1右上角，2右下角，3左下角]

            # 原图mask
            mask = np.zeros(self._map_cv2.shape[:2], dtype=np.uint8)

            # 矩形roi
            rect = (int(r[0].x()), int(r[0].y()), int(r[2].x() - r[0].x()), int(r[2].y() - r[0].y()))
            bgdmodel = np.zeros((1, 65), np.float64)  # bg模型的临时数组
            fgdmodel = np.zeros((1, 65), np.float64)  # fg模型的临时数组

            # 提取区域
            cv2.grabCut(self._map_cv2, mask, rect, bgdmodel, fgdmodel, 3, mode=cv2.GC_INIT_WITH_RECT)

            # 提取前景和可能的前景区域
            room_mask = np.array(mask[int(r[0].y()):int(r[2].y()),
                                 int(r[0].x()):int(r[2].x())], dtype='uint8')
            room_mask = np.where((room_mask == 1) + (room_mask == 3),
                                 125, 0).reshape(room_mask.shape[0], room_mask.shape[1], 1)
            room_color = np.array(self.loc_color_list.pop()) * 255
            room = room_color * np.ones((room_mask.shape[0], room_mask.shape[1], 1), np.uint8)
            room = np.concatenate((room, room_mask), axis=2).astype(np.uint8)
            room[:, :, 3] = np.where(room[:, :, 3] != 0, 60, room[:, :, 3])
            Q_room_Image = QImage(room.data, room.shape[1], room.shape[0], room.shape[1] * 4,
                                  QImage.Format_RGBA8888)
            Q_room = QPixmap().fromImage(Q_room_Image)
            # 记录当前房间item
            map_room_item: QGraphicsPixmapItem = self.map_scene.addPixmap(Q_room)
            map_room_item.setPos(r[0])
            map_room_item.setZValue(1)
            map_room_item.setShapeMode(QGraphicsPixmapItem.MaskShape)
            map_room_item.setFlags(QGraphicsItem.ItemIsSelectable |
                                   QGraphicsItem.ItemIsFocusable |
                                   QGraphicsItem.ItemClipsToShape)
            items = []
            for room_name in self._location_list:
                if room_name not in self.map_scene_room_item_dict:
                    items.append(room_name)
            name, boolAction = QInputDialog.getItem(self.window(), "指定房间", "房间:", items, 0, False)
            if boolAction and name != '':
                self.map_scene_room_item_dict[name] = {}
                room_name_label: QGraphicsTextItem = self.map_scene.addText(name)
                color = (255 - room_color).tolist() + [200]
                color = [0, 0, 0, 255]
                room_name_label.setDefaultTextColor(QColor(color[0], color[1], color[2], color[3]))
                font = QFont("Times", 28)
                room_name_label.setFont(font)
                room_name_label.setFlags(QGraphicsItem.ItemIsSelectable |
                                         QGraphicsItem.ItemIsFocusable)
                room_name_label.setZValue(4)
                room_name_label_pos = [int(rect[0] + rect[2] / 2), int(rect[1] + rect[3] / 2 - 36)]
                room_name_label.setPos(room_name_label_pos[0], room_name_label_pos[1])
                if not self.actionshowRoomLabel.isChecked():
                    room_name_label.setVisible(False)
                map_room_item.setData(0, name)  # 自定义map_room_item的值
                self.map_scene_room_item_dict[name]["item"] = map_room_item
                self.map_scene_room_item_dict[name]["name_label"] = room_name_label
                self.map_scene_room_item_dict[name]["argument"] = {}
                self.map_scene_room_item_dict[name]["argument"]["color"] = room_color
                self.map_scene_room_item_dict[name]["argument"]["label_pos"] = room_name_label_pos
                self.map_scene_room_item_dict[name]["argument"]["name"] = name
                self.map_scene_room_item_dict[name]["argument"]["rect"] = rect
                self.map_scene_room_item_dict[name]["argument"]["room"] = room
                if len(items) == 1 and name == items[0]:  # 最后一个房间已被选择完成，将该模式隐藏
                    self.map_view_real.setDragMode(QGraphicsView.NoDrag)
                    self.map_view_real.setCursor(Qt.ArrowCursor)
                    self.actionTag_location.setCheckable(False)
                    self.actionTag_location.setDisabled(True)
            else:
                self.map_scene.removeItem(map_room_item)
                self.loc_color_list.append(room_color)
            # drag模式选择Flag
            self.dragRectPressFlag = False
        return QGraphicsView.mouseReleaseEvent(self.map_view_real, e)

    def save_map_scene_room_item_dict(self):
        """
        room信息保存功能的实现
        """
        d = {}
        for name in self.map_scene_room_item_dict:
            d[name] = {}
            d[name]['argument'] = {}
            d[name]['argument']['color'] = self.map_scene_room_item_dict[name]["argument"]["color"]
            self.map_scene_room_item_dict[name]["argument"]["label_pos"] = \
                [int(self.map_scene_room_item_dict[name]['name_label'].x()),
                 int(self.map_scene_room_item_dict[name]['name_label'].y())]
            room_name_label_pos = self.map_scene_room_item_dict[name]["argument"]["label_pos"]
            d[name]["argument"]["label_pos"] = room_name_label_pos
            d[name]['argument']['name'] = self.map_scene_room_item_dict[name]['argument']["name"]
            d[name]['argument']['rect'] = self.map_scene_room_item_dict[name]['argument']["rect"]
            d[name]['argument']['room'] = self.map_scene_room_item_dict[name]['argument']["room"]
        d['color_list'] = self.loc_color_list
        with open("data/fit4_5Dealing.pkl", 'wb') as f:
            pickle.dump(d, f)

    def sendButtonFunction(self):
        """
        用户消息发送按钮点击事件
        """

        sendText = self.chat_text.toPlainText()
        self.chat_text.setText("")
        if sendText != '':
            self.UserTalk(sendText)
            if self.CurrentUser['name'] != "Robot":
                t = self.CurrentUser['name'] + ":" + sendText
                self.dealMessage(t)

    def dealMessage(self, sentence: str):
        """
        消息处理函数，主要对消息进行一些简单的处理
        """
        if sentence == "":
            return
        else:
            speak_person = sentence.split(":")[0]
            speak_person = self._Person[speak_person]
            self.__userChanged(None, speak_person)
            t = sentence.split(":")[1]
            self.UserTalk(t)
            # if '@ Robot' not in sentence:
            #     # 提取时间、地点、人物三元组并更新动态时空图谱
            #     self._TimeSpaceGraph_InQueue.put([True, sentence])
            # else:
            #     # 指令处理
            #     sentence = sentence[sentence.index('@ Robot') + 7:]
            #     self.dealInstruction(sentence)


    @staticmethod
    def _get_colors(num_colors):
        colors = []

        for i in np.arange(0., 360., 360. / num_colors):
            hue = i / 360.
            lightness = (50 + np.random.rand() * 10) / 100.
            saturation = (90 + np.random.rand() * 10) / 100.
            colors.append(colorsys.hls_to_rgb(hue, lightness, saturation))

        return colors


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DemoWindows()
    window.showFullScreen()
    window.RobotTalk("你好")
    sys.exit(app.exec_())
