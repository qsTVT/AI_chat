import json
import base64
import io
from PIL import Image
import numpy as np
#把前端传来的图片数据转换成二进制编码
def get_image_byte(request):
    data = json.loads(request.body.decode('utf-8'))
    image_data = data['image']
    # 解码图像数据
    image_data = image_data.split(',')[1]
    # 获取图片的二进制编码
    image_bytes = base64.b64decode(image_data)
    return image_bytes

#把前端传来的图片数据转换成图片矩阵数据
def get_image_array(request):
        data = json.loads(request.body.decode('utf-8'))
        image_data = data['image']
        # 解码图像数据
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes))
        #转换成图片矩阵
        img = np.array(img)
        return img