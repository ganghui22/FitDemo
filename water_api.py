import json
import socket
import time
import math
import cv2

import numpy as np


def edge_node(all_nav_nodes, grid_size):
    edge_nodes = []
    for node in all_nav_nodes:
        edge0 = [node[0], node[1] + grid_size]
        edge1 = [node[0] + grid_size, node[1]]
        edge2 = [node[0], node[1] - grid_size]
        edge3 = [node[0] - grid_size, node[1]]
        if edge0 not in all_nav_nodes or edge1 not in all_nav_nodes or edge2 not in all_nav_nodes or edge3 not in all_nav_nodes:
            edge_nodes.append(node)

    nav_nodes = [iteam for iteam in all_nav_nodes if iteam not in edge_nodes]

    return edge_nodes, nav_nodes


def get_median(data):
    data = sorted(list(set(data)))
    size = len(data)
    madian = data[int(size / 2)]
    return madian


def c_angle(v1, v2):
    dx1 = v1[2] - v1[0]
    dy1 = v1[3] - v1[1]
    dx2 = v2[2] - v2[0]
    dy2 = v2[3] - v2[1]
    angle1 = math.atan2(dy1, dx1)
    angle1 = int(angle1 * 180 / math.pi)
    # print(angle1)
    angle2 = math.atan2(dy2, dx2)
    angle2 = int(angle2 * 180 / math.pi)
    # print(angle2)
    if angle1 * angle2 >= 0:
        included_angle = angle1 - angle2
    else:
        included_angle = angle1 + angle2
        if included_angle > 180:
            included_angle = 360 - included_angle
    return included_angle


def map_dealing(map_path: str) -> None:
    map_origin = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    width, high = np.shape(map_origin)
    for x in range(width):
        for y in range(high):
            if 0 <= map_origin[x, y] <= 204:
                map_origin[x, y] = 0
            else:
                map_origin[x, y] = 255
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(map_origin, connectivity=4)
    area = stats[:, 4:5]  # area
    max1 = np.sort(area, axis=0)[-1]  # first area label
    max_index = area.tolist().index(max1)
    max2 = np.sort(area, axis=0)[-2]  # second area label
    max2_index = area.tolist().index(max2)
    map_connectedcomponents = map_origin
    for x in range(width):
        for y in range(high):
            if labels[x, y] == max2_index:
                map_connectedcomponents[x, y] = 255
            else:
                map_connectedcomponents[x, y] = 204
    for x in range(width):
        for y in range(high):
            if map_origin[x, y] == 0:
                map_connectedcomponents[x, y] = 0
    map_binary = np.array(map_connectedcomponents)
    for x in range(width):
        for y in range(high):
            if map_binary[x, y] == 204:
                map_binary[x, y] = 0
    contours, hierarchy = cv2.findContours(map_binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(map_connectedcomponents, contours, -1, 0, 2)
    map_name = map_path.split('.')
    cv2.imwrite(map_name[0] + 'Dealing' + '.png', map_connectedcomponents)


def map_track_middle(map_path: str) -> None:
    map_origin = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    print(map_origin)
    print(np.shape(map_origin))
    width, high = np.shape(map_origin)
    for x in range(width):
        for y in range(high):
            if 0 <= map_origin[x, y] <= 204:
                map_origin[x, y] = 0
            else:
                map_origin[x, y] = 255
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(map_origin, connectivity=4)
    area = stats[:, 4:5]  # area
    max1 = np.sort(area, axis=0)[-1]  # first area label
    max_index = area.tolist().index(max1)
    max2 = np.sort(area, axis=0)[-2]  # second area label
    max2_index = area.tolist().index(max2)
    map_connectedcomponents = map_origin
    for x in range(width):
        for y in range(high):
            if labels[x, y] == max2_index:
                map_connectedcomponents[x, y] = 255
            else:
                map_connectedcomponents[x, y] = 0
    for x in range(width):
        for y in range(high):
            if map_origin[x, y] == 0:
                map_connectedcomponents[x, y] = 0
    map_binary = np.array(map_connectedcomponents)
    for x in range(width):
        for y in range(high):
            if map_binary[x, y] == 0:
                map_binary[x, y] = 0
    contours, hierarchy = cv2.findContours(map_binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(map_connectedcomponents, contours, -1, 0, 12)
    map_name = map_path.split('.')
    cv2.imwrite('middle' + '.png', map_connectedcomponents)


# 类定义
class WaterApi:
    def __init__(self, host: str, port: int) -> None:
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect((host, port))
        self.origin_x, self.origin_y, self.height, self.width, self.resolution = self.get_map_info()

    def forward(self, length: int) -> None:
        for _ in range(length):
            send_data = "/api/joy_control?angular_velocity={}&linear_velocity={}".format(0.0, 0.2)
            self.tcp_socket.send(send_data.encode("utf-8"))
            receive = self.tcp_socket.recv(1024)
            if len(receive): print(str(receive, encoding='utf-8'))
            time.sleep(0.2)

    def backward(self, length: int) -> None:
        for _ in range(length):
            send_data = "/api/joy_control?angular_velocity={}&linear_velocity={}".format(0.0, -0.2)
            self.tcp_socket.send(send_data.encode("utf-8"))
            receive = self.tcp_socket.recv(1024)
            if len(receive): print(str(receive, encoding='utf-8'))
            time.sleep(0.2)

    def rotate_right(self, angle: int) -> None:  # 30
        for _ in range(angle):
            send_data = "/api/joy_control?angular_velocity={}&linear_velocity={}".format(0.19, 0)
            self.tcp_socket.send(send_data.encode("utf-8"))
            receive = self.tcp_socket.recv(1024)
            if len(receive): print(str(receive, encoding='utf-8'))
            time.sleep(0.4)

    def rotate_left(self, angle: int) -> None:  # 30
        for _ in range(angle):
            send_data = "/api/joy_control?angular_velocity={}&linear_velocity={}".format(-0.4, 0)
            self.tcp_socket.send(send_data.encode("utf-8"))
            receive = self.tcp_socket.recv(1024)
            if len(receive): print(str(receive, encoding='utf-8'))

    def as_robot_status(self, dct):
        if 'command' in dct:
            if dct['command'] == "/api/robot_status" & dct['type'] == 'response':
                return dct['results']

    def robot_status(self) -> dict:
        receive = {}
        try:
            send_data = "/api/robot_status"
            self.tcp_socket.send(send_data.encode("utf-8"))
            rrr = self.tcp_socket.recv(1024)
            rrr = rrr.split()
            try:
                receive = json.loads(rrr[0])
            except json.decoder.JSONDecodeError as e:
                error = str(e).split(':', 1)
                line = error[1].split()[1]  # 行
                column = error[1].split()[3]  # 列
                char = error[1].split()[5].split(')')[0]  # 字节序数
                if error[0] == "Expecting value":  # 开头数据有问题
                    print('error: ', error[0], line, column, char)
                if error[0] == "Extra data":  # 结尾数据有问题
                    print('error: ', error[0], line, column, char)
                if error[0] == "Unterminated string starting at":
                    receive = json.loads(rrr[1])
                print(error)
        except Exception as e:
            receive = self.robot_status()
        if 'results' not in receive:
            receive = self.robot_status()
        return receive

    def robot_location(self, loc):
        status = self.robot_status()
        pose = status['results']['current_pose']
        pose = [round(pose['x'], 2), round(pose['y'], 2)]
        vector = pose + loc
        angle = c_angle(vector, [0, 0, 1, 0])
        location = {'name': 'Nav', 'theta': math.radians(angle), 'x': loc[0], 'y': loc[1]}
        self.set_marker(location)
        self.robot_marker(location['name'])
        self.clear()

    def robot_marker(self, marker):
        send_data = "/api/move?marker=" + marker
        self.tcp_socket.send(send_data.encode("utf-8"))
        receive = self.tcp_socket.recv(1024)
        if len(receive): print(str(receive, encoding='utf-8'))

    def set_marker(self, location):
        send_data = "/api/markers/insert_by_pose?name={}&x={}&y={}&theta={}&floor=2&type=0".format(
            location['name'], location['x'], location['y'], location['theta'])
        self.tcp_socket.send(send_data.encode("utf-8"))
        receive = self.tcp_socket.recv(1024)
        if len(receive): print(str(receive, encoding='utf-8'))

    def move_location(self, x, y, theta):
        send_data = "/api/move?location={},{},{}".format(x, y, theta)
        self.tcp_socket.send(send_data.encode("utf-8"))
        receive = self.tcp_socket.recv(1024)
        if len(receive): print(str(receive, encoding='utf-8'))

    def delete_marker(self, name):
        send_data = "/api/markers/delete?name={}".format(name)
        self.tcp_socket.send(send_data.encode("utf-8"))
        receive = self.tcp_socket.recv(1024)
        if len(receive): print(str(receive, encoding='utf-8'))

    def move_cancel(self):
        send_data = "/api/move/cancel"
        self.tcp_socket.send(send_data.encode("utf-8"))
        receive = self.tcp_socket.recv(1024)
        if len(receive): print(str(receive, encoding='utf-8'))

    def make_plan(self, start, goal):
        send_data = "/api/make_plan?start_x={}&start_y={}&start_floor=2&goal_x={}&goal_y={}&goal_floor=2".format(
            start[0], start[1], goal[0], goal[1])
        self.tcp_socket.send(send_data.encode("utf-8"))
        receive = self.tcp_socket.recv(1024)
        receive = json.loads(receive)
        return receive

    def clear(self):
        receive = self.tcp_socket.recv(1024)
        if len(receive): print(str(receive, encoding='utf-8'))

    def judge(self):
        receive = self.tcp_socket.recv(1024)
        receive = json.loads(receive)
        return receive

    def get_path(self):
        """
        返回当前路径

        :return:
        """
        receive = self.tcp_socket.recv(1024)
        if len(receive): print(str(receive, encoding='utf-8'))
        send_data = "/api/get_planned_path"
        self.tcp_socket.send(send_data.encode("utf-8"))
        receive = self.tcp_socket.recv(51200)
        receive = json.loads(receive)
        print(receive)
        path = receive['results']['path']
        return path

    def set_color(self, rgb_value):
        """
        设置灯条RGB值, 一般不会立即生效，回去充电时会自动生效

        :param rgb_value: (R, G, B)
        :return:
        """
        # RGB_VALUE --> (R,G,B)
        send_data = "/api/LED/set_color?r={}&g={}&b={}".format(rgb_value[0], rgb_value[1], rgb_value[2])
        self.tcp_socket.send(send_data.encode("utf-8"))

    def get_current_pose(self):
        """
        返回当前世界坐标

        :return: [世界坐标x, 世界坐标y, 角度theta]
        """
        send_data = "/api/robot_status"
        self.tcp_socket.send(send_data.encode("utf-8"))
        receive = self.tcp_socket.recv(1024)
        receive = json.loads(receive)
        receive = receive['results']['current_pose']
        return [receive['x'], receive['y'], receive['theta']]

    def get_map_info(self):
        """
        得到地图的相关信息
        :return: [地图左下角世界坐标x, 地图左下角世界坐标y, 像素地图高度, 像素地图宽度, 分辨率]
        """
        send_data = "/api/map/get_current_map"
        self.tcp_socket.send(send_data.encode("utf-8"))
        receive = self.tcp_socket.recv(1024)
        receive = json.loads(receive)
        receive = receive['results']['info']
        return [receive['origin_x'], receive['origin_y'], receive['height'], receive['width'], receive['resolution']]

    def get_pose_pix(self):
        """
        返回像素坐标

        :return: [像素坐标x, 像素坐标y, 角度theta]
        """
        loc_x, loc_y, theta = self.get_current_pose()
        loc_x_pix = int((loc_x - self.origin_x) / self.resolution)
        loc_y_pix = int(self.height - (loc_y - self.origin_y) / self.resolution)
        return loc_x_pix, loc_y_pix, theta

    def get_pose_real_and_pix_and_isRunning(self):
        """
        返回世界坐标和像素坐标以及isRunning的状态

        :return: ([世界坐标x, 世界坐标y, 当前角度theta], [像素坐标x, 像素坐标y, 当前角度theta], isRunning)
        """
        receive = self.robot_status()
        current_pose = receive['results']['current_pose']
        loc_x_pix, loc_y_pix = self.real_to_pix(current_pose['x'], current_pose['y'])
        isRunning = receive['results']['move_status'] == 'running'
        return [current_pose['x'], current_pose['y'], current_pose['theta']], \
               [loc_x_pix, loc_y_pix, current_pose['theta']], isRunning

    def real_to_pix(self, real_x, real_y):
        """
        世界坐标转换成像素坐标

        :param real_x: 世界坐标x
        :param real_y: 世界坐标y
        :return: (像素坐标x, 像素坐标y)
        """
        return int((real_x - self.origin_x) / self.resolution), \
               int(self.height - (real_y - self.origin_y) / self.resolution)

    def pix_to_real(self, pix_x, pix_y):
        """
        像素坐标转换成世界坐标

        :param pix_x: 像素坐标x
        :param pix_y: 像素坐标y
        :return: (世界坐标x, 世界坐标y)
        """
        return self.resolution * pix_x + self.origin_x, self.origin_y - (pix_y - self.height) * self.resolution
