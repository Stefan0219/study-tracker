import json
import time
import datetime
import os
import sys
import random
import threading
import matplotlib.pyplot as plt

# --- 配置 ---
DATA_DIR = "data"
CHART_DIR = "charts"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
LOG_FILE = os.path.join(DATA_DIR, "study_log.json")

# 为终端输出添加颜色和Emoji
class TColors:
    HEADER = '\033[95m'; OKBLUE = '\033[94m'; OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'; WARNING = '\033[93m'; FAIL = '\033[91m'
    ENDC = '\033[0m'; BOLD = '\033[1m'; UNDERLINE = '\033[4m'
POSITIVE_COLORS = [TColors.OKGREEN, TColors.OKCYAN, TColors.WARNING, TColors.OKBLUE, TColors.HEADER]

ENCOURAGEMENTS = [
    "太棒了！又完成了一个阶段，继续保持！🚀", "非常出色！你的努力正在转化为实力。💪",
    "难以置信的进度！休息一下，准备迎接下一个挑战。🎉", "你做得很好！离目标又近了一大步。🎯",
    "坚持就是胜利！你的毅力令人敬佩。💖", "又攻克了一个难关！你比想象中更强大。🌟",
    "这个节奏非常棒，继续加油！🏆"
]
GOAL_COMPLETED_MESSAGES = [
    "你太棒了，简直势不可挡！🎉🎉🎉",
    "恭喜！你已经完成了今天这个科目的所有目标！🥳",
    "任务完成！卓越的表现，为你感到骄傲！✨",
    "完美收官！你已经征服了今天的目标。💯"
]
# --- 结束配置 ---

def load_config():
    """从简化的JSON加载配置，并向后兼容旧格式"""
    if not os.path.exists(CONFIG_FILE):
        print(f"{TColors.WARNING}未找到配置文件，正在创建默认配置...{TColors.ENDC}")
        default_config = {"default_goals": {"math": 50, "english": 40, "politics": 20, "cs408": 10}}
        save_data(default_config, CONFIG_FILE)
        print(f"默认配置文件已创建于: {CONFIG_FILE}\n您可以修改此文件来自定义您的学习科目和每日目标。")
        config_data = default_config
    else:
        config_data = load_data(CONFIG_FILE)
        if "default_goals" not in config_data:
            print(f"{TColors.WARNING}检测到旧版配置文件，正在自动转换为新格式...{TColors.ENDC}")
            new_goals = {}
            if "subjects" in config_data and "default_goals" in config_data:
                for key in config_data["subjects"]: new_goals[key] = config_data["default_goals"].get(key, 0)
            else: new_goals = config_data
            new_config_data = {"default_goals": new_goals}
            os.rename(CONFIG_FILE, CONFIG_FILE + ".bak")
            save_data(new_config_data, CONFIG_FILE)
            print(f"转换完成！旧配置文件已备份为 {CONFIG_FILE}.bak")
            config_data = new_config_data
    subject_goal_map = config_data.get("default_goals", {})
    subjects = {key: key for key in subject_goal_map.keys()}
    default_goals = subject_goal_map
    if not subjects:
        print(f"{TColors.FAIL}错误: 配置文件 {CONFIG_FILE} 中 'default_goals' 为空或不存在。{TColors.ENDC}"); sys.exit(1)
    return subjects, default_goals

class RestReminder(threading.Thread):
    def __init__(self):
        super().__init__(); self.daemon = True; self.stop_event = threading.Event()
    def run(self):
        while not self.stop_event.is_set():
            if self.stop_event.wait(50 * 60): break
            print(f"\n{TColors.HEADER}{TColors.BOLD}☕ 休息时间到！ ☕{TColors.ENDC}")
            print(f"{TColors.HEADER}已专注50分钟，建议休息5分钟，活动一下吧！{TColors.ENDC}")
            print(f"{TColors.BOLD}主菜单 >{TColors.ENDC} ", end="", flush=True)
            if self.stop_event.wait(5 * 60): break
    def stop(self): self.stop_event.set()

# --- 核心功能函数 ---
def format_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"
def load_data(file_path):
    if not os.path.exists(file_path): return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(); return json.loads(content) if content else {}
    except (json.JSONDecodeError, FileNotFoundError): return {}
def save_data(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
def display_status(date_title, daily_data, current_session_elapsed=0):
    total_seconds = daily_data.get('total_study_seconds', 0) + current_session_elapsed
    subjects_data = daily_data.get('subjects', {})
    print(f"\n--- {TColors.BOLD}{date_title} 的学习状态{TColors.ENDC} ---")
    print(f"⏱️  总学习时长: {TColors.OKGREEN}{format_time(total_seconds)}{TColors.ENDC}")
    print("-"*35)
    if not subjects_data: print("没有找到该日的科目数据。")
    else:
        print("📊 各科做题进度:")
        for key in SUBJECTS:
            data = subjects_data.get(key, {})
            solved = data.get("solved", 0); goal = data.get("goal", 0)
            time_spent = data.get("time_seconds", 0)
            time_str = f" ({format_time(time_spent)})" if time_spent > 0 else ""
            if goal > 0: print(f"  - {key}: {TColors.BOLD}{solved}/{goal}{TColors.ENDC}{time_str}")
            else: print(f"  - {key}: {TColors.BOLD}{solved}{TColors.ENDC}{time_str}")
    print("="*35)
def display_help():
    print("\n--- 💡 命令帮助 ---")
    print(f"  {TColors.OKCYAN}start <科目>{TColors.ENDC}           - 开始学习并进入专注模式")
    print(f"  {TColors.OKCYAN}stop{TColors.ENDC}                   - 结束本次学习会话")
    print(f"  {TColors.OKCYAN}status [y|YYYY-MM-DD]{TColors.ENDC}  - 查看状态 (y:昨天)")
    print(f"  {TColors.OKCYAN}chart <type> [p]{TColors.ENDC}       - 生成图表 (type: count|time, p: t|w|m)")
    print(f"  {TColors.OKCYAN}goal <科目> <数>{TColors.ENDC}       - 设置科目目标")
    print(f"  {TColors.OKCYAN}help{TColors.ENDC}                   - 显示此帮助信息")
    print(f"  {TColors.OKCYAN}quit{TColors.ENDC}                   - 保存并退出程序")
    print(f"\n  {TColors.BOLD}可用科目: {', '.join(SUBJECTS.keys())}{TColors.ENDC}")
def check_milestones(subject_data):
    goal = subject_data.get('goal', 0)
    if goal <= 0: return
    solved = subject_data.get('solved', 0)
    milestones_achieved = subject_data.get('milestones_achieved', [])
    progress_percent = (solved / goal) * 100
    # 如果已完成或超过目标，则不再显示里程碑鼓励
    if progress_percent >= 100: return
    milestone_track = [30, 60, 90] if goal * 0.2 <= 10 else [20, 40, 60, 80]
    for milestone in milestone_track:
        if progress_percent >= milestone and milestone not in milestones_achieved:
            color = random.choice(POSITIVE_COLORS)
            message = random.choice(ENCOURAGEMENTS)
            print(f"\n{color}{TColors.BOLD}✨ 里程碑达成 ({milestone}%)! {message}{TColors.ENDC}")
            print(f"{TColors.BOLD}主菜单 >{TColors.ENDC} ", end="", flush=True)
            subject_data['milestones_achieved'].append(milestone)
            break
def focus_mode(subject_key, today_data, all_data, session_start_time):
    subject_name = SUBJECTS[subject_key]
    subject_data = today_data["subjects"][subject_key]
    print(f"\n{TColors.HEADER}已进入 [{subject_name}] 专注模式 (输入 'back' 或 'b' 返回)。{TColors.ENDC}")
    focus_start_time = last_problem_time = time.time()
    problem_count_in_session = 0
    try:
        while True:
            cmd = input(f"[{subject_name}] > ").strip().lower()
            if cmd in ["back", "b"]: break
            elif cmd == "":
                problem_end_time = time.time(); time_taken = problem_end_time - last_problem_time
                subject_data["solved"] += 1; problem_count_in_session += 1
                solved = subject_data['solved']; goal = subject_data['goal']
                print(f"  -> ✅ 第 {solved} 题完成, 用时: {format_time(time_taken)}. ", end="")
                if goal > 0: print(f"进度: {solved}/{goal}")
                else: print()
                last_problem_time = problem_end_time
                # 检查是否达成目标或里程碑
                if goal > 0 and solved == goal:
                    color = random.choice(POSITIVE_COLORS)
                    message = random.choice(GOAL_COMPLETED_MESSAGES)
                    print(f"\n{color}{TColors.BOLD}🏆 目标完成! {message}{TColors.ENDC}")
                    print(f"[{subject_name}] > ", end="", flush=True)
                else:
                    check_milestones(subject_data)
            else: print("  无效输入。")
    finally:
        focus_elapsed_time = time.time() - focus_start_time
        subject_data['time_seconds'] += focus_elapsed_time
        save_data(all_data, LOG_FILE)
        print(f"已退出 [{subject_name}] 专注模式。本次专注时长: {format_time(focus_elapsed_time)}，完成 {problem_count_in_session} 题。")

# --- 主程序 ---
def main():
    global SUBJECTS
    os.makedirs(DATA_DIR, exist_ok=True); os.makedirs(CHART_DIR, exist_ok=True)
    SUBJECTS, DEFAULT_GOALS = load_config()
    all_data = load_data(LOG_FILE)
    today_str = str(datetime.date.today())

    if today_str not in all_data:
        all_data[today_str] = {"total_study_seconds": 0, "subjects": {}}
    for key in SUBJECTS:
        if key not in all_data[today_str]["subjects"]:
            all_data[today_str]["subjects"][key] = {
                "solved": 0, "goal": DEFAULT_GOALS.get(key, 0), 
                "time_seconds": 0, "milestones_achieved": []
            }
    today_data = all_data[today_str]
    is_studying = False; session_start_time = 0; reminder_thread = None

    print(f"--- {TColors.BOLD}学习追踪器 (完全体){TColors.ENDC} ---")
    display_status("今天", today_data)
    display_help()

    try:
        while True:
            parts = input(f"\n{TColors.BOLD}主菜单 >{TColors.ENDC} ").strip().lower().split()
            if not parts: continue
            command = parts[0]
            
            if command == "start":
                if len(parts) != 2 or parts[1] not in SUBJECTS: print(f"{TColors.FAIL}命令格式错误或科目不存在。{TColors.ENDC}")
                else:
                    if not is_studying:
                        is_studying = True; session_start_time = time.time()
                        print(f"{TColors.OKGREEN}学习会话开始，总计时启动！{TColors.ENDC}")
                        reminder_thread = RestReminder(); reminder_thread.start()
                    focus_mode(parts[1], today_data, all_data, session_start_time)
                    display_status("今天", today_data, time.time() - session_start_time if is_studying else 0)
            elif command == "stop":
                if not is_studying: print(f"{TColors.FAIL}错误：学习会话尚未启动。{TColors.ENDC}")
                else:
                    elapsed = time.time() - session_start_time
                    today_data["total_study_seconds"] += elapsed
                    is_studying = False
                    if reminder_thread: reminder_thread.stop(); reminder_thread = None
                    save_data(all_data, LOG_FILE)
                    print(f"{TColors.OKGREEN}学习会话结束，本轮时长: {format_time(elapsed)}{TColors.ENDC}")
                    display_status("今天", today_data)
            elif command == "quit":
                if is_studying:
                    elapsed = time.time() - session_start_time
                    today_data["total_study_seconds"] += elapsed
                    if reminder_thread: reminder_thread.stop()
                    save_data(all_data, LOG_FILE)
                    print(f"\n程序退出前，已自动保存本轮学习时长: {format_time(elapsed)}")
                print("再见！"); break
            elif command == "status":
                target_date_str = today_str; date_title = "今天"
                if len(parts) > 1:
                    arg = parts[1]
                    if arg in ['y', 'yes', 'yesterday']:
                        target_date_str = str(datetime.date.today() - datetime.timedelta(days=1))
                        date_title = f"{target_date_str} (昨天)"
                    else:
                        try:
                            datetime.datetime.strptime(arg, '%Y-%m-%d'); target_date_str = arg; date_title = arg
                        except ValueError: print(f"{TColors.FAIL}无效的日期格式: '{arg}'。{TColors.ENDC}"); continue
                if target_date_str in all_data:
                    display_status(date_title, all_data[target_date_str], time.time() - session_start_time if (target_date_str == today_str and is_studying) else 0)
                else: print(f"{TColors.WARNING}找不到日期 {target_date_str} 的记录。{TColors.ENDC}")
            elif command == "chart":
                chart_type = 'count'; period_arg = 't'
                title_prefix_map = {'count': '做题数量', 'time': '花费时间'}; period_map = {'t': '今日', 'w': '本周', 'm': '本月'}
                if len(parts) > 1:
                    if parts[1] in ['count', 'time']: chart_type = parts[1]; period_arg = (parts[2][0] if len(parts) > 2 else 't')
                    else: period_arg = parts[1][0]
                if period_arg not in period_map: print(f"{TColors.FAIL}无效的图表周期。{TColors.ENDC}"); continue
                period_name = period_map[period_arg]; title = f"{period_name}{title_prefix_map[chart_type]}分布"
                filename = os.path.join(CHART_DIR, f"study_chart_{chart_type}_{period_name}_{today_str}.png")
                data = today_data['subjects'] if period_arg == 't' else aggregate_data_for_period(all_data, {'w': 'week', 'm': 'month'}[period_arg])
                generate_pie_chart(data, chart_type, title, filename)
            elif command == "goal":
                if len(parts) != 3 or parts[1] not in SUBJECTS or not parts[2].isdigit(): print(f"{TColors.FAIL}命令格式错误或科目不存在。{TColors.ENDC}")
                else:
                    today_data["subjects"][parts[1]]["goal"] = int(parts[2])
                    today_data["subjects"][parts[1]]["milestones_achieved"] = []
                    save_data(all_data, LOG_FILE)
                    print(f"{TColors.OKGREEN}已设置 [{SUBJECTS[parts[1]]}] 的目标为: {parts[2]}，里程碑已重置。{TColors.ENDC}")
            elif command == "help": display_help()
            else: print(f"{TColors.FAIL}无效命令，请输入 'help' 查看帮助。{TColors.ENDC}")
    except KeyboardInterrupt:
        if is_studying:
            elapsed = time.time() - session_start_time
            today_data["total_study_seconds"] += elapsed
            if reminder_thread: reminder_thread.stop()
            save_data(all_data, LOG_FILE)
            print(f"\n检测到中断，已自动保存本轮学习时长: {format_time(elapsed)}")
        print("\n程序已退出."); sys.exit(0)

def aggregate_data_for_period(all_data, period):
    agg = {key: {'solved': 0, 'time_seconds': 0} for key in SUBJECTS}
    today = datetime.date.today(); start_date = today
    if period == 'week': start_date = today - datetime.timedelta(days=today.weekday())
    elif period == 'month': start_date = today.replace(day=1)
    for date_str, daily_data in all_data.items():
        try:
            current_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            if start_date <= current_date <= today and 'subjects' in daily_data:
                for s_key, s_data in daily_data['subjects'].items():
                    if s_key in agg:
                        agg[s_key]['solved'] += s_data.get('solved', 0); agg[s_key]['time_seconds'] += s_data.get('time_seconds', 0)
        except (ValueError, KeyError): continue
    return agg
def generate_pie_chart(subjects_data, chart_type, title, filename):
    labels, sizes = [], []
    data_key = 'time_seconds' if chart_type == 'time' else 'solved'
    for key, data in subjects_data.items():
        value = data.get(data_key, 0)
        if value > 0:
            label = SUBJECTS.get(key, key)
            if chart_type == 'time': label += f"\n({format_time(value)})"
            sizes.append(value); labels.append(label)
    if not sizes:
        print(f"{TColors.WARNING}在指定时间范围内没有可供分析的数据。{TColors.ENDC}"); return
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Heiti TC', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(sizes, autopct='%1.1f%%', startangle=140, wedgeprops={'edgecolor': 'white', 'linewidth': 1})
    ax.axis('equal'); ax.set_title(title, pad=20, fontsize=16)
    ax.legend(wedges, labels, title="科目", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    plt.setp(autotexts, size=10, weight="bold", color="white")
    plt.tight_layout(); plt.savefig(filename); plt.close(fig)
    print(f"图表已成功保存为: {filename}")

if __name__ == "__main__":
    main()
