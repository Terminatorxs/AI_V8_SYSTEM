from flask import Flask, render_template, jsonify, session, redirect, request

from camera import (
    get_camera_stream,
    get_status,
    set_mode,
    register_face
)


app = Flask(__name__)

app.secret_key = "ai_security_v45"


# ======================
# 登录
# ======================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "123456":

            session["user"] = "admin"

            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="账号或密码错误"
        )

    return render_template("login.html")


# ======================
# 主控制台
# ======================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:

        return redirect("/")

    set_mode("dashboard")

    return render_template(
        "dashboard.html"
    )


# ======================
# 商场模式
# ======================

@app.route("/mall")
def mall():

    if "user" not in session:

        return redirect("/")

    set_mode("mall")

    return render_template(
        "mall.html"
    )


# ======================
# 禁区模式
# ======================

@app.route("/restricted")
def restricted():

    if "user" not in session:

        return redirect("/")

    set_mode("restricted")

    return render_template(
        "restricted.html"
    )


# ======================
# 校园模式
# ======================

@app.route("/campus")
def campus():

    if "user" not in session:

        return redirect("/")

    set_mode("campus")

    return render_template(
        "campus.html"
    )


# ======================
# 工厂模式
# ======================

@app.route("/factory")
def factory():

    if "user" not in session:

        return redirect("/")

    set_mode("factory")

    return render_template(
        "factory.html"
    )


# ======================
# 停车场模式
# ======================

@app.route("/parking")
def parking():

    if "user" not in session:

        return redirect("/")

    set_mode("parking")

    return render_template(
        "parking.html"
    )


# ======================
# 仓库模式
# ======================

@app.route("/warehouse")
def warehouse():

    if "user" not in session:

        return redirect("/")

    set_mode("warehouse")

    return render_template(
        "warehouse.html"
    )


# ======================
# 家庭模式
# ======================

@app.route("/home")
def home():

    if "user" not in session:

        return redirect("/")

    set_mode("home")

    return render_template(
        "home.html"
    )


# ======================
# 视频流
# ======================

@app.route("/video")
def video():

    return get_camera_stream()


# ======================
# AI状态接口
# ======================

@app.route("/status")
def status():

    return jsonify(
        get_status()
    )


# ======================
# 动态切换AI模式
# ======================

@app.route("/set_mode/<mode>")
def change_mode(mode):

    set_mode(mode)

    return jsonify({

        "status": "ok",

        "mode": mode

    })


# ======================
# 家庭模式：录入白名单人脸
# ======================

@app.route("/register_face", methods=["GET", "POST"])
def register_face_api():

    if "user" not in session:

        return jsonify({

            "status": "error",

            "message": "未登录，无法录入白名单"

        }), 401

    data = request.get_json(silent=True) or {}

    name = (
        data.get("name")
        or request.form.get("name")
        or request.args.get("name")
        or "whitelist_user"
    )

    result = register_face(name)

    return jsonify(result)


# ======================
# 退出
# ======================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ======================
# 启动
# ======================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False,

        use_reloader=False

    )
