import tkinter as tk
from tkinter import ttk, messagebox
from geographiclib.geodesic import Geodesic
import math

# 地球椭球模型常量
GEODESIC = Geodesic.WGS84

def calculate_target_coords_geodesic(lat1, lon1, azimuth, distance_nm):
    """
    使用 geographiclib 的 Geodesic 类计算目标点坐标
    """
    distance = distance_nm * 1852  # 海里转米
    result = GEODESIC.Direct(lat1, lon1, azimuth, distance)
    return result['lat2'], result['lon2']

def get_radius_letter(distance_nm):
    """
    根据距离获取单字母标记
    """
    ranges = [
        (0.1, 1.4, 'A'), (1.5, 2.4, 'B'), (2.5, 3.4, 'C'), (3.5, 4.4, 'D'),
        (4.5, 5.4, 'E'), (5.5, 6.4, 'F'), (6.5, 7.4, 'G'), (7.5, 8.4, 'H'),
        (8.5, 9.4, 'I'), (9.5, 10.4, 'J'), (10.5, 11.4, 'K'), (11.5, 12.4, 'L'),
        (12.5, 13.4, 'M'), (13.5, 14.4, 'N'), (14.5, 15.4, 'O'), (15.5, 16.4, 'P'),
        (16.5, 17.4, 'Q'), (17.5, 18.4, 'R'), (18.5, 19.4, 'S'), (19.5, 20.4, 'T'),
        (20.5, 21.4, 'U'), (21.5, 22.4, 'V'), (22.5, 23.4, 'W'), (23.5, 24.4, 'X'),
        (24.5, 25.4, 'Y'), (25.5, 26.4, 'Z')
    ]
    for low, high, letter in ranges:
        if low <= distance_nm <= high:
            return letter
    # 'Z' is chosen as the fallback letter when the distance does not fall within any specified range
    return 'Z'

class CoordinateCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("坐标计算工具")

        # 设置窗口大小及位置（可按需改动）
        self.root.geometry("700x650") # 调整窗口高度以适应新的输入框

        # 模式选择
        self.mode_var = tk.StringVar(value="WAYPOINT")
        self.create_mode_selection()

        # 包含全部输入控件的框架
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=5, fill="x")

        # 分别创建 WAYPOINT 和 FIX 的界面
        self.waypoint_frame = tk.Frame(self.input_frame)
        self.fix_frame = tk.Frame(self.input_frame)

        self.create_waypoint_ui()
        self.create_fix_ui()

        # 输出区域
        self.create_output_ui()

        # 默认显示 WAYPOINT 界面
        self.on_mode_change()

        # 在界面下方添加操作按钮区
        self.create_bottom_buttons()

    def create_mode_selection(self):
        """
        创建顶部的模式选择区域
        """
        frm_mode = tk.LabelFrame(self.root, text="模式选择", padx=10, pady=5)
        frm_mode.pack(padx=10, pady=5, fill="x")

        tk.Label(frm_mode, text="选择模式:").pack(side=tk.LEFT, padx=5)
        combo_mode = ttk.Combobox(frm_mode, textvariable=self.mode_var, values=('WAYPOINT', 'FIX'), state="readonly")
        combo_mode.pack(side=tk.LEFT, padx=5)

        # 当选择发生变化时触发
        # 'write' 表示当变量的值发生变化时触发回调函数
        self.mode_var.trace_add('write', self.on_mode_change)

    def on_mode_change(self, *args):
        """
        根据模式切换显示不同的输入表单
        """
        current_mode = self.mode_var.get()
        # 隐藏两个界面
        self.waypoint_frame.pack_forget()
        self.fix_frame.pack_forget()

        # 根据模式显示控件
        if current_mode == "WAYPOINT":
            self.waypoint_frame.pack(side=tk.TOP, fill="x", pady=5)
        else:
            self.fix_frame.pack(side=tk.TOP, fill="x", pady=5)

    def create_waypoint_ui(self):
        """
        创建 WAYPOINT 界面的输入区域
        """
        frm = self.waypoint_frame

        tk.Label(frm, text="VOR/DME/NDB 坐标 (纬度 经度):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_vor_coords = tk.Entry(frm, width=30)
        self.entry_vor_coords.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frm, text="磁航向 (度):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_bearing = tk.Entry(frm, width=30)
        self.entry_bearing.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frm, text="距离 (海里):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_distance = tk.Entry(frm, width=30)
        self.entry_distance.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(frm, text="磁差 (度):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entry_declination = tk.Entry(frm, width=30)
        self.entry_declination.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(frm, text="机场代码 (4个字母):").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.entry_airport_code = tk.Entry(frm, width=30)
        self.entry_airport_code.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(frm, text="VOR 标识符 (3-4个字母):").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.entry_vor_identifier = tk.Entry(frm, width=30)
        self.entry_vor_identifier.grid(row=5, column=1, padx=5, pady=5)

        tk.Label(frm, text="操作类型:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.combo_operation_type = ttk.Combobox(frm, values=["离场", "进场", "进近"], state="readonly")
        self.combo_operation_type.current(0)
        self.combo_operation_type.grid(row=6, column=1, padx=5, pady=5)

        btn_calc = tk.Button(frm, text="计算 Waypoint", command=self.on_calculate_waypoint)
        btn_calc.grid(row=7, column=0, columnspan=2, pady=5)

    def create_fix_ui(self):
        """
        创建 FIX 界面的输入区域
        """
        frm = self.fix_frame

        tk.Label(frm, text="FIX 坐标 (纬度 经度):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_fix_coords = tk.Entry(frm, width=30)
        self.entry_fix_coords.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frm, text="FIX 类型:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.combo_fix_type = ttk.Combobox(frm, values=["VORDME", "VOR", "NDBDME", "NDB", "ILS", "RNP"], state="readonly")
        self.combo_fix_type.current(0)
        self.combo_fix_type.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frm, text="FIX 使用:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.combo_fix_usage = ttk.Combobox(frm,
            values=[
                "Final approach fix",
                "Initial approach fix",
                "Intermediate approach fix",
                "Final approach course fix",
                "Missed approach point fix"
            ],
            state="readonly"
        )
        self.combo_fix_usage.current(0)
        self.combo_fix_usage.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(frm, text="跑道编码 (两位数字):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entry_runway_code = tk.Entry(frm, width=30)
        self.entry_runway_code.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(frm, text="机场代码 (4个字母):").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.entry_fix_airport_code = tk.Entry(frm, width=30)
        self.entry_fix_airport_code.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(frm, text="操作类型:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.combo_fix_operation_type = ttk.Combobox(frm, values=["离场", "进场", "进近"], state="readonly")
        self.combo_fix_operation_type.current(0)
        self.combo_fix_operation_type.grid(row=5, column=1, padx=5, pady=5)

        btn_calc = tk.Button(frm, text="计算 FIX", command=self.on_calculate_fix)
        btn_calc.grid(row=6, column=0, columnspan=2, pady=5)

    def create_output_ui(self):
        """
        创建输出区域
        """
        frm_output = tk.LabelFrame(self.root, text="输出结果", padx=10, pady=5)
        frm_output.pack(padx=10, pady=5, fill="both", expand=True)

        self.output_entry = tk.Text(frm_output, width=80, height=8) # 增加高度以防输出内容过长
        self.output_entry.pack(padx=5, pady=5, fill="both", expand=True)

    def create_bottom_buttons(self):
        """
        创建底部操作按钮，如清空、复制等
        """
        frm_btn = tk.Frame(self.root)
        frm_btn.pack(padx=10, pady=5, fill="x")

        btn_clear = tk.Button(frm_btn, text="清空输入", command=self.clear_fields)
        btn_clear.pack(side=tk.LEFT, padx=5)

        btn_copy = tk.Button(frm_btn, text="复制结果", command=self.copy_output)
        btn_copy.pack(side=tk.LEFT, padx=5)

        btn_exit = tk.Button(frm_btn, text="退出", command=self.root.quit)
        btn_exit.pack(side=tk.RIGHT, padx=5)

    def clear_fields(self):
        """
        清空所有输入和输出
        """
        if self.mode_var.get() == "WAYPOINT":
            self.entry_vor_coords.delete(0, tk.END)
            self.entry_bearing.delete(0, tk.END)
            self.entry_distance.delete(0, tk.END)
            self.entry_declination.delete(0, tk.END)
            self.entry_airport_code.delete(0, tk.END)
            self.entry_vor_identifier.delete(0, tk.END) # 清空 VOR Identifier
        else:
            self.entry_fix_coords.delete(0, tk.END)
            self.entry_runway_code.delete(0, tk.END)
            self.entry_fix_airport_code.delete(0, tk.END)

        self.output_entry.delete(1.0, tk.END)

    def copy_output(self):
        """
        将输出结果复制到剪贴板
        """
        output_text = self.output_entry.get(1.0, tk.END).strip()
        if output_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(output_text)
            messagebox.showinfo("复制结果", "结果已复制到剪贴板！")
        else:
            messagebox.showwarning("复制结果", "没有可复制的文本！")

    def calculate_target_coords_vincenty(self, lat_vor, lon_vor, magnetic_bearing, distance_nm, declination):
        """
        根据 VOR 的坐标、磁航向、距离和磁差计算目标点的坐标
        """
        true_bearing = (magnetic_bearing + declination) % 360
        return calculate_target_coords_geodesic(lat_vor, lon_vor, true_bearing, distance_nm)

    def validate_input(self, mode):
        """
        验证输入的有效性
        """
        if mode == "WAYPOINT":
            try:
                lat_vor, lon_vor = map(float, self.entry_vor_coords.get().split())
                if not (-90 <= lat_vor <= 90 and -180 <= lon_vor <= 180):
                    raise ValueError("经纬度超出范围 (±90 / ±180)")
                magnetic_bearing = float(self.entry_bearing.get())
                if not (0 <= magnetic_bearing < 360):
                    raise ValueError("磁航向应在 0~359 范围内")
                distance_nm = float(self.entry_distance.get())
                if distance_nm <= 0:
                    raise ValueError("距离应大于 0 海里")
                declination = float(self.entry_declination.get())
                airport_code = self.entry_airport_code.get().strip().upper()
                if len(airport_code) != 4:
                    raise ValueError("机场代码必须是 4 个字母")
                vor_identifier = self.entry_vor_identifier.get().strip().upper() # 获取 VOR Identifier
                if vor_identifier and not (3 <= len(vor_identifier) <= 4) and not vor_identifier.isalpha(): # Basic validation for identifier format
                    raise ValueError("VOR 标识符应为 3-4 个字母")

                return lat_vor, lon_vor, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier # 返回 vor_identifier
            except ValueError as e:
                messagebox.showerror("输入错误", f"WAYPOINT 模式输入错误：{e}")
                return None

        elif mode == "FIX":
            try:
                lat, lon = map(float, self.entry_fix_coords.get().split())
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("经纬度超出范围 (±90 / ±180)")
                fix_type = self.combo_fix_type.get()
                fix_usage = self.combo_fix_usage.get()
                runway_code = self.entry_runway_code.get().strip()
                if not runway_code.isdigit() or not 0 <= int(runway_code) <= 99:
                    raise ValueError("跑道编码应为 0~99 的两位数字")
                airport_code = self.entry_fix_airport_code.get().strip().upper()
                if len(airport_code) != 4:
                    raise ValueError("机场代码必须是 4 个字母")
                return (lat, lon, fix_type, fix_usage, runway_code, airport_code)
            except ValueError as e:
                messagebox.showerror("输入错误", f"FIX 模式输入错误：{e}")
                return None

    def process_output(self, result, mode, vor_identifier="", magnetic_bearing="", distance_nm=""): # 添加 vor_identifier, magnetic_bearing, distance_nm 参数
        """
        处理计算结果并显示输出
        """
        if mode == "WAYPOINT":
            lat_target, lon_target, radius_letter, airport_code, operation_code = result
            output = (
                f"{lat_target:.9f} {lon_target:.9f} "
                f"D{int(magnetic_bearing):03d}{radius_letter} " # 使用传入的 magnetic_bearing
                f"{airport_code} {airport_code[:2]}" # Removed operation_code here
            )
            if vor_identifier: # 如果 VOR Identifier 不为空，则添加额外信息
                rounded_distance_nm = int(round(distance_nm)) # 四舍五入距离
                magnetic_bearing_int = int(magnetic_bearing) # 磁航向取整
                output += f" {operation_code} {vor_identifier}{magnetic_bearing_int:03d}{rounded_distance_nm:03d}" # 添加 VOR info, 格式化距离为三位数，前导0, 磁航向格式化为三位数
            else:
                 output += f" {operation_code}" # 否则只添加 operation code, although this line is likely unreachable when vor_identifier is used

        else:  # FIX
            lat, lon, fix_code, usage_code, runway_code, airport_code, operation_code = result
            output = (
                f"{lat:.9f} {lon:.9f} {usage_code}{fix_code}{int(runway_code):02d} "
                f"{airport_code} {airport_code[:2]} {operation_code}"
            )
        self.output_entry.delete(1.0, tk.END)
        self.output_entry.insert(tk.END, output)

    def on_calculate_waypoint(self):
        """
        计算 WAYPOINT 坐标并输出
        """
        params = self.validate_input("WAYPOINT")
        if params is None:
            return

        lat_vor, lon_vor, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier = params # 获取 vor_identifier
        try:
            lat_target, lon_target = self.calculate_target_coords_vincenty(
                lat_vor, lon_vor, magnetic_bearing, distance_nm, declination
            )
            radius_letter = get_radius_letter(distance_nm)
            operation_code_map = {
                "离场": "4464713",
                "进场": "4530249",
                "进近": "4595785"
            }
            operation_code = operation_code_map.get(self.combo_operation_type.get(), "")
            result = (
                round(lat_target, 9),
                round(lon_target, 9),
                radius_letter,
                airport_code,
                operation_code
            )
            self.process_output(
                result,
                "WAYPOINT",
                vor_identifier, # 传递 vor_identifier
                magnetic_bearing, # 传递 magnetic_bearing
                distance_nm # 传递 distance_nm
            )
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中发生错误：{str(e)}")

    def on_calculate_fix(self):
        """
        计算 FIX 坐标并输出
        """
        params = self.validate_input("FIX")
        if params is None:
            return

        lat, lon, fix_type, fix_usage, runway_code, airport_code = params
        try:
            fix_code_map = {
                "VORDME": "D", "VOR": "V", "NDBDME": "Q", "NDB": "N",
                "ILS": "I", "RNP": "R"
            }
            usage_code_map = {
                "Final approach fix": "F",
                "Initial approach fix": "A",
                "Intermediate approach fix": "I",
                "Final approach course fix": "C",
                "Missed approach point fix": "M"
            }
            operation_code_map = {
                "离场": "4464713",
                "进场": "4530249",
                "进近": "4595785"
            }

            fix_code = fix_code_map.get(fix_type, "")
            usage_code = usage_code_map.get(fix_usage, "")
            if not fix_code or not usage_code:
                raise ValueError("无效的 FIX 类型或使用")

            operation_code = operation_code_map.get(self.combo_fix_operation_type.get(), "")
            result = (
                round(lat, 9),
                round(lon, 9),
                fix_code,
                usage_code,
                runway_code,
                airport_code,
                operation_code
            )
            self.process_output(result, "FIX")
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中发生错误：{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CoordinateCalculatorApp(root)
    root.mainloop()
