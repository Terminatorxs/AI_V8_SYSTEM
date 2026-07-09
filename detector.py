import cv2
import numpy as np
from rknnlite.api import RKNNLite


# ==========================
# RKNN模型
# ==========================

MODEL_PATH = "yolo11n.rknn"


print("Loading RKNN model...")


rknn = RKNNLite()


ret = rknn.load_rknn(
    MODEL_PATH
)

if ret != 0:
    raise RuntimeError(
        "load rknn failed"
    )


ret = rknn.init_runtime(
    core_mask=(
        RKNNLite.NPU_CORE_0 |
        RKNNLite.NPU_CORE_1 |
        RKNNLite.NPU_CORE_2
    )
)


if ret != 0:
    raise RuntimeError(
        "init runtime failed"
    )


print("RKNN model ready")



# ==========================
# COCO类别
# ==========================

CLASSES = [

    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat"

]



# ==========================
# 参数
# ==========================

INPUT_SIZE = 640

CONF_THRES = 0.35

NMS_THRES = 0.45





# ==========================
# 预处理
# ==========================

def preprocess(frame):


    img = cv2.resize(
        frame,
        (INPUT_SIZE, INPUT_SIZE)
    )


    img = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )


    # RKNN需要4维
    img = np.expand_dims(
        img,
        axis=0
    )


    return img





# ==========================
# NMS
# ==========================

def nms(results):


    if len(results)==0:

        return []



    boxes=[]

    scores=[]


    for r in results:


        x1,y1,x2,y2 = r["xyxy"]


        boxes.append(

            [
                x1,
                y1,
                x2-x1,
                y2-y1
            ]

        )


        scores.append(
            r["conf"]
        )



    keep = cv2.dnn.NMSBoxes(

        boxes,

        scores,

        CONF_THRES,

        NMS_THRES

    )



    output=[]


    if len(keep)>0:


        for i in keep:


            if isinstance(i, (list,tuple,np.ndarray)):

                i=i[0]


            output.append(
                results[i]
            )


    return output





# ==========================
# 后处理
# ==========================

def postprocess(
        outputs,
        frame
):


    if outputs is None:

        return []



    if len(outputs)==0:

        return []



    output = outputs[0]


    output = np.squeeze(
        output
    )



    if output.ndim !=2:

        return []



    # YOLO输出转换

    if output.shape[0] < output.shape[1]:

        output = output.T



    h,w = frame.shape[:2]


    results=[]



    for det in output:



        if len(det)<5:

            continue



        # 类别概率

        cls_scores = det[4:]



        cls_id = np.argmax(
            cls_scores
        )


        conf = cls_scores[cls_id]



        if conf < CONF_THRES:

            continue



        if cls_id >= len(CLASSES):

            continue




        cx,cy,bw,bh = det[:4]



        x1=int(

            (cx-bw/2)
            *w/INPUT_SIZE

        )


        y1=int(

            (cy-bh/2)
            *h/INPUT_SIZE

        )


        x2=int(

            (cx+bw/2)
            *w/INPUT_SIZE

        )


        y2=int(

            (cy+bh/2)
            *h/INPUT_SIZE

        )



        # 边界限制

        x1=max(0,min(x1,w))

        y1=max(0,min(y1,h))

        x2=max(0,min(x2,w))

        y2=max(0,min(y2,h))



        # 去掉异常框

        if x2<=x1 or y2<=y1:

            continue



        results.append({

            "cls":int(cls_id),

            "name":CLASSES[cls_id],

            "conf":float(conf),

            "xyxy":[

                x1,

                y1,

                x2,

                y2

            ]

        })



    # NMS去重

    results=nms(results)



    return results





# ==========================
# 对外检测接口
# ==========================

def detect(frame):


    img = preprocess(
        frame
    )



    outputs = rknn.inference(

        inputs=[img]

    )


    if outputs is None:

        return []



    return postprocess(

        outputs,

        frame

    )





# ==========================
# 类别接口
# ==========================

def get_class_name(cls_id):


    if cls_id < len(CLASSES):

        return CLASSES[cls_id]


    return "unknown"
