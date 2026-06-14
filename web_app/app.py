import os
import pandas as pd
from flask import Flask, jsonify, make_response, render_template, request
from core.db import (
    init_db, get_materials, add_or_update_material, delete_material,
    save_history, get_history_list, get_history_detail, get_datasets, 
    get_connection, get_engine
)
from core.analyzer import suggest_min_cutoff, perform_analysis
from core.spectrum_plot import (
    render_spectrum_fit_png_base64,
    render_wafer_heatmap_png_base64,
    render_crystal_lattice_png_base64,
    render_standing_wave_png_base64,
    render_dispersion_png_base64,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

# Ensure DB initialized
init_db()


@app.after_request
def add_mobile_cors_headers(response):
    """Allow the DBuilder/uni-app client to call the Flask API during dev."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response


@app.before_request
def handle_mobile_preflight():
    if request.method == "OPTIONS":
        return make_response("", 204)

# ---- Page Routes ---- #

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/simulator")
def simulator():
    return render_template("simulator.html")

@app.route("/materials")
def materials():
    return render_template("materials.html")

@app.route("/history")
def history():
    return render_template("history.html")

# ---- API Routes ---- #

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"ok": True, "service": "EPI-Vision API"})

@app.route("/api/datasets")
def api_datasets():
    return jsonify({"items": get_datasets()})

@app.route("/api/dataset_data", methods=["GET"])
def api_get_dataset_data():
    material = request.args.get("material")
    angle = request.args.get("angle")
    if not material or not angle:
        return jsonify({"ok": False, "error": "Missing material or angle"}), 400
    try:
        angle_float = float(angle)
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid angle form"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT wavenumber, reflectance FROM ExperimentalData WHERE material=? AND angle=? ORDER BY wavenumber", (material, angle_float))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return jsonify({"ok": False, "error": "Dataset not found"}), 404

    return jsonify({
        "ok": True,
        "x": [r["wavenumber"] for r in rows],
        "y": [r["reflectance"] for r in rows]
    })

@app.route("/api/materials", methods=["GET"])
def api_get_materials():
    return jsonify({"items": get_materials()})

@app.route("/api/materials", methods=["POST"])
def api_post_materials():
    data = request.json or {}
    name = data.get("name")
    n_film = data.get("n_film")
    n_sub = data.get("n_sub")
    if not name or not n_film or not n_sub:
        return jsonify({"ok": False, "error": "Missing parameters"}), 400
    try:
        add_or_update_material(name.strip(), float(n_film), float(n_sub))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/materials/<name>", methods=["DELETE"])
def api_delete_material(name):
    try:
        delete_material(name)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/suggest_cutoff", methods=["POST"])
def api_suggest_cutoff():
    data = request.get_json(force=True, silent=True) or {}
    material = (data.get("material") or "").strip()
    try:
        angle = float(data.get("angle"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "角度无效"}), 400
    
    r = suggest_min_cutoff(material, angle)
    return jsonify(r), 200 if r.get("ok") else 400

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(force=True, silent=True) or {}
    material = (data.get("material") or "").strip()
    try:
        angle_deg = float(data.get("angle_deg"))
        min_cutoff = float(data.get("min_cutoff", 1500))
        n_film = float(data.get("n_film", 2.6))
        n_sub = float(data.get("n_sub", 2.55))
        peak_distance = int(float(data.get("peak_distance", 30)))
        n_min = float(data.get("n_min", 1.8))
        n_max = float(data.get("n_max", 4.2))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "数值参数无效"}), 400

    method = (data.get("method") or "峰值间距法（快速）").strip()
    inversion = (data.get("inversion") or "固定折射率（反演厚度）").strip()

    if not material:
        return jsonify({"ok": False, "error": "请选择材料"}), 400

    out = perform_analysis(
        material=material,
        angle_deg=angle_deg,
        min_cutoff=min_cutoff,
        method=method,
        inversion_mode=inversion,
        n_film=n_film,
        n_sub=n_sub,
        peak_distance=peak_distance,
        n_min=n_min,
        n_max=n_max,
    )

    # Matplotlib 光谱拟合图（与 epi_vision_qt.py 一致），供前端直接嵌入
    if out.get("ok"):
        try:
            plot_title = f"{material} - {angle_deg}度 | 起点 {min_cutoff:.0f} cm$^{{-1}}$"
            out["spectrum_plot_b64"] = render_spectrum_fit_png_base64(
                out["x"],
                out["y"],
                out["fit_y"],
                out["peaks_x"],
                out["peaks_y"],
                plot_title,
            )
        except Exception as exc:  # noqa: BLE001
            out["spectrum_plot_error"] = str(exc)
    
    # Save to history if successful
    if out.get("ok"):
        dataset_name = f"{material} - {angle_deg}度"
        result_for_history = dict(out)
        result_for_history.pop("spectrum_plot_b64", None)
        save_history(
            dataset_name=dataset_name,
            method=method,
            n_film=out["n_film"],
            n_sub=out["n_sub"],
            thickness=out["thickness_um"],
            fit_confidence=out.get("fit_confidence", 0),
            mse=out.get("mse_final", 0),
            parameters=data,
            result=result_for_history
        )
        
    status = 200 if out.get("ok") else 400
    return jsonify(out), status


@app.route("/api/history", methods=["GET"])
def api_get_history():
    return jsonify({"items": get_history_list()})

@app.route("/api/history/<int:history_id>", methods=["GET"])
def api_get_history_detail(history_id):
    detail = get_history_detail(history_id)
    if detail:
        # 历史详情也返回与主分析页一致的 Matplotlib 光谱拟合图
        try:
            r = detail.get("result_json") or {}
            if all(k in r for k in ("x", "y", "fit_y", "peaks_x", "peaks_y")):
                detail["spectrum_plot_b64"] = render_spectrum_fit_png_base64(
                    r["x"],
                    r["y"],
                    r["fit_y"],
                    r["peaks_x"],
                    r["peaks_y"],
                    f"历史回放 | {detail.get('dataset_name', '')}",
                )
        except Exception as exc:  # noqa: BLE001
            detail["spectrum_plot_error"] = str(exc)
        return jsonify({"ok": True, "data": detail})
    return jsonify({"ok": False, "error": "Not found"}), 404

@app.route("/api/import", methods=["POST"])
def api_import():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "未上传文件"}), 400
    f = request.files["file"]
    material = (request.form.get("material") or "").strip()
    replace = request.form.get("replace") in ("1", "true", "on", "yes", True)
    try:
        angle = float(request.form.get("angle", ""))
    except ValueError:
        return jsonify({"ok": False, "error": "角度请输入数字"}), 400
    if not material:
        return jsonify({"ok": False, "error": "请输入材料名称"}), 400

    name = (f.filename or "").lower()
    try:
        if name.endswith(".csv"):
            raw = pd.read_csv(f)
        else:
            raw = pd.read_excel(f)
    except Exception as e:
        return jsonify({"ok": False, "error": f"读取失败: {e}"}), 400

    if raw.shape[1] < 2:
        return jsonify({"ok": False, "error": "至少需要两列：波数、反射率"}), 400

    x = pd.to_numeric(raw.iloc[:, 0], errors="coerce")
    y = pd.to_numeric(raw.iloc[:, 1], errors="coerce")
    clean = pd.DataFrame({"wavenumber": x, "reflectance": y}).dropna().sort_values("wavenumber")
    if clean.empty:
        return jsonify({"ok": False, "error": "无有效数值行"}), 400

    conn = get_connection()
    cur = conn.cursor()
    if replace:
        cur.execute("DELETE FROM ExperimentalData WHERE material=? AND angle=?", (material, angle))
    conn.commit()
    
    payload = pd.DataFrame({
        "material": material,
        "angle": angle,
        "wavenumber": clean["wavenumber"].values,
        "reflectance": clean["reflectance"].values,
    })
    
    # Save the dataframe to sql using pandas
    try:
        engine = get_engine()
        # Using method='multi' and chunksize for performance
        payload.to_sql("ExperimentalData", engine, if_exists="append", index=False, method='multi', chunksize=1000)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": f"数据库写入失败: {e}"}), 500
        
    return jsonify({"ok": True, "count": len(payload), "label": f"{material} - {angle}度"})

# ---- Visualization Plot Endpoints (server-rendered base64 for mobile) ---- #

@app.route("/api/plot/wafer", methods=["POST"])
def api_plot_wafer():
    data = request.get_json(force=True, silent=True) or {}
    try:
        thickness_um = float(data.get("thickness_um", 1.0))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid thickness"}), 400
    material = (data.get("material") or "").strip()
    try:
        b64 = render_wafer_heatmap_png_base64(thickness_um, material)
        return jsonify({"ok": True, "image_b64": b64})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/plot/crystal", methods=["POST"])
def api_plot_crystal():
    data = request.get_json(force=True, silent=True) or {}
    material = (data.get("material") or "SiC").strip()
    try:
        b64 = render_crystal_lattice_png_base64(material)
        return jsonify({"ok": True, "image_b64": b64})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/plot/standing-wave", methods=["POST"])
def api_plot_standing_wave():
    data = request.get_json(force=True, silent=True) or {}
    wave_x = data.get("swave_x")
    depth_z = data.get("swave_y")
    wave_z = data.get("swave_z")
    title = (data.get("title") or "").strip()
    if not wave_x or not depth_z or not wave_z:
        return jsonify({"ok": False, "error": "Missing swave_x / swave_y / swave_z fields"}), 400
    try:
        b64 = render_standing_wave_png_base64(wave_x, depth_z, wave_z, title)
        return jsonify({"ok": True, "image_b64": b64})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/plot/dispersion", methods=["POST"])
def api_plot_dispersion():
    data = request.get_json(force=True, silent=True) or {}
    required = ("disp_x", "disp_n", "disp_k", "disp_ref_n", "disp_upper", "disp_lower")
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"ok": False, "error": f"Missing fields: {missing}"}), 400
    title = (data.get("title") or "").strip()
    try:
        b64 = render_dispersion_png_base64(
            data["disp_x"], data["disp_n"], data["disp_k"],
            data["disp_ref_n"], data["disp_upper"], data["disp_lower"],
            title,
        )
        return jsonify({"ok": True, "image_b64": b64})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=True)
