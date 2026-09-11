import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error


# Set global appearance and color theme
ctk.set_appearance_mode("Dark")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"


class DatabaseManager:
    """Handles all database operations using MySQL."""

    def __init__(self, host="127.0.0.1", port=3306, user="YourUser", password="YourPassword", database="todolist"): #CHANGE THE USER AND PASSWORD THAT YOU HAVE FOR SQL
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database
        }
        self.conn = None
        self.cursor = None
        self.connect()
        self.init_db()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.cursor = self.conn.cursor()
        except Error as e:
            print(f"Database connection error: {e}")

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.cursor = self.conn.cursor()
        except Error as e:
            print(f"Database connection error: {e}")

    def init_db(self):
        if not self.conn or not self.cursor:
            return
        try:
            create_list_tbl = """
            CREATE TABLE IF NOT EXISTS todo_list (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                task VARCHAR(255) NOT NULL, 
                priority VARCHAR(50) DEFAULT 'Medium',
                status VARCHAR(50) DEFAULT 'Pending', 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                due_date VARCHAR(50)
            )"""
            self.cursor.execute(create_list_tbl)

            # Auto-migrate existing tables that lack the priority column
            try:
                self.cursor.execute("ALTER TABLE todo_list ADD COLUMN priority VARCHAR(50) DEFAULT 'Medium' AFTER task")
            except Error:
                pass  # Column already exists

            self.conn.commit()
        except Error as e:
            print(f"Database initialization error: {e}")

    def fetch_all_tasks(self, filter_status="All"):
        if not self.conn or not self.conn.is_connected():
            return []
        try:
            if filter_status == "All":
                self.cursor.execute("SELECT id, task, priority, status, due_date FROM todo_list ORDER BY id DESC")
            else:
                self.cursor.execute("SELECT id, task, priority, status, due_date FROM todo_list WHERE status = %s ORDER BY id DESC", (filter_status,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Fetch error: {e}")
            return []

    def add_task(self, task, priority, due_date):
        try:
            query = "INSERT INTO todo_list (task, priority, status, due_date) VALUES (%s, %s, %s, %s)"
            self.cursor.execute(query, (task, priority, "Pending", due_date))
            self.conn.commit()
            return True
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to add task: {e}")
            return False

    def update_status(self, task_id, new_status):
        try:
            query = "UPDATE todo_list SET status = %s WHERE id = %s"
            self.cursor.execute(query, (new_status, task_id))
            self.conn.commit()
            return True
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to update task: {e}")
            return False

    def delete_task(self, task_id):
        try:
            query = "DELETE FROM todo_list WHERE id = %s"
            self.cursor.execute(query, (task_id,))
            self.conn.commit()
            return True
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to delete task: {e}")
            return False

    def get_stats(self):
        if not self.conn or not self.conn.is_connected():
            return 0, 0, 0
        try:
            self.cursor.execute("SELECT COUNT(*) FROM todo_list")
            total = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM todo_list WHERE status = 'Pending'")
            pending = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM todo_list WHERE status = 'Completed'")
            completed = self.cursor.fetchone()[0]

            return total, pending, completed
        except Error:
            return 0, 0, 0

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()


class ModernTodoApp(ctk.CTk):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager

        self.title("ApexTask — Modern Workspace")
        self.geometry("980x680")
        self.minsize(900, 600)

        # Configure Main Grid Layout (Left Sidebar + Right Content Area)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_panel()
        self.refresh_dashboard()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_sidebar(self):
        """Constructs the navigation and creation panel on the left."""
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # App Logo / Title
        logo_label = ctk.CTkLabel(self.sidebar_frame, text="⚡ ApexTask", font=ctk.CTkFont(size=22, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        subtitle = ctk.CTkLabel(self.sidebar_frame, text="Task Management Dashboard", font=ctk.CTkFont(size=11), text_color="gray")
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Section Header
        lbl_add = ctk.CTkLabel(self.sidebar_frame, text="CREATE NEW TASK", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        lbl_add.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        # Task Name Field
        self.entry_task = ctk.CTkEntry(self.sidebar_frame, placeholder_text="What needs to be done?", width=240, height=35)
        self.entry_task.grid(row=3, column=0, padx=20, pady=8)

        # Priority Selection
        self.priority_option = ctk.CTkOptionMenu(
            self.sidebar_frame, 
            values=["Low Priority", "Medium Priority", "High Priority"],
            width=240,
            height=35
        )
        self.priority_option.set("Medium Priority")
        self.priority_option.grid(row=4, column=0, padx=20, pady=8)

        # Due Date Input Field
        self.entry_due_date = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Due Date (e.g. YYYY-MM-DD)", width=240, height=35)
        self.entry_due_date.grid(row=5, column=0, padx=20, pady=8)

        # Create Task Button
        btn_add = ctk.CTkButton(
            self.sidebar_frame, 
            text="+ Add Task", 
            command=self.on_add_task, 
            fg_color="#1f6aa5", 
            hover_color="#144870",
            font=ctk.CTkFont(weight="bold"),
            height=38,
            width=240
        )
        btn_add.grid(row=6, column=0, padx=20, pady=(12, 20))

        # Theme Switcher (Bottom of Sidebar)
        self.theme_switch = ctk.CTkSwitch(
            self.sidebar_frame, 
            text="Dark Mode", 
            command=self.toggle_theme,
            onvalue="Dark", 
            offvalue="Light"
        )
        self.theme_switch.select()
        self.theme_switch.grid(row=9, column=0, padx=20, pady=20, sticky="s")

    def _build_main_panel(self):
        """Constructs the right dashboard container with statistics and scrollable list."""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Top Metric Cards Frame
        self.stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Stat Card 1: Total
        self.card_total = self._create_metric_card(self.stats_frame, "Total Tasks", "0", 0)
        # Stat Card 2: Pending
        self.card_pending = self._create_metric_card(self.stats_frame, "Pending", "0", 1, accent_color="#e67e22")
        # Stat Card 3: Completed
        self.card_completed = self._create_metric_card(self.stats_frame, "Completed", "0", 2, accent_color="#2ecc71")

        # Task List Header & Filter Bar
        self.filter_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.filter_frame.grid_columnconfigure(0, weight=1)

        lbl_list_title = ctk.CTkLabel(self.filter_frame, text="Your Workspace", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_list_title.grid(row=0, column=0, sticky="w")

        self.filter_segment = ctk.CTkSegmentedButton(
            self.filter_frame, 
            values=["All", "Pending", "Completed"],
            command=lambda val: self.load_tasks(filter_status=val)
        )
        self.filter_segment.set("All")
        self.filter_segment.grid(row=0, column=1, sticky="e")

        # Scrollable Task Container
        self.scroll_tasks = ctk.CTkScrollableFrame(self.main_frame, label_text="Task Queue")
        self.scroll_tasks.grid(row=2, column=0, sticky="nsew")
        self.scroll_tasks.grid_columnconfigure(0, weight=1)

    def _create_metric_card(self, parent, title, value, column, accent_color=None):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=0, column=column, padx=6, sticky="ew")
        
        lbl_val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=26, weight="bold"), text_color=accent_color)
        lbl_val.pack(padx=15, pady=(12, 0))

        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color="gray")
        lbl_title.pack(padx=15, pady=(0, 12))

        return lbl_val

    def refresh_dashboard(self):
        """Refreshes both top metric counters and task records."""
        total, pending, completed = self.db.get_stats()
        self.card_total.configure(text=str(total))
        self.card_pending.configure(text=str(pending))
        self.card_completed.configure(text=str(completed))

        current_filter = self.filter_segment.get()
        self.load_tasks(filter_status=current_filter)

    def load_tasks(self, filter_status="All"):
        """Populates scrollable frame with card-style task records."""
        for widget in self.scroll_tasks.winfo_children():
            widget.destroy()

        tasks = self.db.fetch_all_tasks(filter_status)

        if not tasks:
            empty_lbl = ctk.CTkLabel(
                self.scroll_tasks, 
                text="🎉 No tasks found here!", 
                font=ctk.CTkFont(size=14), 
                text_color="gray"
            )
            empty_lbl.pack(pady=40)
            return

        for task_data in tasks:
            task_id, title, priority, status, due_date = task_data
            self._render_task_card(task_id, title, priority, status, due_date)

    def _render_task_card(self, task_id, title, priority, status, due_date):
        """Creates an individual task row card widget."""
        card = ctk.CTkFrame(self.scroll_tasks, corner_radius=8)
        card.pack(fill="x", padx=5, pady=4)
        card.grid_columnconfigure(1, weight=1)

        # Priority Color Badge
        p_colors = {"High Priority": "#e74c3c", "Medium Priority": "#f39c12", "Low Priority": "#3498db"}
        p_color = p_colors.get(priority, "gray")

        p_badge = ctk.CTkLabel(
            card, text=f"  {priority.replace(' Priority', '')}  ", 
            font=ctk.CTkFont(size=10, weight="bold"), 
            fg_color=p_color, 
            text_color="white", 
            corner_radius=4
        )
        p_badge.grid(row=0, column=0, padx=(12, 8), pady=12)

        # Task Title (Strike-through effect visually if completed)
        display_title = f"<s>{title}</s>" if status == "Completed" else title
        lbl_title = ctk.CTkLabel(
            card, text=title, 
            font=ctk.CTkFont(size=13, weight="normal" if status == "Pending" else "bold"),
            text_color="gray" if status == "Completed" else None,
            anchor="w"
        )
        lbl_title.grid(row=0, column=1, sticky="w", padx=5)

        # Due Date Label
        if due_date:
            lbl_due = ctk.CTkLabel(card, text=f"📅 {due_date}", font=ctk.CTkFont(size=11), text_color="gray")
            lbl_due.grid(row=0, column=2, padx=10)

        # Action Buttons Container
        btn_container = ctk.CTkFrame(card, fg_color="transparent")
        btn_container.grid(row=0, column=3, padx=10)

        # Status Toggle Button
        toggle_text = "Undo" if status == "Completed" else "Done"
        btn_toggle = ctk.CTkButton(
            btn_container, 
            text=toggle_text, 
            width=60, 
            height=26,
            fg_color="#2ecc71" if status == "Pending" else "#7f8c8d",
            hover_color="#27ae60" if status == "Pending" else "#95a5a6",
            command=lambda: self.on_toggle_status(task_id, status)
        )
        btn_toggle.pack(side="left", padx=3)

        # Delete Button
        btn_delete = ctk.CTkButton(
            btn_container, 
            text="Delete", 
            width=60, 
            height=26,
            fg_color="#e74c3c", 
            hover_color="#c0392b",
            command=lambda: self.on_delete_task(task_id, title)
        )
        btn_delete.pack(side="left", padx=3)

    def on_add_task(self):
        title = self.entry_task.get().strip()
        priority = self.priority_option.get()
        due_date = self.entry_due_date.get().strip()

        if not title:
            messagebox.showwarning("Validation Warning", "Task title cannot be empty.")
            return

        if self.db.add_task(title, priority, due_date if due_date else "No Date"):
            self.entry_task.delete(0, "end")
            self.entry_due_date.delete(0, "end")
            self.refresh_dashboard()

    def on_toggle_status(self, task_id, current_status):
        new_status = "Completed" if current_status == "Pending" else "Pending"
        if self.db.update_status(task_id, new_status):
            self.refresh_dashboard()

    def on_delete_task(self, task_id, title):
        if messagebox.askyesno("Confirm Delete", f"Delete task '{title}'?"):
            if self.db.delete_task(task_id):
                self.refresh_dashboard()

    def toggle_theme(self):
        mode = self.theme_switch.get()
        ctk.set_appearance_mode(mode)

    def on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    db = DatabaseManager()
    app = ModernTodoApp(db)
    app.mainloop()
