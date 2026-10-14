"""Запуск графической лабораторной работы № 5 (Python + tkinter)."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.lsystem import load_system, expand, trace, fit_segments
from src.midpoint import generate
from src.bezier import sample

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / 'examples'
BG = '#f5f7fb'


class GraphicsLab(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Лабораторная № 5 — Компьютерная графика')
        self.geometry('1150x780')
        self.minsize(850, 580)
        self.configure(bg=BG)
        tabs = ttk.Notebook(self)
        tabs.pack(fill='both', expand=True, padx=12, pady=12)
        self.lsystem_tab(tabs)
        self.mountain_tab(tabs)
        self.bezier_tab(tabs)

    def canvas(self, parent):
        c = tk.Canvas(parent, bg='white', highlightthickness=1, highlightbackground='#d4dce8')
        c.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        return c

    def error(self, func):
        try:
            func()
        except (ValueError, OSError) as exc:
            messagebox.showerror('Ошибка', str(exc))

    def lsystem_tab(self, tabs):
        page = ttk.Frame(tabs)
        tabs.add(page, text='1. L-системы и дерево')
        controls = ttk.Frame(page)
        controls.pack(fill='x', padx=10, pady=10)
        files = sorted(EXAMPLES.glob('*.txt'))
        self.systems = {p.stem: p for p in files}
        self.chosen = tk.StringVar(value='tree' if 'tree' in self.systems else next(iter(self.systems)))
        ttk.Label(controls, text='Пример:').pack(side='left')
        menu = ttk.Combobox(controls, textvariable=self.chosen,
                            values=list(self.systems), state='readonly', width=18)
        menu.pack(side='left', padx=5)
        ttk.Button(controls, text='Открыть .txt', command=self.open_lsystem).pack(side='left', padx=4)
        self.iterations = tk.IntVar(value=6)
        self.jitter = tk.DoubleVar(value=0)
        self.seed_l = tk.IntVar(value=42)
        self.tree_style = tk.BooleanVar(value=self.chosen.get() in ('tree', 'stochastic_tree'))
        self.draw_symbols = tk.StringVar(value=load_system(self.systems[self.chosen.get()]).draw_symbols)
        for label, var, width in [('Итерации', self.iterations, 4),
                                   ('Случайный угол ±°', self.jitter, 5),
                                   ('Seed', self.seed_l, 6)]:
            ttk.Label(controls, text=label).pack(side='left', padx=(9, 2))
            ttk.Entry(controls, textvariable=var, width=width).pack(side='left')
        ttk.Label(controls, text='Рисующие:').pack(side='left', padx=(9, 2))
        ttk.Entry(controls, textvariable=self.draw_symbols, width=5).pack(side='left')
        ttk.Checkbutton(controls, text='Цвет и толщина дерева', variable=self.tree_style).pack(side='left', padx=10)
        ttk.Button(controls, text='Построить', command=lambda: self.error(self.draw_lsystem)).pack(side='left')
        self.linfo = ttk.Label(page, text='Рисующие символы задаются в поле или # draw: AB; f — движение, +/- — поворот, [] — ветвление')
        self.linfo.pack(anchor='w', padx=12, pady=(0, 6))
        self.lcanvas = self.canvas(page)
        self.lcanvas.bind('<Configure>', lambda _: self.error(self.draw_lsystem))
        menu.bind('<<ComboboxSelected>>', lambda _: self.error(self.select_lsystem))

    def select_lsystem(self):
        system = load_system(self.systems[self.chosen.get()])
        self.draw_symbols.set(system.draw_symbols)
        self.tree_style.set(self.chosen.get() in ('tree', 'stochastic_tree'))
        self.draw_lsystem()

    def open_lsystem(self):
        path = filedialog.askopenfilename(filetypes=[('L-системы', '*.txt'), ('Все файлы', '*.*')])
        if path:
            name = Path(path).stem
            self.systems[name] = Path(path)
            self.chosen.set(name)
            self.error(self.select_lsystem)

    def draw_lsystem(self):
        path = self.systems[self.chosen.get()]
        system = load_system(path)
        instructions = expand(system, self.iterations.get(), self.seed_l.get())
        parts = trace(instructions, system.angle, system.direction,
                      self.jitter.get(), self.seed_l.get(), self.draw_symbols.get())
        c = self.lcanvas
        width, height = max(c.winfo_width(), 200), max(c.winfo_height(), 200)
        c.delete('all')
        fitted = fit_segments(parts, width, height, 35)
        max_depth = max((s.depth for s in fitted), default=0)
        for s in fitted:
            if self.tree_style.get():
                t = min(s.depth / max(max_depth, 1), 1)
                color = f'#{int(110-60*t):02x}{int(72+80*t):02x}{int(42+18*t):02x}'
                thickness = max(1.0, 6 * (0.72**s.depth))
            else:
                color, thickness = '#205a86', 1.5
            c.create_line(s.x1, s.y1, s.x2, s.y2, fill=color,
                          width=thickness, capstyle='round')
        self.linfo.config(text=f'{path.name}  |  символов: {len(instructions)}  |  отрезков: {len(fitted)}'
                               f'  |  рисующие: {self.draw_symbols.get()}, [] — ветвление')

    def mountain_tab(self, tabs):
        page = ttk.Frame(tabs)
        tabs.add(page, text='2. Горный массив')
        tools = ttk.Frame(page)
        tools.pack(fill='x', padx=10, pady=10)
        self.m_steps = tk.IntVar(value=8)
        self.m_amplitude = tk.DoubleVar(value=0.32)
        self.m_roughness = tk.DoubleVar(value=0.56)
        self.m_seed = tk.IntVar(value=42)
        self.m_left = tk.DoubleVar(value=0.30)
        self.m_right = tk.DoubleVar(value=0.35)
        for label, var, size in [('Шаги', self.m_steps, 4), ('Амплитуда', self.m_amplitude, 6),
                                  ('Затухание', self.m_roughness, 6), ('Seed', self.m_seed, 6),
                                  ('Слева', self.m_left, 5), ('Справа', self.m_right, 5)]:
            ttk.Label(tools, text=label).pack(side='left', padx=(7, 2))
            ttk.Entry(tools, textvariable=var, width=size).pack(side='left')
        ttk.Button(tools, text='Генерировать', command=lambda: self.error(self.reset_mountain)).pack(side='left', padx=9)
        stepsrow = ttk.Frame(page)
        stepsrow.pack(fill='x', padx=12)
        ttk.Label(stepsrow, text='Показать шаг:').pack(side='left')
        self.m_stage = tk.IntVar(value=8)
        self.stage_slider = ttk.Scale(stepsrow, from_=0, to=8, orient='horizontal',
                                      command=self.on_mountain_slider)
        self.stage_slider.pack(side='left', fill='x', expand=True, padx=12)
        self.stage_slider.set(8)
        self.m_label = ttk.Label(stepsrow, text='Шаг 8')
        self.m_label.pack(side='left')
        self.m_canvas = self.canvas(page)
        self.m_canvas.bind('<Configure>', lambda _: self.draw_mountain())
        self.history = generate(self.m_steps.get(), self.m_amplitude.get(),
                                self.m_roughness.get(), self.m_seed.get(),
                                self.m_left.get(), self.m_right.get())

    def reset_mountain(self):
        self.history = generate(self.m_steps.get(), self.m_amplitude.get(),
                                self.m_roughness.get(), self.m_seed.get(),
                                self.m_left.get(), self.m_right.get())
        self.stage_slider.configure(to=len(self.history)-1)
        self.stage_slider.set(len(self.history)-1)
        self.draw_mountain()

    def on_mountain_slider(self, value):
        self.m_stage.set(round(float(value)))
        self.draw_mountain()

    def draw_mountain(self):
        #если ещё не всё готово к отрисовке, не рисуй
        if not hasattr(self, 'm_canvas') or not hasattr(self, 'history'):
            return
        c = self.m_canvas
        c.delete('all')
        if not hasattr(self, 'history'):
            return
        stage = max(0, min(self.m_stage.get(), len(self.history)-1))
        points = self.history[stage]
        w, h = max(c.winfo_width(), 200), max(c.winfo_height(), 200)
        values = [y for version in self.history for _, y in version]
        min_y, max_y = min(values)-.15, max(values)+.15
        def xy(p):
            return 35+p[0]*(w-70), h-55-(p[1]-min_y)/(max_y-min_y)*(h-100)
        path = [xy(p) for p in points]
        polygon = [35, h-35] + [z for p in path for z in p] + [w-35, h-35]
        c.create_polygon(*polygon, fill='#bac7d2', outline='')
        c.create_line(*[z for p in path for z in p], fill='#365e76', width=2)
        if len(points) <= 129:
            for x, y in path:
                c.create_oval(x-2, y-2, x+2, y+2, fill='#ec8750', outline='')
        c.create_line(20, h-35, w-20, h-35, fill='#a4b3c4')
        self.m_label.configure(text=f'Шаг {stage} / {len(self.history)-1} · {len(points)} точек')

    def bezier_tab(self, tabs):
        page = ttk.Frame(tabs)
        tabs.add(page, text='3. Сплайны Безье')
        actions = ttk.Frame(page)
        actions.pack(fill='x', padx=10, pady=10)
        ttk.Label(actions, text='ЛКМ: добавить точку или перетащить существующую; ПКМ: удалить').pack(side='left')
        ttk.Button(actions, text='Сбросить', command=self.reset_bezier).pack(side='right')
        self.b_canvas = self.canvas(page)
        self.b_points = [(130, 440), (260, 200), (430, 390), (600, 160), (780, 300)]
        self.drag_index = None
        self.b_canvas.bind('<Button-1>', self.start_drag)
        self.b_canvas.bind('<B1-Motion>', self.drag)
        self.b_canvas.bind('<ButtonRelease-1>', lambda _: setattr(self, 'drag_index', None))
        self.b_canvas.bind('<Button-3>', self.delete_point)
        self.b_canvas.bind('<Configure>', lambda _: self.draw_bezier())

    def closest(self, x, y, radius=13):
        for i in range(len(self.b_points)-1, -1, -1):
            px, py = self.b_points[i]
            if (px-x)**2+(py-y)**2 <= radius*radius:
                return i
        return None

    def start_drag(self, event):
        index = self.closest(event.x, event.y)
        if index is None:
            self.b_points.append((event.x, event.y))
            index = len(self.b_points)-1
        self.drag_index = index
        self.draw_bezier()

    def drag(self, event):
        if self.drag_index is not None:
            self.b_points[self.drag_index] = (event.x, event.y)
            self.draw_bezier()

    def delete_point(self, event):
        index = self.closest(event.x, event.y)
        if index is not None:
            del self.b_points[index]
            self.draw_bezier()

    def reset_bezier(self):
        self.b_points = [(130, 440), (260, 200), (430, 390), (600, 160), (780, 300)]
        self.draw_bezier()

    def draw_bezier(self):
        c = self.b_canvas
        c.delete('all')
        if len(self.b_points) >= 2:
            c.create_line(*[v for p in self.b_points for v in p],
                          fill='#b4c0ce', dash=(4, 5), width=1)
            curve = sample(self.b_points)
            c.create_line(*[v for p in curve for v in p], fill='#3565a8', width=3, smooth=False)
        for i, (x, y) in enumerate(self.b_points):
            c.create_oval(x-7, y-7, x+7, y+7, fill='#ed874b', outline='white', width=2)
            c.create_text(x+15, y-13, text=f'P{i}', fill='#556579', font=('Arial', 10))


if __name__ == '__main__':
    GraphicsLab().mainloop()
