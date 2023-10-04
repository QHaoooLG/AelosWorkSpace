import time
import CMDcontrol as CMD
import cv2
import threading
import numpy as np
import rospy
import math
from functools import wraps

from image_Tag_converter import ImgConverter
from image_Tag_converter import TagConverter
import action_includ as action

#定义一些参数
Head_img = None

marker = None
avg_x = None
avg_y = None
avg_yaw = None

head_circle_x = None
head_circle_y = None

# key = 0
real = 1

# 不同色块的hsv范围
color_range = {
    'red_box0': [(170,120,200),(190,140,260)],
    'red_box1': [(0, 128, 105), (45, 191, 170)],
    'red_box2': [(140, 128, 105), (179, 191, 170)],
    'red_box3': [(156, 43, 46), (180, 255, 255)]
}

#动作指令监听线程
def move_action():
    if real :
        CMD.CMD_transfer()
th1 = threading.Thread(target=move_action)
th1.setDaemon(True)
th1.start()

#获取图像
def get_img():
    global Head_img,HeadOrg
    global ret
    image_reader_chest = ImgConverter()
    while True:
        ret, HeadOrg = image_reader_chest.chest_image()
        time.sleep(1)
        if HeadOrg is not None:
            Head_img = HeadOrg
            time.sleep(0.05)
            #Head_img = cv2.flip(Head_img, 1)
        else:
            time.sleep(1)
            print("暂时未获取到图像")
th2 = threading.Thread(target=get_img)
th2.setDaemon(True)
th2.start()

#查找方块
def find_box(img,color_name):
    global head_circle_x, head_circle_y
    if Head_img is None:
        print('等待获取图像中...')
        time.sleep(1)
    else:
        red_box_img = img
        red_box_img_bgr = cv2.cvtColor(red_box_img, cv2.COLOR_RGB2BGR)  # 将图片转换到BRG空间
        red_box_img_hsv = cv2.cvtColor(red_box_img, cv2.COLOR_BGR2HSV)  # 将图片转换到HSV空间
        red_box_img = cv2.GaussianBlur(red_box_img_hsv, (3, 3), 0)  # 高斯模糊
        red_box_img_mask = cv2.inRange(red_box_img, color_range[color_name][0], color_range[color_name][1])  # 二值化
        red_box_img_closed = cv2.erode(red_box_img_mask, None, iterations=2)  # 腐蚀
        red_box_img_opened = cv2.dilate(red_box_img_mask, np.ones((4, 4), np.uint8), iterations=2)  # 膨胀    先腐蚀后运算等同于开运算
        (contours, hierarchy) = cv2.findContours(red_box_img_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if len(contours) != 0:
            for cn in contours:
                (head_circle_x, head_circle_y), head_radius = cv2.minEnclosingCircle(cn)
                contour_area = math.fabs(cv2.contourArea(cn))
                max_cn = np.argmax(contour_area)
                if contour_area > 600 :
                    cv2.circle(red_box_img_bgr,(int(head_circle_x), int(head_circle_y)),int(head_radius),(0,0,255))

        else:
            print('正在寻找目标')

#去搬箱子
def goto_box():
    print('已经找到目标，准备调整位置')
    global ID
    if head_circle_x is None :
        print('等待中获取坐标中...')
        time.sleep(1)
    else:
        if head_circle_y < 150:  # 240 - 50  (150)
            print("正在左侧移 ")
            action.L_move(1)
            time.sleep(1)
        elif head_circle_y > 220:    # 240 + 50  (220)
            print("正在右侧移 ")
            action.R_move(1)
            time.sleep(1)
        else:
            if head_circle_x > 180:  #320 + 20   (180)
                print("前进")
                action.go_slow(1)
                time.sleep(0.5)
            elif head_circle_x < 100:  #320 - 20 (100)
                print("后退")
                action.back_slow(1)
                time.sleep(0.5)
            else:
                print("开始抱箱子")
                action.R_move(1)
                action.box_up(1)
                ID+=1

# def market():
#     global ID
#     Tag = TagConverter()
#     if Head_img is not None:
#         if ID == marker[0]:
#             return True
#         else:
#             return False
# th3 = threading.Thread(target=market)
# th3.setDaemon(True)
# th3.start()

#获取ARtag信息并处理
@timefn
def get_marker(key):
    global marker,avg_x,avg_y,avg_yaw,ID
    # global x_step1,x_step2,y_step,yaw_step1,yaw_step2
    tag_x, tag_y, tag_yaw = [], [], []
    while key:
        marker = Tag.get_nearest_marker()
        if len(tag_x) == 3:
            avg_x = np.mean(tag_x)
            avg_y = np.mean(tag_y)
            avg_yaw = np.mean(tag_yaw)
            rad_z = -avg_yaw - 90
            rad_z = rad_z/180*math.pi
            mat_a = [[math.cos(rad_z),-math.sin(rad_z),0],[math.sin(rad_z),math.cos(rad_z),0],[0,0,1]]
            mat_b = [[avg_x],[avg_y],[0]]
            res = matrixMul(mat_a,mat_b)
            avg_x = res[0][0]
            avg_y = res[1][0]
            key = 0
        elif len(marker) == 0:
            print('无Tag')
            if ID == 2:
                action.R_move(1)
            if ID == 3:
                action.back_fast(1)
            if ID == 4:
                action.back_fast(1)
            continue
        elif ID == marker[0]:
            tag_x.append(int(marker[1]*100))
            tag_y.append(int(marker[2]*100))
            tag_yaw.append(int(marker[3]))
        else:
            print('tag不匹配')
            if ID == 2:
                action.R_move(1)
            if ID == 3:
                action.back_fast(1)
            if ID == 4:
                action.back_fast(1)
# th2 = threading.Thread(target=get_marker)
# th2.setDaemon(True)
# th2.start()
@timefn
def action_step_yaw(yaw_low,yaw_high):
    if avg_yaw < yaw_low:
        chg_yaw = yaw_low - avg_yaw
        yaw_step1 = int(chg_yaw / 15);yaw_step2 = math.ceil((chg_yaw - yaw_step1 * 15) / 7)
        print('yaw_step1=',yaw_step1,'yaw_step2=',yaw_step2)
        action.R_turn(yaw_step1)
        action.R_turn_slow(yaw_step2)
    elif avg_yaw > yaw_high:
        chg_yaw = avg_yaw - yaw_high
        yaw_step1 = int(chg_yaw / 15);yaw_step2 = math.ceil((chg_yaw - yaw_step1 * 15) / 7)
        print('yaw_step1=', yaw_step1, 'yaw_step2=', yaw_step2)
        action.L_turn(yaw_step1)
        action.L_turn_slow(yaw_step2)
@timefn
def action_step(x_low,x_high,y_low,y_high):
    if avg_x < x_low:
        chg_x = x_low - avg_x
        x_step1 = int(chg_x / 4.5);x_step2 = math.ceil((chg_x - x_step1 * 4.5) / 2.5)
        print('x_step1=', x_step1, 'x_step2=', x_step2)
        action.back_fast(x_step1)
        action.back_slow(x_step2)
    elif avg_x > x_high:
        chg_x = avg_x - x_high
        x_step1 = int(chg_x / 4.5);x_step2 = math.ceil((chg_x - x_step1 * 4.5) / 2.5)
        print('x_step1=', x_step1, 'x_step2=', x_step2)
        action.go_fast(x_step1)
        action.go_slow(x_step2)
    if avg_y < y_low:
        chg_y = y_low - avg_y
        y_step = math.ceil(chg_y / 4.5)
        print('y_step',y_step)
        action.R_move(y_step)
    elif avg_y > y_high:
        chg_y = avg_y - y_high
        y_step = math.ceil(chg_y / 4.5)
        print('y_step', y_step)
        action.L_move(y_step)
@timefn
def box_action_step_yaw(yaw_low,yaw_high):
    if avg_yaw < yaw_low:
        chg_yaw = yaw_low - avg_yaw
        yaw_step1 = math.ceil(chg_yaw / 7)
        print('yaw_step1=',yaw_step1)
        action.box_R_turn(yaw_step1)
    elif avg_yaw > yaw_high:
        chg_yaw = avg_yaw - yaw_high
        yaw_step1 = math.ceil(chg_yaw / 8)
        print('yaw_step1=', yaw_step1)
        action.box_L_turn(yaw_step1)
@timefn
def box_action_step(x_low,x_high,y_low,y_high):   #参数未修改
    if avg_x < x_low:
        chg_x = x_low - avg_x
        x_step1 = int(chg_x / 4.5);x_step2 = math.ceil((chg_x - x_step1 * 4.5) / 2.5)
        print('x_step1=', x_step1, 'x_step2=', x_step2)
        action.back_fast(x_step1)
        action.back_slow(x_step2)
    elif avg_x > x_high:
        chg_x = avg_x - x_high
        x_step1 = int(chg_x / 4.5);x_step2 = math.ceil((chg_x - x_step1 * 4.5) / 2.5)
        print('x_step1=', x_step1, 'x_step2=', x_step2)
        action.go_fast(x_step1)
        action.go_slow(x_step2)
    if avg_y < y_low:
        chg_y = y_low - avg_y
        y_step = math.ceil(chg_y / 4.5)
        print('y_step',y_step)
        action.R_move(y_step)
    elif avg_y > y_high:
        chg_y = avg_y - y_high
        y_step = math.ceil(chg_y / 4.5)
        print('y_step', y_step)
        action.L_move(y_step)


def matrixMul(A, B):   #矩阵相乘
    res = [[0] * len(B[0]) for i in range(len(A))]
    for i in range(len(A)):
        for j in range(len(B[0])):
            for k in range(len(B)):
                res[i][j] += int(A[i][k] * B[k][j])
    return res

def timefn(fn):
    """计算性能的修饰器"""

    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        print(f" {fn.__name__} took {t2 - t1: .5f} s")
        return result

    return measure_time

if __name__ == '__main__':
    rospy.init_node('image_listener')
    Tag = TagConverter()
    time.sleep(1)
    ID = 0
    step = 1
    n = 1
    while True:
        while HeadOrg is None:
            print('wite')
        if step == 1:  #转身寻找方块
            print('启动')
            action.R_turn_big(4)
            action.R_move(2)
            while True:
                if ID == 0:
                    find_box(Head_img, 'red_box3')
                    goto_box()
                elif ID == 1:
                    break
            action.box_go_fast(2)
            action.box_R_turn2(3)
            step = 0
        if step == 2:
            action.go_fast(1)
            find_box(Head_img, 'red_box3')
            goto_box()
            action.box_L_turn2(4)
            action.go_fast(1)
            step = 0
            ID=1
        if ID == 1:
            if n == 1:
                get_marker(1)
                action_step_yaw(-100, -80)
                action_step(12, 17, -4, 4)
                get_marker(1)
                action_step_yaw(-100, -80)
                print(avg_x, avg_y, avg_yaw)
                print('1第1次对正结束')
                get_marker(1)
                action_step_yaw(-95,-85)
                action_step(2,5,-2,2)
                get_marker(1)
                action_step_yaw(-95,-85)
                print(avg_x, avg_y, avg_yaw)
                print('1第2次对正结束')
                action.go_fast(2)
                n = -n
                ID+=1
            elif n == -1:
                get_marker(1)
                action_step_yaw(-105,-85)
                action_step(7,10,-4,4)
                get_marker(1)
                action_step_yaw(-105, -85)
                step = 2
                ID = 0
                n = -n
        if ID == 2:
            get_marker(1)
            action_step_yaw(-100, -80)
            action_step(15, 18, -4, 4)
            get_marker(1)
            action_step_yaw(-100, -80)
            print(avg_x, avg_y, avg_yaw)
            print('2第1次对正结束')
            get_marker(1)
            action_step_yaw(-95,-85)
            action_step(10, 13, -3, 3)
            get_marker(1)
            action_step_yaw(-95, -85)
            print(avg_x, avg_y, avg_yaw)
            print('2第2次对正结束')
            action.R_move3(8)
            ID+=1
        if ID == 3:
            get_marker(1)
            action_step_yaw(-95,-85)
            action_step(7, 10, -3, 3)
            get_marker(1)
            action_step_yaw(-95, -85)
            print(avg_x, avg_y, avg_yaw)
            print('3第1次对正结束')
            action.R_move3(4)
            ID+=1
        if ID == 4:
            get_marker(1)
            action_step_yaw(-95,-85)
            action_step(7, 10, -4, 4)
            get_marker(1)
            action_step_yaw(-95, -85)
            print(avg_x, avg_y, avg_yaw)
            print('4第1次对正结束')
            action.go_fast(4)
            ID+=1
        if ID == 5:
            get_marker(1)
            action_step_yaw(-100,-80)
            action_step(12, 17, -4, 4)
            get_marker(1)
            action_step_yaw(-100, -80)
            print(avg_x, avg_y, avg_yaw)
            print('5第1次对正结束')
            get_marker(1)
            action_step_yaw(-95, -75)
            action_step(7, 10, -3, 3)
            get_marker(1)
            action_step_yaw(-95, -75)
            print(avg_x, avg_y, avg_yaw)
            print('5第5次对正结束')
            action.L_move3(8)
            ID+=1
        # if ID == 6:
        #     key = 1
        #     get_marker()
        #     action_step(7, 10, -4, 4, -105, -85)
        #     action.go_fast(4)
        #     action.box_down_H(1)
        #     action.R_turn_big(4)
        #     action.R_move(2)
        #     key = 1
        #     get_marker()
        #     action_step(7, 10, -4, 4, -105, -85)
        #     ID+=1
        # if ID == 7:
        #     key = 1
        #     get_marker()
        #     action_step(7, 10, -4, 4, -105, -85)
        #     action.L_move(3)
        #     ID+=1
        # if ID == 8:
        #     key = 1
        #     get_marker()
        #     action_step(7, 10, -4, 4, -105, -85)
        #     action.L_move(3)
        #     ID+=1
        # if ID == 9:
        #     key = 1
        #     get_marker()
        #     action_step(7, 10, -4, 4, -105, -85)
        #     action.R_move(3)
        #     ID+=1
        # if ID == 10:
        #     key = 1
        #     get_marker()
        #     action_step(7, 10, -4, 4, -105, -85)
        #     action.R_move(3)
        #     ID = 1