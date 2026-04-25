"""
DEDSEC TOOLBOX v9.5
Interface gráfica estilo DedSec / Watch Dogs
By GabrielRj6 e Antigravity
Requer: customtkinter, Pillow
"""

import customtkinter as ctk
import subprocess
import threading
import os
import sys
import time
import random
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageDraw
import tkinter as tk
from tkinter import messagebox
import ctypes
import json
import datetime
import urllib.request
import tempfile

# ── Versão do App ──
APP_VERSION = "10.1"
GITHUB_REPO = "GabrielRj6/DedSecToolBox"
UPDATE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# ── Status de Administrador ──
try:
    IS_ADMIN = ctypes.windll.shell32.IsUserAnAdmin() != 0
except Exception:
    IS_ADMIN = False

# ── Auto-Updater ──
class UpdateChecker:
    @staticmethod
    def check():
        try:
            req = urllib.request.Request(UPDATE_URL, headers={"User-Agent": "DEDSEC-TOOLBOX"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                raw_tag = data.get("tag_name", "").strip()
                # Limpa 'v' ou 'V' do início
                latest = raw_tag.lower().replace("v", "").strip()
                current = APP_VERSION.lower().replace("v", "").strip()
                
                # Só notifica se a versão do GitHub for DIFERENTE e possivelmente MAIOR (comparação simples de string/float)
                if latest and latest != current:
                    try:
                        # Tenta comparar como número para evitar avisar de versões antigas
                        if float(latest) > float(current):
                            assets = data.get("assets", [])
                            download_url = None
                            for asset in assets:
                                if asset.get("name", "").endswith(".exe"):
                                    download_url = asset.get("browser_download_url")
                                    break
                            if download_url:
                                return raw_tag, download_url
                    except:
                        # Se não for número (ex: 10.0.1), volta pra comparação de texto
                        if latest != current:
                             # (Lógica extra: você pode decidir se quer que apareça sempre que for diferente ou só maior)
                             pass 
                return None, None
        except Exception:
            pass
        return None, None

    @staticmethod
    def download_and_install(url, version):
        try:
            tmp_dir = tempfile.mkdtemp()
            exe_path = os.path.join(tmp_dir, f"DEDSEC_TOOLBOX_v{version}.exe")
            messagebox.showinfo("Atualização", f"Baixando versão {version}...")
            urllib.request.urlretrieve(url, exe_path)
            batch_path = os.path.join(tmp_dir, "update.bat")
            exe_current = sys.executable
            
            # Script BAT à prova de balas: tenta deletar o executável atual até o Windows destravar (quando fechar de vez)
            with open(batch_path, "w") as f:
                f.write(f'''@echo off
set _MEIPASS2=
set _MEIPASS=
set _PYI_APPLICATION_HOME_DIR=
set _PYI_ARCHIVE_FILE=
set _PYI_PARENT_PROCESS_LEVEL=
:loop
del "{exe_current}" 2>nul
if exist "{exe_current}" (
    timeout /t 1 /nobreak >nul
    goto loop
)
copy /Y "{exe_path}" "{exe_current}"
del "{exe_path}"
start "" "{exe_current}"
del "%~f0"
''')
            # Também limpamos a env local pra não herdar pro Popen
            clean_env = os.environ.copy()
            for k in list(clean_env.keys()):
                if k.startswith('_MEI') or k.startswith('_PYI'):
                    clean_env.pop(k, None)
            subprocess.Popen(batch_path, shell=True, env=clean_env, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao baixar atualização:\n{e}")
            return False

# ─────────────────────────────────────────────
#  CAMINHO BASE (funciona tanto .py quanto .exe)
# ─────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSETS = os.path.join(BASE_DIR, "assets")

def asset(filename):
    return os.path.join(ASSETS, filename)

# ── Caminhos de Dados Persistentes (Mesma pasta do .exe no pendrive) ──
_EXE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
HISTORY_DB = os.path.join(_EXE_DIR, "dedsec_history.json")
_USER_CFG  = os.path.join(_EXE_DIR, "user.cfg") # Agora o nome do usuário também persiste no pendrive

# ── Gerenciamento de Histórico (Dossiê) ──
class HistoryManager:
    @staticmethod
    def get_hwid():
        """Retorna o ID Único da máquina (BIOS UUID)."""
        try:
            cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_ComputerSystemProduct).UUID"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            hwid = res.stdout.strip()
            return hwid if hwid else "UNKNOWN_DEVICE"
        except: return "UNKNOWN_DEVICE"

    @staticmethod
    def get_system_brief():

        """Coleta resumo técnico da máquina."""
        import platform, socket
        info = {
            "hostname": socket.gethostname(),
            "ip": "Desconectado",
            "os": platform.system() + " " + platform.release(),
            "cpu": "Desconhecido",
            "ram": "Desconhecido"
        }
        try:
            # Tenta pegar IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            try:
                s.connect(('8.8.8.8', 80))
                info["ip"] = s.getsockname()[0]
            except Exception:
                pass
            finally:
                s.close()
        except: pass

        try:
            # CPU via WMIC/CIM
            cmd_cpu = 'powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).Name"'
            r = subprocess.run(cmd_cpu, shell=True, capture_output=True, text=True, timeout=4)
            info["cpu"] = r.stdout.strip() or "Desconhecido"
            
            # RAM via WMIC/CIM
            cmd_ram = 'powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)"'
            r2 = subprocess.run(cmd_ram, shell=True, capture_output=True, text=True, timeout=4)
            info["ram"] = r2.stdout.strip() + " GB"
        except: pass
        return info

    @classmethod
    def load_db(cls):
        if os.path.exists(HISTORY_DB):
            try:
                with open(HISTORY_DB, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {}

    @classmethod
    def save_db(cls, data):
        try:
            with open(HISTORY_DB, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except: pass

    @classmethod
    def register_machine(cls):
        """Detecta máquina e registra no Dossiê se for nova."""
        hwid = cls.get_hwid()
        db = cls.load_db()
        sys_info = cls.get_system_brief()
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        if hwid not in db:
            db[hwid] = {
                "name": USER_NAME,
                "first_seen": now,
                "hostname": sys_info["hostname"],
                "ip": sys_info["ip"],
                "os": sys_info["os"],
                "cpu": sys_info["cpu"],
                "ram": sys_info["ram"],
                "history": [{"date": now, "action": "MAQUINA REGISTRADA NO SISTEMA"}],
                "notes": []
            }
        else:
            # Garante que campos novos existam
            db[hwid]["ip"] = sys_info["ip"]
            if "notes" not in db[hwid] or isinstance(db[hwid]["notes"], str):
                old = db[hwid].get("notes", "")
                db[hwid]["notes"] = [{"date": now, "info": old}] if old else []
            
            fields = ["hostname", "os", "cpu", "ram"]
            for f in fields:
                if f not in db[hwid]: db[hwid][f] = sys_info[f]
        
        cls.save_db(db)

    @classmethod
    def save_note(cls, note_text, hwid=None):
        """Adiciona uma nova nota sem apagar as anteriores."""
        if not hwid: hwid = cls.get_hwid()
        db = cls.load_db()
        if hwid in db:
            if not isinstance(db[hwid]["notes"], list):
                db[hwid]["notes"] = []
            
            now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            db[hwid]["notes"].append({"date": now, "info": note_text})
            cls.save_db(db)
            cls.log_action(f"Nota adicionada ao dossier")

    @classmethod
    def log_action(cls, action_name):
        """Registra uma ação no histórico do PC atual."""
        hwid = cls.get_hwid()
        db = cls.load_db()
        
        if hwid not in db:
            cls.register_machine()
            db = cls.load_db()
        
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        db[hwid]["history"].append({"date": now, "action": action_name})
        
        if len(db[hwid]["history"]) > 100:
            db[hwid]["history"] = db[hwid]["history"][-100:]
        
        cls.save_db(db)
# ─────────────────────────────────────────────
#  NOME DO USUÁRIO — personalização
# ─────────────────────────────────────────────
def load_username():
    """Lê o nome do técnico salvo no pendrive. Retorna None se não existir."""
    try:
        if os.path.exists(_USER_CFG):
            with open(_USER_CFG, "r", encoding="utf-8") as f:
                name = f.read().strip()
                if name:
                    return name
    except Exception:
        pass
    return None

def save_username(name: str):
    """Salva o nome do técnico na mesma pasta do .exe no pendrive."""
    try:
        with open(_USER_CFG, "w", encoding="utf-8") as f:
            f.write(name.strip())
    except Exception:
        pass


# Nome ativo — preenchido no entry point antes de criar o App
USER_NAME = "USUÁRIO"

# ─────────────────────────────────────────────
#  PALETA REDSEC PRO — coesa, moderna, hacker
# ─────────────────────────────────────────────
BG_DARK      = "#080c0a"
BG_PANEL     = "#0b1410"
BG_CARD      = "#0e1a13"
BG_HOVER     = "#142318"
GREEN_NEON   = "#00e676"   # Verde suave (sucesso / principal)
GREEN_DIM    = "#00a854"
GREEN_DARK   = "#004d22"
CYAN_NEON    = "#00d4ff"   # Ciano azulado (rede / remoto)
BLUE_NEON    = "#40a4ff"   # Azul (runtimes)
PURPLE_NEON  = "#ce93d8"   # Lilás suave (browsers / ativação)
ORANGE_NEON  = "#ff9100"   # Laranja (manutenção / aviso)
RED_NEON     = "#ff5252"   # Vermelho suave (segurança)
YELLOW_NEON  = "#ffd740"   # Dourado (hardware)
WHITE_DIM    = "#d0d8d0"
GRAY_DIM     = "#4a5e50"
BORDER_COLOR = "#00e676"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ─────────────────────────────────────────────
#  TELA DE BOAS-VINDAS — Pede nome na 1ª vez
# ─────────────────────────────────────────────
class WelcomeDialog(tk.Toplevel):
    """
    Aparece na primeira execução (ou quando não há user.cfg).
    Estilo terminal hacker: fundo preto, texto verde, input centralizado.
    Chama on_done(nome) quando o usuário confirma.
    """
    def __init__(self, parent, on_done):
        super().__init__(parent)
        self._on_done = on_done
        self.overrideredirect(True)
        self.configure(bg="#000000")
        self.attributes("-topmost", True)

        w, h = 520, 320
        try:
            import ctypes as _ct
            user32 = _ct.windll.user32
            user32.SetProcessDPIAware()
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
        except Exception:
            self.update_idletasks()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()

        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # ── Fundo canvas ─────────────────────────────────────────────
        cv = tk.Canvas(self, bg="#000000", highlightthickness=0, width=w, height=h)
        cv.pack(fill="both", expand=True)

        # Borda neon externa
        cv.create_rectangle(2, 2, w-2, h-2, outline="#00ff41", width=2)
        cv.create_rectangle(6, 6, w-6, h-6, outline="#004d22", width=1)

        # Cantos decorativos
        cl = 18
        for cx, cy, dx, dy in [(2,2,1,1),(w-2,2,-1,1),(2,h-2,1,-1),(w-2,h-2,-1,-1)]:
            cv.create_line(cx, cy, cx+dx*cl, cy, fill="#00ff41", width=2)
            cv.create_line(cx, cy, cx, cy+dy*cl, fill="#00ff41", width=2)

        # Título
        cv.create_text(w//2, 38, text="◈  TOOLBOX  —  INICIALIZAÇÃO",
                       font=("Courier New", 13, "bold"), fill="#00ff41")
        cv.create_line(20, 58, w-20, 58, fill="#004d22", width=1)

        # Texto instrução — pisca
        self._inst_id = cv.create_text(
            w//2, 95,
            text="IDENTIFIQUE-SE PARA CONTINUAR",
            font=("Courier New", 11), fill="#00b32c"
        )
        self._cv = cv
        self._blink_state = True
        self._blink()

        cv.create_text(w//2, 135, text="INSIRA SEU NOME / APELIDO:",
                       font=("Courier New", 10), fill="#4a5e50")

        # ── Frame do input ────────────────────────────────────────────
        entry_frame = tk.Frame(cv, bg="#001a08", bd=0)
        cv.create_window(w//2, 175, window=entry_frame, width=340, height=38)

        # Borda do entry
        cv.create_rectangle(
            (w//2)-172, 156, (w//2)+172, 194,
            outline="#00ff41", width=1
        )

        self._entry = tk.Entry(
            entry_frame,
            font=("Courier New", 14, "bold"),
            bg="#000d04", fg="#00ff41",
            insertbackground="#00ff41",
            relief="flat", bd=4,
            justify="center"
        )
        self._entry.pack(fill="both", expand=True)
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda e: self._confirm())

        # ── Botão confirmar ───────────────────────────────────────────
        btn_frame = tk.Frame(cv, bg="#000000")
        cv.create_window(w//2, 235, window=btn_frame, width=200, height=36)

        btn = tk.Button(
            btn_frame,
            text="[ CONFIRMAR  ▶ ]",
            font=("Courier New", 11, "bold"),
            bg="#001a08", fg="#00ff41",
            activebackground="#002d10", activeforeground="#00ff41",
            relief="flat", cursor="hand2",
            command=self._confirm
        )
        btn.pack(fill="both", expand=True)

        # Dica em baixo
        cv.create_text(w//2, 285,
                       text="Este nome será exibido na interface.  Pode ser alterado depois.",
                       font=("Courier New", 8), fill="#2a3e2a")

    def _blink(self):
        color = "#00ff41" if self._blink_state else "#004d22"
        self._cv.itemconfig(self._inst_id, fill=color)
        self._blink_state = not self._blink_state
        self.after(600, self._blink)

    def _confirm(self):
        name = self._entry.get().strip()
        if not name:
            self._cv.itemconfig(self._inst_id, text="⚠  NOME NÃO PODE SER VAZIO!", fill="#ff5252")
            self.after(1500, lambda: self._cv.itemconfig(
                self._inst_id, text="IDENTIFIQUE-SE PARA CONTINUAR", fill="#00b32c"))
            return
        # Salva e prossegue
        save_username(name)
        self.destroy()
        self._on_done(name)


# ─────────────────────────────────────────────
#  SPLASH SCREEN — Dark Triad Flash + Mundo/PC Loading
# ─────────────────────────────────────────────
class SplashScreen(tk.Toplevel):
    """
    Splash: imagem mundo/PC transferindo dados + Matrix rain + barra de loading animada
    """
    _LOAD_MSGS = [
        "INICIALIZANDO MÓDULOS...",
        "CARREGANDO SISTEMA...",
        "VERIFICANDO INTEGRIDADE...",
        "CONECTANDO AO SERVIDOR...",
        "DESCRIPTOGRAFANDO DADOS...",
        "SINCRONIZANDO PROTOCOLOS...",
        "INJETANDO PAYLOAD...",
        "COMPILANDO RECURSOS...",
        "AUTENTICANDO USUÁRIO...",
        "ACESSO AUTORIZADO...",
    ]

    def __init__(self, parent, on_done):
        super().__init__(parent)
        self._on_done = on_done
        self.overrideredirect(True)
        self.configure(bg="#000000")
        self.attributes("-topmost", True)

        w, h = 700, 500

        # ── FIX DEFINITIVO: usa Windows API para dimensões reais da tela ──
        # winfo_screenwidth falha antes da janela ser desenhada; ctypes é confiável
        try:
            import ctypes as _ct
            user32 = _ct.windll.user32
            user32.SetProcessDPIAware()          # respeita DPI scaling
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
        except Exception:
            self.update_idletasks()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()

        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.canvas = tk.Canvas(self, width=w, height=h, bg="#000000", highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self._w, self._h = w, h
        self._phase = 0
        self._progress = 0
        self._typed = 0
        self._blink = True
        self._img_ref_world = None

        # ── Matrix rain: colunas com caracteres caindo ──
        self._matrix_cols = []
        col_count = w // 14
        matrix_chars = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉABCDEF0123456789@#$%&"
        for i in range(col_count):
            col = {
                "x": 7 + i * 14,
                "y": random.randint(-h, 0),
                "speed": random.randint(8, 22),
                "chars": [random.choice(matrix_chars) for _ in range(h // 14 + 2)],
            }
            self._matrix_cols.append(col)
        self._matrix_char_pool = matrix_chars
        self._matrix_running = True
        self._draw_matrix()

        # ── Pré-carrega imagem mundo/pc ──
        self._world_img = None
        for name in ["pixel_pc.jpg", "download__5_.jpg", "download__6_.jpg"]:
            p2 = asset(name)
            if os.path.exists(p2):
                try:
                    # Carrega em escala de cinzas para criar a máscara perfeita
                    img_src = Image.open(p2).convert("L")
                    img_src = img_src.crop((10, 10, img_src.width-10, img_src.height-10))
                    img_src = img_src.resize((460, 300), Image.LANCZOS)
                    
                    # Máscara de transparência: o que é preto na imagem vira transparente no Canvas
                    # Isso permite que a chuva Matrix passe POR TRÁS do desenho sem sumir
                    mask = img_src.point(lambda x: 255 if x > 110 else 0)
                    
                    # Cria a imagem RGBA (Verde DedSec + Canal Alpha da máscara)
                    final_rgba = Image.merge("RGBA", (
                        img_src.point(lambda x: 0),                         # R
                        img_src.point(lambda x: min(255, int(x * 2.2))),    # G
                        img_src.point(lambda x: 0),                         # B
                        mask                                                # A (Alpha)
                    ))
                    
                    self._world_img = final_rgba
                    break
                except Exception:
                    pass

        # Borda neon dupla
        self.canvas.create_rectangle(4, 4, w-4, h-4, outline="#004d22", width=1, tags="border")
        self.canvas.create_rectangle(8, 8, w-8, h-8, outline="#00e676", width=2, tags="border")
        for cx, cy, s, e in [(8,8,180,90),(w-8,8,90,90),(8,h-8,270,90),(w-8,h-8,0,90)]:
            self.canvas.create_arc(cx-20,cy-20,cx+20,cy+20, start=s, extent=e,
                                   outline="#00e676", width=2, style="arc")

        self._txt_title = self.canvas.create_text(w//2, 355, text="", font=("Courier New", 22, "bold"), fill="#00e676", anchor="center")
        self._txt_sub   = self.canvas.create_text(w//2, 390, text="", font=("Courier New", 10), fill="#00a854", anchor="center")
        self._txt_bar   = self.canvas.create_text(w//2, 438, text="", font=("Courier New", 10), fill="#004d22", anchor="center")
        self._txt_pct   = self.canvas.create_text(w//2, 462, text="", font=("Courier New", 10), fill="#00e676", anchor="center")

        # Scanlines removidas para evitar "névoa" de cor sobre o preto absoluto
        pass

        self._show_world_img()
        self.after(50, self._animate)

    def _draw_matrix(self):
        """Chuva Matrix animada no fundo da splash."""
        if not self._matrix_running:
            return
        self.canvas.delete("matrix")
        for col in self._matrix_cols:
            col["y"] += col["speed"] * 0.5
            if col["y"] > self._h + 200:
                col["y"] = random.randint(-self._h, -20)
                col["speed"] = random.randint(8, 22)
                col["chars"] = [random.choice(self._matrix_char_pool) for _ in range(self._h // 14 + 2)]
            trail_len = 10
            for t in range(trail_len, 0, -1):
                ty = col["y"] - t * 14
                if 0 <= ty <= self._h:
                    char_idx = min(t, len(col["chars"]) - 1)
                    shade = 40 + int(120 * (1 - t / trail_len))
                    color = f"#00{shade:02x}20"
                    self.canvas.create_text(col["x"], ty, text=col["chars"][char_idx],
                                            font=("Courier New", 9), fill=color, tags="matrix")
            hy = col["y"]
            if 0 <= hy <= self._h:
                self.canvas.create_text(col["x"], hy, text=random.choice(self._matrix_char_pool),
                                        font=("Courier New", 9, "bold"), fill="#ccffcc", tags="matrix")
        self.canvas.tag_lower("matrix")
        self.canvas.tag_lower("scanlines")
        self.after(60, self._draw_matrix)

    def _show_world_img(self):
        if self._world_img is None:
            return
        try:
            self._img_ref_world = ImageTk.PhotoImage(self._world_img)
            self.canvas.create_image(self._w//2, 190, anchor="center",
                                     image=self._img_ref_world, tags="world_img")
            self.canvas.tag_lower("world_img")
        except Exception:
            pass

    def _animate(self):
        if self._phase == 0:
            title = "DEDSEC TOOLBOX"
            if self._typed <= len(title):
                shown = title[:self._typed]
                cursor = "_" if self._blink else " "
                self._blink = not self._blink
                self.canvas.itemconfig(self._txt_title, text=shown + cursor)
                self._typed += 1
                self.after(80, self._animate)
            else:
                self.canvas.itemconfig(self._txt_title, text=title)
                self.canvas.itemconfig(self._txt_sub, text=f"v{APP_VERSION}  //  by GabrielRj6")
                self._phase = 1
                self.after(200, self._animate)
        elif self._phase == 1:
            if self._progress <= 100:
                filled = int(self._progress / 5)
                bar = "█" * filled + "░" * (20 - filled)
                self.canvas.itemconfig(self._txt_bar, text=f"[{bar}]")
                msg_idx = min(int(self._progress / 10), len(self._LOAD_MSGS) - 1)
                self.canvas.itemconfig(self._txt_pct, text=f"{self._progress}%  {self._LOAD_MSGS[msg_idx]}")
                self._progress += 2
                self.after(38, self._animate)
            else:
                self.canvas.itemconfig(self._txt_bar, text="[████████████████████]")
                self.canvas.itemconfig(self._txt_pct, text="100%  ACESSO CONCEDIDO ✓")
                self._phase = 2
                self.after(600, self._animate)
        elif self._phase == 2:
            self._matrix_running = False
            self.destroy()
            self._on_done()


# ─────────────────────────────────────────────
#  EXECUTOR DE COMANDOS
# ─────────────────────────────────────────────
def run_cmd(cmd, output_widget=None, success_msg="Concluído!"):
    def _run():
        try:
            if output_widget:
                output_widget.configure(state="normal")
                output_widget.delete("1.0", "end")
                output_widget.insert("end", f"[*] Executando...\n\n", "info")
            proc = subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            # --- Alerta de Permissão se necessário ---
            if not IS_ADMIN:
                if any(x in cmd.lower() for x in ["net stop", "net start", "sfc", "dism", "reg add", "netsh", "powershell"]):
                    if output_widget:
                        output_widget.insert("end", "[!] AVISO: Este comando pode exigir PRIVILÉGIOS DE ADMINISTRADOR.\n", "warn")
                        output_widget.see("end")
            for line in proc.stdout:
                if output_widget:
                    output_widget.insert("end", line)
                    output_widget.see("end")
                    output_widget.update()
            proc.wait()
            if output_widget:
                output_widget.insert("end", f"\n[✓] {success_msg}\n", "ok")
                output_widget.see("end")
                output_widget.configure(state="disabled")
            
            # ── LOG AUTOMÁTICO ──
            HistoryManager.log_action(success_msg)
        except Exception as e:
            if output_widget:
                output_widget.insert("end", f"\n[!] Erro: {e}\n", "err")
                output_widget.configure(state="disabled")
    threading.Thread(target=_run, daemon=True).start()


def run_winget(pkg_id, name, output_widget):
    run_cmd(
        f'winget install --id {pkg_id} -e --silent --accept-source-agreements --accept-package-agreements',
        output_widget,
        f"{name} instalado com sucesso!"
    )


# ─────────────────────────────────────────────
#  TERMINAL BOX
# ─────────────────────────────────────────────
class TerminalBox(ctk.CTkTextbox):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            font=("Courier New", 11),
            fg_color=BG_DARK,
            text_color=GREEN_NEON,
            border_color=GREEN_DARK,
            border_width=1,
            scrollbar_button_color=GREEN_DARK,
            **kwargs
        )
        self.tag_config("info", foreground=CYAN_NEON)
        self.tag_config("ok",   foreground=GREEN_NEON)
        self.tag_config("err",  foreground=RED_NEON)
        self.tag_config("warn", foreground=YELLOW_NEON)
        # Placeholder
        self.configure(state="normal")
        self.insert("end", ">>> aguardando comando...\n", "info")
        self.configure(state="disabled")


# ─────────────────────────────────────────────
#  BOTÃO DEDSEC
# ─────────────────────────────────────────────
class DedSecButton(ctk.CTkButton):
    def __init__(self, master, number=None, **kwargs):
        text = kwargs.pop("text", "")
        text_color = kwargs.pop("text_color", GREEN_NEON)
        display = f"  [{number}]  {text}" if number is not None else text
        super().__init__(
            master,
            text=display,
            font=("Courier New", 12, "bold"),
            fg_color=BG_CARD,
            hover_color=BG_HOVER,
            text_color=text_color,
            border_color=GREEN_DARK,
            border_width=1,
            corner_radius=2,
            anchor="w",
            **kwargs
        )


# ─────────────────────────────────────────────
#  GLITCH LABEL
# ─────────────────────────────────────────────
class GlitchLabel(ctk.CTkLabel):
    GLITCH_CHARS = "!@#$%^&*<>?/\\|█▓▒░"

    def __init__(self, master, text, **kwargs):
        self._original = text
        super().__init__(master, text=text, **kwargs)
        self._glitching = False
        self.after(random.randint(3000, 8000), self._start_glitch)

    def _start_glitch(self):
        if not self._glitching:
            self._glitching = True
            self._glitch_frames = 0
            self._do_glitch()

    def _do_glitch(self):
        if self._glitch_frames < 6:
            glitched = "".join(
                random.choice(self.GLITCH_CHARS) if ch != " " and random.random() < 0.25 else ch
                for ch in self._original
            )
            self.configure(text=glitched)
            self._glitch_frames += 1
            self.after(60, self._do_glitch)
        else:
            self.configure(text=self._original)
            self._glitching = False
            self.after(random.randint(5000, 12000), self._start_glitch)



# ─────────────────────────────────────────────
#  GIF PLAYER — reproduz GIF animado via PIL
# ─────────────────────────────────────────────
class GifPlayer(tk.Canvas):
    """Canvas que reproduz GIF animado via PIL.
    one_shot=True  → toca uma vez e chama on_done().
    contain=True   → letterbox (mantém proporção, pode ter bordas).
    contain=False  → cover (preenche tudo, sem bordas pretas).
    tint=True      → tinge de verde."""

    def __init__(self, master, gif_path, one_shot=False, on_done=None,
                 tint=False, contain=False, bg="#000000", **kwargs):
        super().__init__(master, bg=bg, highlightthickness=0, **kwargs)
        self._frames_pil = []
        self._delays     = []
        self._idx        = 0
        self._one_shot   = one_shot
        self._on_done    = on_done
        self._contain    = contain
        self._running    = False
        self._after_id   = None
        self._img_item   = None
        self._cache      = {}

        if gif_path and os.path.exists(gif_path):
            self._load(gif_path, tint)
        # bind Configure: quando o canvas ganhar tamanho real, inicia sozinho
        self.bind("<Configure>", self._on_resize)

    def _load(self, path, tint):
        """Carrega frames NA ORDEM CERTA usando ImageSequence.Iterator."""
        try:
            from PIL import ImageSequence
            gif = Image.open(path)
            for raw in ImageSequence.Iterator(gif):
                # duration deve ser lida ANTES de converter
                d = raw.info.get("duration", 60)
                frame = raw.copy().convert("RGBA")
                if tint:
                    r, g, b, a = frame.split()
                    frame = Image.merge("RGBA", (
                        r.point(lambda x: int(x * 0.10)),
                        g.point(lambda x: min(255, int(x * 1.30))),
                        b.point(lambda x: int(x * 0.10)),
                        a
                    ))
                self._frames_pil.append(frame)
                self._delays.append(max(30, d))
        except Exception:
            pass

    def _on_resize(self, event):
        """Invalida cache. Se ainda não iniciou e tem frames, começa agora."""
        self._cache.clear()
        if self._frames_pil and not self._running:
            self._running = True
            self._idx = 0
            self._show_frame()

    def start(self):
        """Inicia ou reinicia do frame 0."""
        if not self._frames_pil:
            return
        if self._after_id:
            try: self.after_cancel(self._after_id)
            except: pass
        self._running = True
        self._idx = 0
        self._cache.clear()
        self._img_item = None
        self.delete("all")
        self._show_frame()

    def stop(self):
        self._running = False
        if self._after_id:
            try: self.after_cancel(self._after_id)
            except: pass
        self._after_id = None

    def _scale(self, idx):
        """Escala frame para o tamanho atual do canvas (cover ou contain)."""
        w = max(self.winfo_width(), 1)
        h = max(self.winfo_height(), 1)
        key = (w, h, idx)
        if key not in self._cache:
            src = self._frames_pil[idx]
            sw, sh = src.size
            if self._contain:
                ratio = min(w / sw, h / sh)
            else:
                ratio = max(w / sw, h / sh)   # cover: preenche tudo
            nw = max(1, int(sw * ratio))
            nh = max(1, int(sh * ratio))
            self._cache[key] = ImageTk.PhotoImage(src.resize((nw, nh), Image.LANCZOS))
        return self._cache[key]

    def _show_frame(self):
        if not self._running:
            return
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 4 or h < 4:            # canvas ainda não tem tamanho
            self._after_id = self.after(40, self._show_frame)
            return

        photo = self._scale(self._idx)
        cx, cy = w // 2, h // 2
        if self._img_item is None:
            self._img_item = self.create_image(cx, cy, anchor="center", image=photo)
        else:
            self.coords(self._img_item, cx, cy)
            self.itemconfig(self._img_item, image=photo)

        delay = self._delays[self._idx] if self._idx < len(self._delays) else 60
        self._idx += 1

        if self._idx >= len(self._frames_pil):
            if self._one_shot:
                self._running = False
                if self._on_done:
                    self.after(150, self._on_done)
                return
            self._idx = 0

        self._after_id = self.after(delay, self._show_frame)


# ─────────────────────────────────────────────
#  SCREENSAVER — olho após 5 min de inatividade
# ─────────────────────────────────────────────
class ScreenSaver:
    """
    Screensaver real: usa GetLastInputInfo para detectar idle GLOBAL do Windows.
    Só ativa se o usuário ficar 1h sem tocar em NADA no PC (mouse/teclado/qualquer app).
    Polling a cada 30s — sem sobrecarregar o tkinter com bind_all.
    """
    IDLE_THRESHOLD_MS = 3_600_000  # 1 hora em milissegundos
    POLL_INTERVAL_MS  = 30_000     # checa a cada 30 segundos

    def __init__(self, root, gif_path):
        self._root     = root
        self._gif_path = gif_path
        self._overlay  = None
        self._player   = None
        self._active   = False
        self._poll_id  = None
        # Bind apenas para fechar o screensaver quando usuário volta
        root.bind_all("<Motion>",        self._on_activity, add="+")
        root.bind_all("<Key>",           self._on_activity, add="+")
        root.bind_all("<Button>",        self._on_activity, add="+")
        root.bind_all("<MouseWheel>",    self._on_activity, add="+")
        self._poll()

    @staticmethod
    def _get_idle_ms():
        """Retorna ms desde o último input no Windows (mouse/teclado em qualquer app)."""
        try:
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
            tick = ctypes.windll.kernel32.GetTickCount()
            return tick - lii.dwTime
        except Exception:
            return 0

    def _poll(self):
        """Verifica idle global a cada 30s. Mostra screensaver se >= 1h."""
        if not self._active:
            idle = self._get_idle_ms()
            if idle >= self.IDLE_THRESHOLD_MS:
                self._show()
        self._poll_id = self._root.after(self.POLL_INTERVAL_MS, self._poll)

    def _on_activity(self, event=None):
        """Fecha screensaver se estiver ativo (usuário voltou)."""
        if self._active:
            self._hide()

    def _show(self):
        if self._overlay or not self._gif_path:
            return
        self._active = True
        try:
            self._overlay = tk.Toplevel(self._root)
            self._overlay.overrideredirect(True)
            self._overlay.attributes("-topmost", True)
            self._overlay.configure(bg="#000000")
            try:
                u32 = ctypes.windll.user32
                sw, sh = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
            except Exception:
                sw = self._root.winfo_screenwidth()
                sh = self._root.winfo_screenheight()
            self._overlay.geometry(f"{sw}x{sh}+0+0")
            self._player = GifPlayer(
                self._overlay, self._gif_path,
                one_shot=False, tint=False, contain=True, bg="#000000"
            )
            self._player.pack(fill="both", expand=True)
            self._overlay.update_idletasks()
            self._player.start()
            for ev in ("<Motion>", "<Key>", "<Button>", "<MouseWheel>"):
                self._overlay.bind(ev, self._on_activity, add="+")
            self._overlay.focus_set()
        except Exception:
            self._active = False

    def _hide(self):
        self._active = False
        if self._player:
            try: self._player.stop()
            except: pass
            self._player = None
        if self._overlay:
            try: self._overlay.destroy()
            except: pass
            self._overlay = None



MINI_ASCII = {
    "RUNTIMES":     "[ RUNTIME & LIBS ]",
    "BROWSERS":     "[ NAVEGADORES & COM ]",
    "REMOTE":       "[ SUPORTE REMOTO ]",
    "UTILS":        "[ UTILITÁRIOS ]",
    "MAINTENANCE":  "[ MANUTENÇÃO ]",
    "NETWORK":      "[ REDE & CONEXÃO ]",
    "HARDWARE":     "[ HARDWARE & DRIVERS ]",
    "SECURITY":     "[ SEGURANÇA ]",
    "SYSINFO":      "[ INFO DO SISTEMA ]",
    "ACTIVATION":   "[ ATIVAÇÃO ]",
    "CLEAN":        "[ LIMPEZA PROFUNDA ]",
    "KIT":          "[ KIT PC NOVO ]",
    "KALI":         "[ KALI LINUX TOOLS ]",
    "BACKUP":       "[ BACKUP RÁPIDO ]",
    "PROCESSOS":    "[ GERENCIAR PROCESSOS ]",
    "VELOCIDADE":   "[ VELOCIDADE & REDE ]",
    "IMPRESSORAS":  "[ IMPRESSORAS & FILA ]",
    "DISCO":        "[ DISCO & ARMAZENAMENTO ]",
}


# ─────────────────────────────────────────────
#  PAINEL BASE — SEM espaço preto desnecessário
# ─────────────────────────────────────────────
class BasePanel(ctk.CTkFrame):
    def __init__(self, master, title_key, color=GREEN_NEON, **kwargs):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=0, **kwargs)
        self._color = color
        self._build_header(title_key)

        # ── Terminal expansível ──────────────────────────────────────────
        # Em modo normal: 95px (compacto). Em modo execução: expande, botões somem.
        self._terminal_expanded = False
        self.terminal = TerminalBox(self, height=95)
        self.terminal.pack(fill="x", padx=8, pady=(0, 4))

        # Botão colapsar/expandir terminal
        self._toggle_btn = ctk.CTkButton(
            self, text="▼ VER OUTPUT COMPLETO",
            font=("Courier New", 9), height=18,
            fg_color=BG_DARK, hover_color=BG_HOVER,
            text_color=GRAY_DIM, border_width=0, corner_radius=0,
            command=self._toggle_terminal
        )
        self._toggle_btn.pack(fill="x", padx=8, pady=(0, 2))

        # Área scrollable de botões ocupa o resto
        self.btn_frame = ctk.CTkScrollableFrame(
            self, fg_color=BG_PANEL,
            scrollbar_button_color=GREEN_DARK
        )
        self.btn_frame.pack(fill="both", expand=True, padx=8, pady=(0, 6))

    def _toggle_terminal(self):
        if self._terminal_expanded:
            self.terminal.configure(height=95)
            self._toggle_btn.configure(text="▼ VER OUTPUT COMPLETO")
            self.btn_frame.pack(fill="both", expand=True, padx=8, pady=(0, 6))
            self._terminal_expanded = False
        else:
            self.terminal.configure(height=350)
            self._toggle_btn.configure(text="▲ VER BOTÕES")
            self.btn_frame.pack_forget()
            self._terminal_expanded = True

    def _auto_expand_terminal(self):
        if not self._terminal_expanded:
            self.terminal.configure(height=350)
            self._toggle_btn.configure(text="▲ VER BOTÕES")
            self.btn_frame.pack_forget()
            self._terminal_expanded = True

    def _build_header(self, key):
        title_text = MINI_ASCII.get(key, f"[ {key} ]")
        header_frame = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0, height=38)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        lbl = GlitchLabel(
            header_frame, text=title_text,
            font=("Courier New", 14, "bold"),
            text_color=self._color,
            fg_color=BG_DARK,
            corner_radius=0
        )
        lbl.pack(side="left", padx=10, pady=6)

        sep = ctk.CTkFrame(self, height=1, fg_color=self._color)
        sep.pack(fill="x", padx=0, pady=(0, 4))

    def add_button(self, number, text, command, color=None):
        # Envolve o command para auto-expandir o terminal e LOGAR A AÇÃO
        def _wrapped_cmd(c=command, t=text):
            self._auto_expand_terminal()
            # Log automático no dossiê
            HistoryManager.log_action(f"Executou: {t}")
            c()
        btn = DedSecButton(
            self.btn_frame,
            number=number,
            text=text,
            command=_wrapped_cmd,
            text_color=color or GREEN_NEON,
            height=32
        )
        btn.pack(fill="x", pady=2)
        return btn


    def add_section_label(self, text):
        lbl = ctk.CTkLabel(
            self.btn_frame,
            text=f"  ── {text} ──",
            font=("Courier New", 11),
            text_color=GRAY_DIM,
            anchor="w"
        )
        lbl.pack(fill="x", pady=(8, 2))


# ════════════════════════════════════════════════════════
#  SEÇÃO 1: RUNTIMES
# ════════════════════════════════════════════════════════
class RuntimesPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "RUNTIMES", BLUE_NEON)
        t = self.terminal
        items = [
            (1,  "Microsoft WebView2",       "Microsoft.EdgeWebView2Runtime"),
            (2,  "Visual C++ x64",           "Microsoft.VCRedist.2015+.x64"),
            (3,  "Visual C++ x86",           "Microsoft.VCRedist.2015+.x86"),
            (4,  "DirectX Runtime",          "Microsoft.DirectX"),
            (5,  "XNA Framework 4.0",        "Microsoft.XNAFramework"),
            (6,  "NVIDIA PhysX",             "Nvidia.PhysX"),
            (7,  ".NET Desktop Runtime 8",   "Microsoft.DotNet.DesktopRuntime.8"),
            (8,  ".NET Framework 4.8",       "Microsoft.DotNet.Framework.DeveloperPack_4"),
            (9,  "Java Runtime (JRE)",       "Oracle.JavaRuntimeEnvironment"),
            (10, "OpenAL Audio Library",     "OpenAL.OpenAL"),
        ]
        for num, name, pkg in items:
            self.add_button(num, name, lambda p=pkg, n=name: run_winget(p, n, t))
        self.add_section_label("INSTALAR TUDO")
        self.add_button("★", "INSTALAR TODOS OS RUNTIMES", self._install_all, GREEN_NEON)

    def _install_all(self):
        pkgs = [
            "Microsoft.EdgeWebView2Runtime","Microsoft.VCRedist.2015+.x64",
            "Microsoft.VCRedist.2015+.x86","Microsoft.DirectX",
            "Microsoft.DotNet.DesktopRuntime.8","Microsoft.DotNet.Framework.DeveloperPack_4",
            "Oracle.JavaRuntimeEnvironment",
        ]
        cmd = " & ".join([f'winget install --id {p} -e --silent --accept-source-agreements --accept-package-agreements' for p in pkgs])
        run_cmd(cmd, self.terminal, "TODOS OS RUNTIMES INSTALADOS!")


# ════════════════════════════════════════════════════════
#  SEÇÃO 2: NAVEGADORES
# ════════════════════════════════════════════════════════
class BrowsersPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "BROWSERS", PURPLE_NEON)
        t = self.terminal
        self.add_section_label("NAVEGADORES")
        browsers = [
            (1,"Google Chrome","Google.Chrome"),(2,"Mozilla Firefox","Mozilla.Firefox"),
            (3,"Brave Browser","Brave.Brave"),(4,"Opera GX","Opera.OperaGX"),
            (5,"Microsoft Edge","Microsoft.Edge"),(6,"Vivaldi","VivaldiTechnologies.Vivaldi"),
        ]
        for num, name, pkg in browsers:
            self.add_button(num, name, lambda p=pkg, n=name: run_winget(p, n, t))
        self.add_section_label("COMUNICAÇÃO")
        comms = [
            (7,"Discord","Discord.Discord"),(8,"Telegram Desktop","Telegram.TelegramDesktop"),
            (9,"WhatsApp Desktop","WhatsApp.WhatsApp"),(10,"Zoom","Zoom.Zoom"),
            (11,"Microsoft Teams","Microsoft.Teams"),(12,"Skype","Microsoft.Skype"),
        ]
        for num, name, pkg in comms:
            self.add_button(num, name, lambda p=pkg, n=name: run_winget(p, n, t))


# ════════════════════════════════════════════════════════
#  SEÇÃO 3: SUPORTE REMOTO
# ════════════════════════════════════════════════════════
class RemotePanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "REMOTE", CYAN_NEON)
        t = self.terminal
        items = [
            (1,"AnyDesk","AnyDeskSoftwareGmbH.AnyDesk"),
            (2,"TeamViewer","TeamViewer.TeamViewer"),
            (3,"Supremo Remote Desktop","Supremo.Supremo"),
            (4,"RustDesk (Open Source)","RustDesk.RustDesk"),
            (5,"UltraViewer","UltraViewer.UltraViewer"),
        ]
        for num, name, pkg in items:
            self.add_button(num, name, lambda p=pkg, n=name: run_winget(p, n, t))
        self.add_section_label("INSTALAR TUDO")
        self.add_button("★", "INSTALAR TODAS AS FERRAMENTAS REMOTAS", self._install_all, YELLOW_NEON)

    def _install_all(self):
        pkgs = ["AnyDeskSoftwareGmbH.AnyDesk","TeamViewer.TeamViewer","RustDesk.RustDesk","UltraViewer.UltraViewer"]
        cmd = " & ".join([f'winget install --id {p} -e --silent --accept-source-agreements --accept-package-agreements' for p in pkgs])
        run_cmd(cmd, self.terminal, "TODAS AS FERRAMENTAS REMOTAS INSTALADAS!")


# ════════════════════════════════════════════════════════
#  SEÇÃO 4: UTILITÁRIOS
# ════════════════════════════════════════════════════════
class UtilsPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "UTILS", BLUE_NEON)
        t = self.terminal
        sections = {
            "COMPACTADORES":  [(1,"7-Zip","7zip.7zip"),(2,"WinRAR","RARLab.WinRAR")],
            "MÍDIA":          [(3,"VLC","VideoLAN.VLC"),(4,"K-Lite Codec","CodecGuide.K-LiteCodecPack.Standard")],
            "TEXTO / CÓDIGO": [(5,"Notepad++","Notepad++.Notepad++"),(6,"VS Code","Microsoft.VisualStudioCode")],
            "IMAGENS":        [(7,"IrfanView","IrfanSkiljan.IrfanView"),(8,"GIMP","GIMP.GIMP")],
            "DOCUMENTOS":     [(9,"LibreOffice","TheDocumentFoundation.LibreOffice"),(10,"Acrobat Reader","Adobe.Acrobat.Reader.64-bit"),(11,"Foxit PDF","Foxit.FoxitReader")],
            "SISTEMA":        [(12,"Everything","voidtools.Everything"),(13,"WinDirStat","WinDirStat.WinDirStat"),(14,"CrystalDiskMark","CrystalDewWorld.CrystalDiskMark")],
            "GAMES":          [(15,"Steam","Valve.Steam"),(16,"Epic Games","EpicGames.EpicGamesLauncher")],
            "STREAMING":      [(17,"OBS Studio","OBSProject.OBSStudio"),(18,"Streamlabs OBS","Streamlabs.Streamlabs"),(19,"Spotify","Spotify.Spotify")],
        }
        for section_name, items in sections.items():
            self.add_section_label(section_name)
            for num, name, pkg in items:
                self.add_button(num, name, lambda p=pkg, n=name: run_winget(p, n, t))


# ════════════════════════════════════════════════════════
#  SEÇÃO 5: MANUTENÇÃO
# ════════════════════════════════════════════════════════
class MaintenancePanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "MAINTENANCE", ORANGE_NEON)
        t = self.terminal
        self.add_section_label("INTEGRIDADE DO SISTEMA")
        self.add_button(1, "Diagnóstico Inteligente (1-Click) ★", self._smart_diag, CYAN_NEON)
        self.add_button(2, "SFC /SCANNOW (Correção rápida)",   lambda: run_cmd("sfc /scannow", t, "SFC concluído!"))
        self.add_button(3, "DISM /RestoreHealth (Reparo BD)",  lambda: run_cmd("dism /online /cleanup-image /restorehealth", t, "DISM concluído!"))
        self.add_button(4, "Criar Ponto de Restauração",       self._create_restore_point, GREEN_NEON)
        self.add_section_label("DISCO")
        self.add_button(5, "CHKDSK C:",             lambda: run_cmd("chkdsk C: /f /r", t))
        self.add_button(6, "Limpeza de Disco",       lambda: run_cmd("cleanmgr", t))
        self.add_button(9, "Desfragmentar C:",       lambda: run_cmd("defrag C: /U /V", t))
        self.add_section_label("WINDOWS UPDATE")
        self.add_button(7, "Reiniciar Windows Update", self._restart_wu)
        self.add_button(8, "Limpar Cache WU",          self._clear_wu)
        self.add_section_label("OUTROS")
        self.add_button(10, "GPUpdate /force",           lambda: run_cmd("gpupdate /force", t))
        self.add_button(11, "Limpar Cache DNS",          lambda: run_cmd("ipconfig /flushdns", t, "DNS limpo!"))
        self.add_button(12, "Restaurar config IE/Edge",  lambda: run_cmd("RunDll32.exe InetCpl.cpl,ResetIEtoDefaults", t))

    def _smart_diag(self):
        cmd = "echo [1/3] Limpando Temp... & del /q /f /s %temp%\\* & echo [2/3] Rodando SFC... & sfc /scannow & echo [3/3] Rodando DISM... & dism /online /cleanup-image /restorehealth"
        run_cmd(cmd, self.terminal, "DIAGNÓSTICO SMART CONCLUÍDO!")

    def _create_restore_point(self):
        # Habilita a proteção do sistema se estiver desativada, e cria o ponto
        cmd = 'powershell -NoProfile -Command "Enable-ComputerRestore -Drive C:\\; Checkpoint-Computer -Description \'DedSec_Toolbox_Save\' -RestorePointType \'MODIFY_SETTINGS\'"'
        run_cmd(cmd, self.terminal, "Ponto de Restauração Criado!")

    def _restart_wu(self):
        run_cmd("net stop wuauserv & net stop cryptSvc & net stop bits & net stop msiserver & timeout /t 3 & net start wuauserv & net start cryptSvc & net start bits & net start msiserver", self.terminal, "Windows Update reiniciado!")

    def _clear_wu(self):
        run_cmd('net stop wuauserv & net stop bits & rd /s /q "C:\\Windows\\SoftwareDistribution\\Download" & mkdir "C:\\Windows\\SoftwareDistribution\\Download" & net start wuauserv & net start bits', self.terminal, "Cache WU limpo!")


# ════════════════════════════════════════════════════════
#  SEÇÃO 6: REDE
# ════════════════════════════════════════════════════════
class NetworkPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "NETWORK", CYAN_NEON)
        t = self.terminal
        self.add_section_label("TROCAR DNS")
        self.add_button(1, "DNS Google     (8.8.8.8 / 8.8.4.4)",    lambda: self._set_dns("8.8.8.8","8.8.4.4"))
        self.add_button(2, "DNS Cloudflare (1.1.1.1 / 1.0.0.1)",    lambda: self._set_dns("1.1.1.1","1.0.0.1"))
        self.add_button(3, "DNS OpenDNS    (208.67.222.222)",        lambda: self._set_dns("208.67.222.222","208.67.220.220"))
        self.add_button(4, "DNS AdGuard    (bloqueia anúncios) ★",   lambda: self._set_dns("94.140.14.14","94.140.15.15"), GREEN_NEON)
        self.add_section_label("DIAGNÓSTICO")
        self.add_button(5,  "Limpar Cache DNS",          lambda: run_cmd("ipconfig /flushdns", t, "DNS limpo!"))
        self.add_button(6,  "Resetar TCP/IP + Winsock",  self._reset_net, RED_NEON)
        self.add_button(7,  "Ver IP (ipconfig /all)",    lambda: run_cmd("ipconfig /all", t))
        self.add_button(8,  "Ping Google",               lambda: run_cmd("ping google.com -n 10", t))
        self.add_button(9,  "Traceroute Google",         lambda: run_cmd("tracert google.com", t))
        self.add_button(10, "Netstat (conexões ativas)", lambda: run_cmd("netstat -an", t))
        self.add_button(11, "Tabela de Rotas",           lambda: run_cmd("route print", t))
        self.add_button(12, "Renovar IP (DHCP)",         lambda: run_cmd("ipconfig /release & ipconfig /renew & ipconfig /flushdns", t, "IP renovado!"))

    def _set_dns(self, dns1, dns2):
        cmd = (f'powershell -Command "Get-NetAdapter | Where-Object {{$_.Status -eq \'Up\'}} | '
               f'Set-DnsClientServerAddress -ServerAddresses (\'{dns1}\',\'{dns2}\')" & ipconfig /flushdns')
        run_cmd(cmd, self.terminal, f"DNS {dns1} aplicado!")

    def _reset_net(self):
        run_cmd("netsh int ip reset & netsh int ipv6 reset & netsh winsock reset & ipconfig /flushdns & ipconfig /release & ipconfig /renew", self.terminal, "Rede resetada! Reinicie o PC.")


# ════════════════════════════════════════════════════════
#  SEÇÃO 7: HARDWARE
# ════════════════════════════════════════════════════════
class HardwarePanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "HARDWARE", YELLOW_NEON)
        t = self.terminal
        self.add_section_label("NVIDIA")
        self.add_button(1, "GeForce Experience",              lambda: run_winget("Nvidia.GeForceExperience","GeForce Experience",t))
        self.add_button(2, "NVIDIA App (Novo)",               lambda: run_winget("Nvidia.NvidiaApp","NVIDIA App",t))
        self.add_section_label("AMD")
        self.add_button(3, "AMD Adrenalin",                   lambda: run_winget("AMD.Adrenalin","AMD Adrenalin",t))
        self.add_button(4, "DDU - Display Driver Uninstaller ⚠", self._open_ddu, RED_NEON)
        self.add_section_label("MONITORAMENTO")
        self.add_button(5,  "CPU-Z + GPU-Z",                  self._cpu_gpu_z)
        self.add_button(6,  "HWMonitor (Temperatura)",        lambda: run_winget("CPUID.HWMonitor","HWMonitor",t))
        self.add_button(7,  "CrystalDiskInfo",                lambda: run_winget("CrystalDewWorld.CrystalDiskInfo","CrystalDiskInfo",t))
        self.add_button(8,  "MSI Afterburner",                lambda: run_winget("MSI.Afterburner","MSI Afterburner",t))
        self.add_button(9,  "HWiNFO64",                       lambda: run_winget("REALiX.HWiNFO","HWiNFO64",t))
        self.add_button(10, "OCCT (Teste de estabilidade)",   lambda: run_winget("OCCT.OCCT","OCCT",t))

    def _open_ddu(self):
        run_cmd('start https://www.guru3d.com/files-details/display-driver-uninstaller-download.html', self.terminal)
        self.terminal.configure(state="normal")
        self.terminal.insert("end", "\n[!] Use o DDU em modo de segurança!\n", "warn")
        self.terminal.configure(state="disabled")

    def _cpu_gpu_z(self):
        run_cmd(
            'winget install --id CPUID.CPU-Z -e --silent --accept-source-agreements --accept-package-agreements & '
            'winget install --id techpowerup.GPU-Z -e --silent --accept-source-agreements --accept-package-agreements',
            self.terminal, "CPU-Z + GPU-Z instalados!"
        )


# ════════════════════════════════════════════════════════
#  SEÇÃO 8: SEGURANÇA
# ════════════════════════════════════════════════════════
class SecurityPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "SECURITY", RED_NEON)
        t = self.terminal
        self.add_section_label("ANTIVÍRUS")
        self.add_button(1, "Instalar Malwarebytes",      lambda: run_winget("Malwarebytes.Malwarebytes","Malwarebytes",t))
        self.add_button(2, "Scan Rápido (Defender)",     lambda: run_cmd(f'"{os.environ.get("ProgramFiles","C:\\Program Files")}\\Windows Defender\\MpCmdRun.exe" -Scan -ScanType 1', t, "Scan rápido concluído!"))
        self.add_button(3, "Scan Completo (Defender)",   lambda: run_cmd(f'"{os.environ.get("ProgramFiles","C:\\Program Files")}\\Windows Defender\\MpCmdRun.exe" -Scan -ScanType 2', t, "Scan completo concluído!"))
        self.add_button(4, "Atualizar Definições",       lambda: run_cmd(f'"{os.environ.get("ProgramFiles","C:\\Program Files")}\\Windows Defender\\MpCmdRun.exe" -SignatureUpdate', t, "Definições atualizadas!"))
        self.add_section_label("FIREWALL")
        self.add_button(5, "✓ ATIVAR Firewall",          lambda: run_cmd("netsh advfirewall set allprofiles state on", t, "Firewall ATIVADO!"), GREEN_NEON)
        self.add_button(6, "✗ DESATIVAR Firewall ⚠",    self._disable_fw, RED_NEON)
        self.add_button(7, "Ver Regras do Firewall",     lambda: run_cmd("netsh advfirewall show allprofiles", t))
        self.add_section_label("DIAGNÓSTICO")
        self.add_button(8,  "Programas na Inicialização", lambda: run_cmd('powershell -NoProfile -Command "Get-CimInstance Win32_StartupCommand | Format-Table Name,Command,Location -AutoSize"', t))
        self.add_button(9,  "Tarefas Agendadas",          lambda: run_cmd("schtasks /query /fo TABLE", t))
        self.add_button(10, "Processos em Execução",      lambda: run_cmd("tasklist /v", t))
        self.add_button(11, "Usuários e Grupos Locais",   lambda: run_cmd("net user & net localgroup", t))

    def _disable_fw(self):
        if messagebox.askyesno("⚠ ATENÇÃO", "Desativar o Firewall deixa o PC vulnerável!\n\nConfirma?", icon="warning"):
            run_cmd("netsh advfirewall set allprofiles state off", self.terminal, "Firewall DESATIVADO!")


# ════════════════════════════════════════════════════════
#  SEÇÃO 9: INFO DO SISTEMA
# ════════════════════════════════════════════════════════
class SysInfoPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "SYSINFO", GREEN_NEON)
        t = self.terminal
        self.add_button(1, "Resumo do Sistema",           self._quick_info)
        self.add_button(2, "systeminfo Completo",         lambda: run_cmd("systeminfo", t))
        self.add_button(3, "Salvar Relatório no Desktop", self._save_report)
        self.add_button(4, "Informações de Rede",         lambda: run_cmd("ipconfig /all", t))
        self.add_button(5, "Processos (tasklist)",        lambda: run_cmd("tasklist", t))

    def _quick_info(self):
        cmd = (
            'echo === SISTEMA === & '
            'powershell -NoProfile -Command "(Get-CimInstance Win32_OperatingSystem) | Format-List Caption,BuildNumber,OSArchitecture" & '
            'echo === CPU === & '
            'powershell -NoProfile -Command "(Get-CimInstance Win32_Processor) | Format-List Name,NumberOfCores,MaxClockSpeed" & '
            'echo === RAM === & '
            'powershell -NoProfile -Command "$os=Get-CimInstance Win32_OperatingSystem; Write-Host (\'Total: \'+[math]::Round($os.TotalVisibleMemorySize/1MB,2)+\' GB   Livre: \'+[math]::Round($os.FreePhysicalMemory/1MB,2)+\' GB\')" & '
            'echo === DISCO === & '
            'powershell -NoProfile -Command "Get-PSDrive -PSProvider FileSystem | Format-Table -AutoSize"'
        )
        run_cmd(cmd, self.terminal, "Coleta concluída!")

    def _save_report(self):
        desktop = os.path.join(os.environ.get("USERPROFILE","C:\\Users\\Default"), "Desktop", "relatorio_sistema.txt")
        run_cmd(f'systeminfo > "{desktop}"', self.terminal, f"Relatório salvo em: {desktop}")


# ════════════════════════════════════════════════════════
#  SEÇÃO 10: ATIVAÇÃO
# ════════════════════════════════════════════════════════
class ActivationPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "ACTIVATION", PURPLE_NEON)
        t = self.terminal
        info = ctk.CTkLabel(
            self.btn_frame,
            text="  ⚠  Script externo — requer conexão com a internet.",
            font=("Courier New", 11),
            text_color=YELLOW_NEON, anchor="w"
        )
        info.pack(fill="x", pady=(0, 8))
        self.add_button(1, "Ativar Windows / Office (MAS)", lambda: run_cmd('powershell -Command "irm https://get.activated.win | iex"', t))
        self.add_button(2, "Ver Status de Ativação",         lambda: run_cmd('cscript //nologo "%windir%\\system32\\slmgr.vbs" /xpr', t))
        self.add_button(3, "Ver Versão do Windows",          lambda: run_cmd('powershell -NoProfile -Command "(Get-CimInstance Win32_OperatingSystem) | Format-List Caption,Version,BuildNumber,OSArchitecture"', t, "Info de versão obtida!"))


# ════════════════════════════════════════════════════════
#  SEÇÃO 11: LIMPEZA
# ════════════════════════════════════════════════════════
class CleanPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "CLEAN", GREEN_NEON)
        t = self.terminal
        self.add_button("★", "LIMPEZA PROFUNDA COMPLETA (Recomendado)", self._full_clean, GREEN_NEON)
        self.add_section_label("LIMPEZA INDIVIDUAL")
        self.add_button(1, "Temp do Usuário",      lambda: run_cmd('del /q /s /f "%temp%\\*"', t))
        self.add_button(2, "Temp do Windows",      lambda: run_cmd('del /q /s /f "C:\\Windows\\Temp\\*"', t))
        self.add_button(3, "Prefetch",             lambda: run_cmd('del /q /s /f "C:\\Windows\\Prefetch\\*"', t))
        self.add_button(4, "Lixeira",              lambda: run_cmd('rd /s /q "%systemdrive%\\$Recycle.Bin"', t))
        self.add_button(5, "Cache de Miniaturas",  lambda: run_cmd('del /q /s /f "%localappdata%\\Microsoft\\Windows\\Explorer\\thumbcache*.db"', t))
        self.add_button(6, "Cache DNS",            lambda: run_cmd("ipconfig /flushdns", t))
        self.add_button(7, "Logs de Eventos",      self._clear_logs)
        self.add_button(8, "Cache Windows Update", lambda: run_cmd('del /q /s /f "C:\\Windows\\SoftwareDistribution\\Download\\*"', t))

        self.add_section_label("INTEGRAÇÃO COM WINDOWS")
        self.add_button(9, "Adicionar 'Exterminar' no Botão Direito", self._add_context_menu, CYAN_NEON)
        self.add_button(10, "Remover 'Exterminar' no Botão Direito", self._remove_context_menu, ORANGE_NEON)

    def _add_context_menu(self):
        exe = sys.executable
        if getattr(sys, 'frozen', False):
            cmd_action = f'"{exe}" --context-delete \\"%1\\"'
        else:
            cmd_action = f'"{exe}" "{os.path.abspath(__file__)}" --context-delete \\"%1\\"'
        
        cmd = (
            f'reg add "HKCR\\*\\shell\\DedSecExterminar" /ve /t REG_SZ /d "Aniquilar Forçado (DedSec)" /f & '
            f'reg add "HKCR\\*\\shell\\DedSecExterminar\\command" /ve /t REG_SZ /d "{cmd_action}" /f & '
            f'reg add "HKCR\\Directory\\shell\\DedSecExterminar" /ve /t REG_SZ /d "Aniquilar Forçado (DedSec)" /f & '
            f'reg add "HKCR\\Directory\\shell\\DedSecExterminar\\command" /ve /t REG_SZ /d "{cmd_action}" /f'
        )
        run_cmd(cmd, self.terminal, "Menu de contexto instalado (Aniquilar Forçado)!")

    def _remove_context_menu(self):
        cmd = (
            'reg delete "HKCR\\*\\shell\\DedSecExterminar" /f & '
            'reg delete "HKCR\\Directory\\shell\\DedSecExterminar" /f'
        )
        run_cmd(cmd, self.terminal, "Menu de contexto removido!")

    def _full_clean(self):
        cmd = (
            'del /q /s /f "%temp%\\*" 2>nul & rd /s /q "%temp%" 2>nul & mkdir "%temp%" & '
            'del /q /s /f "C:\\Windows\\Temp\\*" 2>nul & '
            'del /q /s /f "C:\\Windows\\Prefetch\\*" 2>nul & '
            'rd /s /q "%systemdrive%\\$Recycle.Bin" 2>nul & '
            'del /q /s /f "%localappdata%\\Microsoft\\Windows\\Explorer\\thumbcache*.db" 2>nul & '
            'ipconfig /flushdns >nul & '
            'del /q /s /f "C:\\Windows\\SoftwareDistribution\\Download\\*" 2>nul'
        )
        run_cmd(cmd, self.terminal, "LIMPEZA PROFUNDA CONCLUÍDA!")

    def _clear_logs(self):
        run_cmd('powershell -NoProfile -Command "Get-WinEvent -ListLog * -ErrorAction SilentlyContinue | ForEach-Object { try { [System.Diagnostics.Eventing.Reader.EventLogSession]::GlobalSession.ClearLog($_.LogName) } catch {} }; Write-Host \'Logs limpos.\'"', self.terminal, "Logs limpos!")


# ════════════════════════════════════════════════════════
#  SEÇÃO 12: KIT PC NOVO
# ════════════════════════════════════════════════════════
class KitPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "KIT", GREEN_NEON)
        t = self.terminal
        info_text = (
            "  Instala tudo que um PC novo precisa de uma vez.\n"
            "  • WebView2 + VC++ x64/x86 + DirectX + .NET 8\n"
            "  • Chrome + 7-Zip + AnyDesk\n"
            "  • VLC + Notepad++ + Acrobat Reader\n"
            "  • Discord + WhatsApp\n"
            "  Tempo estimado: 5–15 minutos."
        )
        info = ctk.CTkLabel(self.btn_frame, text=info_text, font=("Courier New", 11), text_color=WHITE_DIM, anchor="w", justify="left")
        info.pack(fill="x", pady=(0, 12))
        self.add_button("★", "▶  INICIAR KIT PC NOVO", self._run_kit, GREEN_NEON)

    def _run_kit(self):
        if not messagebox.askyesno("Kit PC Novo", "Instalar TODOS os programas essenciais?\n\nIsso pode levar alguns minutos."):
            return
        pkgs = [
            "Microsoft.EdgeWebView2Runtime","Microsoft.VCRedist.2015+.x64","Microsoft.VCRedist.2015+.x86",
            "Microsoft.DirectX","Microsoft.DotNet.DesktopRuntime.8","Google.Chrome","7zip.7zip",
            "AnyDeskSoftwareGmbH.AnyDesk","VideoLAN.VLC","Notepad++.Notepad++",
            "Adobe.Acrobat.Reader.64-bit","Discord.Discord","WhatsApp.WhatsApp",
        ]
        cmd = " & ".join([f'winget install --id {p} -e --silent --accept-source-agreements --accept-package-agreements' for p in pkgs])
        run_cmd(cmd, self.terminal, f"KIT PC NOVO INSTALADO! — By {USER_NAME}")


# ════════════════════════════════════════════════════════
#  PAINEL PRINCIPAL — DedSec skull → WE ARE COMING
# ════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════
#  SEÇÃO K: KALI LINUX TOOLS
# ════════════════════════════════════════════════════════
class KaliPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "KALI", RED_NEON)
        t = self.terminal

        # ── RECONHECIMENTO / IP ─────────────────────────────────────
        self.add_section_label("RECONHECIMENTO / IP")
        self.add_button(1,  "IP Tracker — Localizar IP (público ou qualquer IP)", self._ip_tracker,  CYAN_NEON)
        self.add_button(2,  "Whois — Consultar domínio/IP via Resolve-DnsName",   self._whois,       CYAN_NEON)
        self.add_button(3,  "NSLookup — Resolver DNS",                            self._nslookup,    CYAN_NEON)
        self.add_button(4,  "Traceroute para destino",                             self._traceroute,  CYAN_NEON)
        self.add_button(5,  "Ver conexões ativas (netstat)",                       lambda: run_cmd("netstat -ano", t))
        self.add_button(6,  "Tabela ARP — Dispositivos na rede",                  lambda: run_cmd("arp -a", t))
        self.add_button(7,  "IP e interfaces (ipconfig /all)",                     lambda: run_cmd("ipconfig /all", t))
        self.add_button(8,  "MAC Address da máquina",                             lambda: run_cmd("getmac /v /fo table", t))

        # ── VARREDURA DE REDE ───────────────────────────────────────
        self.add_section_label("VARREDURA DE REDE (requer PowerShell)")
        self.add_button(9,  "Ping Sweep — Hosts ativos na rede local",    self._ping_sweep,  YELLOW_NEON)
        self.add_button(10, "Port Scan básico (PowerShell nativo)",        self._port_scan,   YELLOW_NEON)

        # ── INFORMAÇÕES DO SISTEMA ──────────────────────────────────
        self.add_section_label("INFORMAÇÕES DO SISTEMA")
        self.add_button(11, "Processos em execução",                       lambda: run_cmd("tasklist /v", t))
        self.add_button(12, "Serviços do sistema",                         lambda: run_cmd("sc query type= all state= all", t))
        self.add_button(13, "Patches instalados (KB)",                     lambda: run_cmd('powershell -NoProfile -Command "Get-HotFix | Sort-Object InstalledOn -Descending -ErrorAction SilentlyContinue | Format-Table HotFixID,Description,InstalledOn -AutoSize"', t))
        self.add_button(14, "Usuários e grupos locais",                    lambda: run_cmd("net user & net localgroup", t))
        self.add_button(15, "Variáveis de ambiente",                       lambda: run_cmd("set", t))

        # ── ANÁLISE DE LOGS ─────────────────────────────────────────
        self.add_section_label("ANÁLISE DE LOGS")
        self.add_button(16, "Conexões TCP estabelecidas",                  lambda: run_cmd('netstat -an | findstr ESTABLISHED', t))
        self.add_button(17, "Logs de segurança (últimos 20)",              lambda: run_cmd('powershell -Command "Get-EventLog -LogName Security -Newest 20 | Format-List"', t))
        self.add_button(18, "Erros críticos do sistema (últimos 20)",      lambda: run_cmd('powershell -Command "Get-EventLog -LogName System -EntryType Error,Warning -Newest 20 | Format-List"', t))
        self.add_button(19, "Compartilhamentos de rede ativos",            lambda: run_cmd("net share", t))

        # ── INSTALAR FERRAMENTAS ────────────────────────────────────
        self.add_section_label("INSTALAR FERRAMENTAS (via winget)")
        self.add_button(20, "Instalar Nmap",                               lambda: run_winget("Insecure.Nmap",                   "Nmap",       t), PURPLE_NEON)
        self.add_button(21, "Instalar Wireshark",                          lambda: run_winget("WiresharkFoundation.Wireshark",   "Wireshark",  t), PURPLE_NEON)
        self.add_button(22, "Instalar PuTTY (SSH client)",                 lambda: run_winget("PuTTY.PuTTY",                     "PuTTY",      t), PURPLE_NEON)
        self.add_button(23, "Instalar WinSCP (SFTP/FTP)",                  lambda: run_winget("WinSCP.WinSCP",                   "WinSCP",     t), PURPLE_NEON)

        # ── WSL2 / KALI NATIVO ──────────────────────────────────────
        self.add_section_label("WSL2 — Kali Linux Nativo")
        self.add_button(24, "Ativar WSL2 (reiniciar depois)",              self._enable_wsl,       GREEN_NEON)
        self.add_button(25, "Instalar Kali Linux no WSL2",                 self._install_kali_wsl, GREEN_NEON)
        self.add_button(26, "Visualizar Senhas Wi-Fi Salvas",              self._wifi_passwords,   YELLOW_NEON)
        self.add_button(27, "★ Scanner de Rede (Inventory)",               self._network_inventory, CYAN_NEON)

    def _network_inventory(self):
        """Mapeia dispositivos na rede local com IP, MAC e Fabricante aproximado."""
        cmd = (
            'powershell -NoProfile -Command "'
            'Write-Host \\"=== SCANNER DE REDE (INVENTORY) ===\\" -ForegroundColor Green;'
            'Write-Host \\"[*] Escaneando rede local (pode levar 10-20s)...\\" -ForegroundColor Gray;'
            '$results = arp -a | Select-String \\"dynamic|estatico\\";'
            'foreach ($line in $results) {'
            '  $parts = $line.ToString().Trim() -split \'\\s+\';'
            '  if ($parts.Length -ge 2) {'
            '    $ip = $parts[0]; $mac = $parts[1].ToUpper();'
            '    $vendor = \\"Desconhecido\\";'
            '    if ($mac -match \'^00-05-02|^00-1C-B3|^00-25-00|^D0-D2-B0|^F0-B0-52\') { $vendor = \\"Apple Inc.\\" }'
            '    elseif ($mac -match \'^28-11-A5|^00-15-B9|^D0-D2-B0|^38-2D-D1\') { $vendor = \\"Samsung\\" }'
            '    elseif ($mac -match \'^BC-5F-F4|^A4-75-B9|^00-E0-4C\') { $vendor = \\"TP-Link / Realtek\\" }'
            '    elseif ($mac -match \'^00-15-5D\') { $vendor = \\"Microsoft (Hyper-V)\\" }'
            '    elseif ($mac -match \'^00-0C-29|^00-05-69\') { $vendor = \\"VMware\\" }'
            '    elseif ($mac -match \'^DC-A6-32|^B8-27-EB\') { $vendor = \\"Raspberry Pi\\" }'
            '    elseif ($mac -match \'^F8-FF-C2|^48-A9-8A|^00-12-70\') { $vendor = \\"Intel / Dell / HP\\" }'
            '    Write-Host \\"  [+] IP: $ip  |  MAC: $mac  |  Fab: $vendor\\" -ForegroundColor Cyan'
            '  }'
            '}'
            'Write-Host \\"Scan concluido!\\" -ForegroundColor Green'
            '"'
        )
        run_cmd(cmd, self.terminal, "Inventário de Rede concluído!")

    def _wifi_passwords(self):
        cmd = (
            'powershell -NoProfile -Command "'
            'Write-Host \\"=== SENHAS WI-FI SALVAS ===\\" -ForegroundColor Green;'
            '$profiles = netsh wlan show profiles | Select-String \\"All User Profile\\" | ForEach-Object { $_.ToString().Split(\\":\\")[1].Trim() };'
            'foreach ($p in $profiles) {'
            '  $pass = netsh wlan show profile name=\\"$p\\" key=clear | Select-String \\"Key Content\\" | ForEach-Object { $_.ToString().Split(\\":\\")[1].Trim() };'
            '  if ($pass) { Write-Host \\"  [+] SSID: $p  -->  Senha: $pass\\" -ForegroundColor Cyan }'
            '  else { Write-Host \\"  [!] SSID: $p  -->  (Sem senha / Aberta)\\" -ForegroundColor Gray }'
            '}"'
        )
        run_cmd(cmd, self.terminal, "Coleta de senhas concluída!")

    def _ip_tracker(self):
        popup = ctk.CTkInputDialog(
            text="IP para rastrear (vazio = seu próprio IP público):",
            title="IP Tracker"
        )
        target = (popup.get_input() or "").strip()
        ps_script = r"""
$ErrorActionPreference = 'SilentlyContinue'
$target = '""" + target.replace("'", "''") + r"""'
if (-not $target) {
    try { $target = (Invoke-RestMethod -Uri 'https://api.ipify.org' -TimeoutSec 5).Trim() }
    catch { try { $target = (Invoke-RestMethod -Uri 'https://ifconfig.me/ip' -TimeoutSec 5).Trim() }
            catch { Write-Host '[ERRO] Nao foi possivel obter IP publico.' -ForegroundColor Red; exit } }
}
Write-Host ''
Write-Host "=== IP TRACKER: $target ===" -ForegroundColor Green
Write-Host ('=' * 45) -ForegroundColor DarkGreen
Write-Host ''
$url = "http://ip-api.com/json/$target`?fields=status,message,country,regionName,city,zip,lat,lon,isp,org,as,query"
try {
    $r = Invoke-RestMethod -Uri $url -TimeoutSec 8
    if ($r.status -eq 'success') {
        Write-Host "  IP         : $($r.query)"      -ForegroundColor Cyan
        Write-Host "  Pais       : $($r.country)"    -ForegroundColor White
        Write-Host "  Estado     : $($r.regionName)" -ForegroundColor White
        Write-Host "  Cidade     : $($r.city)"       -ForegroundColor White
        Write-Host "  CEP/ZIP    : $($r.zip)"        -ForegroundColor White
        Write-Host "  Lat / Lon  : $($r.lat) / $($r.lon)" -ForegroundColor Yellow
        Write-Host "  ISP        : $($r.isp)"        -ForegroundColor Cyan
        Write-Host "  Org        : $($r.org)"        -ForegroundColor Cyan
        Write-Host "  AS         : $($r.as)"         -ForegroundColor DarkCyan
        Write-Host ''
        Write-Host "  Maps : https://maps.google.com/?q=$($r.lat),$($r.lon)" -ForegroundColor Green
    } else { Write-Host "[ERRO] $($r.message)" -ForegroundColor Red }
} catch { Write-Host '[ERRO] Falha na requisicao.' -ForegroundColor Red }
Write-Host ''
"""
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".ps1", delete=False, mode="w", encoding="utf-8")
        tmp.write(ps_script); tmp.close()
        run_cmd(f'powershell -ExecutionPolicy Bypass -File "{tmp.name}"', self.terminal, "IP Tracker concluído!")
        self.after(15000, lambda p=tmp.name: os.unlink(p) if os.path.exists(p) else None)

    def _whois(self):
        popup = ctk.CTkInputDialog(text="Domínio para Whois:", title="Whois")
        target = (popup.get_input() or "").strip()
        if target:
            cmd = (
                f'powershell -Command "'
                f'Write-Host \\"=== WHOIS: {target} ===\\" -ForegroundColor Green;'
                f'try {{ $r = Invoke-RestMethod -Uri \\"https://rdap.org/domain/{target}\\" -ErrorAction Stop;'
                f'  Write-Host \\"  Registrar : $($r.port43)\\" -ForegroundColor Cyan;'
                f'  Write-Host \\"  Eventos   : \\" -ForegroundColor White;'
                f'  foreach($ev in $r.events){{ Write-Host \\"    - $($ev.eventAction): $($ev.eventDate)\\" }}'
                f'}} catch {{ Resolve-DnsName {target} | Format-List }}'
                f'"'
            )
            run_cmd(cmd, self.terminal, f"Whois de {target} concluído!")

    def _nslookup(self):
        popup = ctk.CTkInputDialog(text="Domínio para NSLookup:", title="NSLookup")
        target = popup.get_input()
        if target:
            run_cmd(f"nslookup {target}", self.terminal, f"NSLookup de {target} concluído!")

    def _traceroute(self):
        popup = ctk.CTkInputDialog(text="Destino (IP ou domínio):", title="Traceroute")
        target = popup.get_input()
        if target:
            run_cmd(f"tracert -d {target}", self.terminal, f"Traceroute para {target} concluído!")

    def _ping_sweep(self):
        popup = ctk.CTkInputDialog(text="Rede base (ex: 192.168.1):", title="Ping Sweep")
        base = popup.get_input()
        if base:
            cmd = (
                f'powershell -Command "'
                f'Write-Host \\"=== PING SWEEP {base}.0/24 ===" -ForegroundColor Green;'
                f'1..254 | ForEach-Object {{'
                f'  $ip = \\"{base}.$_\\";'
                f'  if (Test-Connection -ComputerName $ip -Count 1 -Quiet -TimeoutSeconds 1) {{'
                f'    Write-Host \\"[+] ATIVO: $ip\\" -ForegroundColor Cyan'
                f'  }}'
                f'}};'
                f'Write-Host \\"Scan concluido!\\" -ForegroundColor Green'
                f'"'
            )
            run_cmd(cmd, self.terminal, "Ping Sweep concluído!")

    def _port_scan(self):
        popup = ctk.CTkInputDialog(text="IP/Host para scan de portas:", title="Port Scan")
        target = popup.get_input()
        if target:
            cmd = (
                f'powershell -Command "'
                f'$target = \\"{target}\\";'
                f'$ports = @(21,22,23,25,53,80,110,135,139,143,443,445,3306,3389,8080,8443);'
                f'Write-Host \\"=== PORT SCAN: $target ===" -ForegroundColor Green;'
                f'foreach ($port in $ports) {{'
                f'  $tcp = New-Object System.Net.Sockets.TcpClient;'
                f'  $conn = $tcp.BeginConnect($target,$port,$null,$null);'
                f'  $wait = $conn.AsyncWaitHandle.WaitOne(500,$false);'
                f'  if ($wait) {{ try {{ $tcp.EndConnect($conn); Write-Host \\"[ABERTA] $port\\" -ForegroundColor Cyan }} catch {{}} }}'
                f'  else {{ Write-Host \\"[fechada] $port\\" -ForegroundColor DarkGray }};'
                f'  try {{ $tcp.Close() }} catch {{}}'
                f'}}"'
            )
            run_cmd(cmd, self.terminal, "Port Scan concluído!")

    def _enable_wsl(self):
        run_cmd(
            'powershell -Command "dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart; '
            'dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart; '
            'wsl --set-default-version 2"',
            self.terminal, "WSL2 ativado! Reinicie o PC."
        )

    def _install_kali_wsl(self):
        run_cmd('wsl --install -d kali-linux', self.terminal, "Kali Linux instalado no WSL2!")




# ════════════════════════════════════════════════════════
#  NOVO — BACKUP RÁPIDO
# ════════════════════════════════════════════════════════
class CustomScriptsPanel(BasePanel):
    """Painel para executar scripts de terceiros de forma rápida."""
    def __init__(self, master, **kwargs):
        super().__init__(master, "MEUS SCRIPTS (DYNAMIC)", **kwargs)
        self.scripts_path = os.path.join(os.getcwd(), "meus_scripts")
        if not os.path.exists(self.scripts_path):
            os.makedirs(self.scripts_path)
            
        desc = (
            "Coloque seus arquivos (.bat, .ps1, .vbs, .exe, .py) na pasta 'meus_scripts'.\n"
            "O sistema fará o auto-scan e permitirá executá-los com 1-clique."
        )
        ctk.CTkLabel(self, text=desc, font=("Courier New", 12), text_color=GRAY_DIM).pack(pady=10)
        
        # Area de lista
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG_PANEL, border_color=GRAY_DIM, border_width=1)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refresh_btn = DedSecButton(self, text="◈ ATUALIZAR LISTA", command=self.refresh)
        self.refresh_btn.pack(pady=10)
        
        self.refresh()

    def refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()
            
        try:
            files = [f for f in os.listdir(self.scripts_path) if f.lower().endswith(('.bat', '.ps1', '.vbs', '.exe', '.py'))]
        except:
            files = []

        if not files:
            ctk.CTkLabel(self.scroll, text="─ NENHUM SCRIPT ENCONTRADO ─", font=("Courier New", 14), text_color=RED_NEON).pack(pady=40)
            return
            
        for f in files:
            frame = ctk.CTkFrame(self.scroll, fg_color=BG_DARK, border_color="#333", border_width=1)
            frame.pack(fill="x", pady=4, padx=5)
            
            ctk.CTkLabel(frame, text=f"◈ {f}", font=("Courier New", 13, "bold"), text_color=CYAN_NEON).pack(side="left", padx=15, pady=8)
            
            run_btn = ctk.CTkButton(frame, text="EXECUTAR", width=100, height=28, 
                                    fg_color="transparent", border_color=GREEN_NEON, border_width=1,
                                    text_color=GREEN_NEON, hover_color="#002200",
                                    command=lambda name=f: self.run_script(name))
            run_btn.pack(side="right", padx=15)

    def run_script(self, filename):
        full_path = os.path.normpath(os.path.join(self.scripts_path, filename))
        try:
            if filename.lower().endswith('.ps1'):
                subprocess.Popen(['powershell', '-ExecutionPolicy', 'Bypass', '-File', full_path], shell=True)
            else:
                os.startfile(full_path)
            # Log no Dossiê
            HistoryManager.save_note(f"Executou script customizado: {filename}")
            messagebox.showinfo("DEDSEC", f"Iniciando: {filename}")
        except Exception as e:
            messagebox.showerror("ERRO", f"Falha ao executar:\n{e}")

class BackupPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "BACKUP", GREEN_NEON)
        t = self.terminal

        self.add_section_label("BACKUP DE PASTAS IMPORTANTES")
        self.add_button(1,  "Backup: Desktop → Documentos\\Backup",     self._bk_desktop,   GREEN_NEON)
        self.add_button(2,  "Backup: Documentos → Documentos\\Backup",  self._bk_docs,      GREEN_NEON)
        self.add_button(3,  "Backup: Imagens → Documentos\\Backup",     self._bk_pictures,  GREEN_NEON)
        self.add_button(4,  "Backup: Downloads → Documentos\\Backup",   self._bk_downloads, GREEN_NEON)
        self.add_button(5,  "★  BACKUP COMPLETO (todos acima)",          self._bk_all,       CYAN_NEON)

        self.add_section_label("BACKUP PARA PENDRIVE / PASTA EXTERNA")
        self.add_button(6,  "Backup Desktop → Pendrive (escolher drive)", lambda: self._bk_to_drive("Desktop"))
        self.add_button(7,  "Backup Documentos → Pendrive",               lambda: self._bk_to_drive("Documents"))
        self.add_button(8,  "Backup Completo → Pendrive",                 self._bk_all_pendrive)

        self.add_section_label("RESTAURAR / VERIFICAR")
        self.add_button(9,  "Abrir pasta de backup",    self._open_backup_folder)
        self.add_button(10, "Ver tamanho do backup",    self._check_size)
        self.add_button(11, "Histórico de versões (Windows Backup)", lambda: run_cmd("control /name Microsoft.BackupAndRestoreWindows", t))

    def _dest(self):
        return os.path.join(os.environ.get("USERPROFILE","C:\\Users\\Default"), "Documents", "Backup_DEDSEC")

    def _bk_folder(self, src_name):
        src  = os.path.join(os.environ.get("USERPROFILE","C:\\"), src_name)
        dest = os.path.join(self._dest(), src_name)
        run_cmd(f'robocopy "{src}" "{dest}" /E /COPYALL /R:2 /W:3 /NP', self.terminal, f"Backup de {src_name} concluído!")

    def _bk_desktop(self):   self._bk_folder("Desktop")
    def _bk_docs(self):      self._bk_folder("Documents")
    def _bk_pictures(self):  self._bk_folder("Pictures")
    def _bk_downloads(self): self._bk_folder("Downloads")

    def _bk_all(self):
        up = os.environ.get("USERPROFILE","C:\\")
        dest = self._dest()
        cmd = " & ".join([
            f'robocopy "{os.path.join(up,f)}" "{os.path.join(dest,f)}" /E /COPYALL /R:2 /W:3 /NP'
            for f in ["Desktop","Documents","Pictures","Downloads"]
        ])
        run_cmd(cmd, self.terminal, "BACKUP COMPLETO CONCLUÍDO!")

    def _bk_to_drive(self, folder_name):
        popup = ctk.CTkInputDialog(text="Letra do drive (ex: E, F, G):", title="Backup para Pendrive")
        drive = (popup.get_input() or "").strip().upper().replace(":", "")
        if not drive:
            return
        src  = os.path.join(os.environ.get("USERPROFILE","C:\\"), folder_name)
        dest = f"{drive}:\\Backup_DEDSEC\\{folder_name}"
        run_cmd(f'robocopy "{src}" "{dest}" /E /COPYALL /R:2 /W:3 /NP', self.terminal, f"Backup para {drive}: concluído!")

    def _bk_all_pendrive(self):
        popup = ctk.CTkInputDialog(text="Letra do drive (ex: E, F, G):", title="Backup Completo → Pendrive")
        drive = (popup.get_input() or "").strip().upper().replace(":", "")
        if not drive:
            return
        up = os.environ.get("USERPROFILE","C:\\")
        cmd = " & ".join([
            f'robocopy "{os.path.join(up,f)}" "{drive}:\\Backup_DEDSEC\\{f}" /E /COPYALL /R:2 /W:3 /NP'
            for f in ["Desktop","Documents","Pictures","Downloads"]
        ])
        run_cmd(cmd, self.terminal, f"BACKUP COMPLETO → {drive}: CONCLUÍDO!")

    def _open_backup_folder(self):
        dest = self._dest()
        os.makedirs(dest, exist_ok=True)
        run_cmd(f'explorer "{dest}"', self.terminal)

    def _check_size(self):
        dest = self._dest()
        run_cmd(
            f'powershell -NoProfile -Command "if(Test-Path \'{dest}\'){{$s=(Get-ChildItem \'{dest}\' -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; Write-Host (\'Tamanho: \'+[math]::Round($s/1MB,2)+\' MB (\'+[math]::Round($s/1GB,2)+\' GB)\') -ForegroundColor Cyan}}else{{Write-Host \'Pasta de backup nao encontrada.\' -ForegroundColor Yellow}}"',
            self.terminal, "Verificação concluída!"
        )


# ════════════════════════════════════════════════════════
#  NOVO — GERENCIADOR DE PROCESSOS
# ════════════════════════════════════════════════════════
class ProcessPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "PROCESSOS", ORANGE_NEON)
        t = self.terminal

        self.add_section_label("VISUALIZAR PROCESSOS")
        self.add_button(1,  "Top 20 processos (RAM)",       self._top_ram)
        self.add_button(2,  "Top 20 processos (CPU)",       self._top_cpu)
        self.add_button(3,  "Todos os processos + PID",     lambda: run_cmd("tasklist /v /fo table", t))
        self.add_button(4,  "Processos de rede (porta)",    lambda: run_cmd("netstat -ano", t))
        self.add_button(5,  "Inicialização automática",     lambda: run_cmd('powershell -NoProfile -Command "Get-CimInstance Win32_StartupCommand | Format-Table Name,Command,Location -AutoSize"', t))

        self.add_section_label("ENCERRAR PROCESSO")
        self.add_button(6,  "Encerrar por NOME (digitar)",  self._kill_by_name)
        self.add_button(7,  "Encerrar por PID (digitar)",   self._kill_by_pid)
        self.add_button(8,  "Encerrar Chrome (todos)",      lambda: run_cmd("taskkill /F /IM chrome.exe /T", t, "Chrome encerrado!"))
        self.add_button(9,  "Encerrar Teams",               lambda: run_cmd("taskkill /F /IM Teams.exe /T", t, "Teams encerrado!"))
        self.add_button(10, "Encerrar OneDrive",            lambda: run_cmd("taskkill /F /IM OneDrive.exe /T", t, "OneDrive encerrado!"))

        self.add_section_label("SERVIÇOS")
        self.add_button(11, "Listar serviços rodando",      lambda: run_cmd("sc query type= all state= running", t))
        self.add_button(12, "Parar serviço (digitar nome)", self._stop_service)
        self.add_button(13, "Iniciar serviço (digitar nome)",self._start_service)
        self.add_button(14, "Desativar serviço da inicialização", self._disable_service)
        self.add_button(15, "Abrir Gerenciador de Serviços", lambda: run_cmd("services.msc", t))

        self.add_section_label("PERFORMANCE")
        self.add_button(16, "Uso de CPU e RAM agora",       self._perf_now)
        self.add_button(17, "Tempo ligado do sistema",      lambda: run_cmd('powershell -NoProfile -Command "(Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime | Format-Table Days,Hours,Minutes"', t))
        self.add_button(18, "Abrir Gerenciador de Tarefas", lambda: run_cmd("taskmgr", t))

    def _top_ram(self):
        run_cmd(
            'powershell -NoProfile -Command "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 20 | Format-Table Name,Id,@{N=\'RAM(MB)\';E={[math]::Round($_.WorkingSet64/1MB,1)}},CPU -AutoSize"',
            self.terminal, "OK"
        )

    def _top_cpu(self):
        run_cmd(
            'powershell -NoProfile -Command "Get-Process | Sort-Object CPU -Descending | Select-Object -First 20 | Format-Table Name,Id,@{N=\'RAM(MB)\';E={[math]::Round($_.WorkingSet64/1MB,1)}},CPU -AutoSize"',
            self.terminal, "OK"
        )

    def _kill_by_name(self):
        popup = ctk.CTkInputDialog(text="Nome do processo (ex: notepad.exe):", title="Encerrar Processo")
        name = (popup.get_input() or "").strip()
        if name:
            run_cmd(f'taskkill /F /IM "{name}" /T', self.terminal, f"{name} encerrado!")

    def _kill_by_pid(self):
        popup = ctk.CTkInputDialog(text="PID do processo:", title="Encerrar por PID")
        pid = (popup.get_input() or "").strip()
        if pid.isdigit():
            run_cmd(f'taskkill /F /PID {pid}', self.terminal, f"PID {pid} encerrado!")

    def _stop_service(self):
        popup = ctk.CTkInputDialog(text="Nome do serviço:", title="Parar Serviço")
        svc = (popup.get_input() or "").strip()
        if svc:
            run_cmd(f'net stop "{svc}"', self.terminal, f"{svc} parado!")

    def _start_service(self):
        popup = ctk.CTkInputDialog(text="Nome do serviço:", title="Iniciar Serviço")
        svc = (popup.get_input() or "").strip()
        if svc:
            run_cmd(f'net start "{svc}"', self.terminal, f"{svc} iniciado!")

    def _disable_service(self):
        popup = ctk.CTkInputDialog(text="Nome do serviço para desativar da inicialização:", title="Desativar Serviço")
        svc = (popup.get_input() or "").strip()
        if svc:
            if messagebox.askyesno("Confirmar", f"Desativar '{svc}' da inicialização?\nPode ser reativado depois."):
                run_cmd(f'sc config "{svc}" start= disabled', self.terminal, f"{svc} desativado!")

    def _perf_now(self):
        run_cmd(
            'powershell -NoProfile -Command "'
            '$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average;'
            '$os = Get-CimInstance Win32_OperatingSystem;'
            '$ramTotal = [math]::Round($os.TotalVisibleMemorySize/1MB,2);'
            '$ramFree  = [math]::Round($os.FreePhysicalMemory/1MB,2);'
            '$ramUsed  = [math]::Round($ramTotal-$ramFree,2);'
            '$ramPct   = [math]::Round(($ramUsed/$ramTotal)*100,1);'
            'Write-Host \\"CPU: $cpu%\\" -ForegroundColor Cyan;'
            'Write-Host \\"RAM: $ramUsed GB / $ramTotal GB ($ramPct% usado)\\" -ForegroundColor Yellow"',
            self.terminal, "OK"
        )


# ════════════════════════════════════════════════════════
#  NOVO — VELOCIDADE & CONECTIVIDADE
# ════════════════════════════════════════════════════════
class SpeedPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "VELOCIDADE", CYAN_NEON)
        t = self.terminal

        self.add_section_label("TESTE DE VELOCIDADE")
        self.add_button(1,  "Instalar speedtest-cli",                   lambda: run_cmd("python -m pip install speedtest-cli --quiet", t, "speedtest-cli instalado!"), GREEN_NEON)
        self.add_button(2,  "★ Rodar Speed Test (download/upload/ping)", self._run_speedtest, CYAN_NEON)
        self.add_button(3,  "Abrir Speedtest no navegador",             lambda: run_cmd("start https://www.speedtest.net", t))
        self.add_button(4,  "Abrir Fast.com (Netflix)",                  lambda: run_cmd("start https://fast.com", t))

        self.add_section_label("PING — LATÊNCIA")
        self.add_button(5,  "Ping Google (8.8.8.8)",             lambda: run_cmd("ping -n 10 8.8.8.8", t))
        self.add_button(6,  "Ping Cloudflare (1.1.1.1)",         lambda: run_cmd("ping -n 10 1.1.1.1", t))
        self.add_button(7,  "Ping Servidor da operadora (GW)",   self._ping_gateway)
        self.add_button(8,  "Ping completo múltiplos destinos ★",self._ping_all, GREEN_NEON)

        self.add_section_label("DIAGNÓSTICO DE REDE")
        self.add_button(9,  "Traceroute → Google",               lambda: run_cmd("tracert -h 15 8.8.8.8", t))
        self.add_button(10, "Ver IP público atual",              self._public_ip)
        self.add_button(11, "Verificar conexão de internet",     self._check_internet)
        self.add_button(12, "Pacotes perdidos (ping longo)",     lambda: run_cmd("ping -n 50 8.8.8.8", t))
        self.add_button(13, "Estatísticas de rede (netstat -e)", lambda: run_cmd("netstat -e", t))
        self.add_button(14, "Informações Wi-Fi detalhadas",      lambda: run_cmd("netsh wlan show all", t))
        self.add_button(15, "Redes Wi-Fi disponíveis",           lambda: run_cmd("netsh wlan show networks mode=Bssid", t))

    def _run_speedtest(self):
        cmd = (
            'python -c "import speedtest; s=speedtest.Speedtest(); s.get_best_server(); '
            'print(\'[*] Testando Download...\'); d=s.download()/1e6; '
            'print(\'[*] Testando Upload...\'); u=s.upload()/1e6; '
            'p=s.results.ping; '
            'print(f\'[✓] Download : {d:.2f} Mbps\'); '
            'print(f\'[✓] Upload   : {u:.2f} Mbps\'); '
            'print(f\'[✓] Ping     : {p:.1f} ms\')" '
            '2>nul || python -m speedtest_cli 2>nul || echo [!] Erro: speedtest-cli nao instalado. Use o botao 1.'
        )
        run_cmd(cmd, self.terminal, "Speed Test finalizado!")

    def _ping_gateway(self):
        run_cmd(
            'for /f "tokens=3" %i in (\'route print 0.0.0.0 ^| findstr "0.0.0.0 0.0.0.0"\') do ping -n 10 %i',
            self.terminal, "Ping concluído!"
        )

    def _ping_all(self):
        run_cmd(
            'echo === GOOGLE (8.8.8.8) === & ping -n 5 8.8.8.8 | findstr "ms tempo" & '
            'echo === CLOUDFLARE (1.1.1.1) === & ping -n 5 1.1.1.1 | findstr "ms tempo" & '
            'echo === MICROSOFT (13.107.4.52) === & ping -n 5 13.107.4.52 | findstr "ms tempo" & '
            'echo === AMAZON (54.239.28.85) === & ping -n 5 54.239.28.85 | findstr "ms tempo"',
            self.terminal, "Ping múltiplo concluído!"
        )

    def _public_ip(self):
        run_cmd(
            'powershell -NoProfile -Command "try{$ip=(Invoke-WebRequest -Uri \'https://api.ipify.org\' -UseBasicParsing -TimeoutSec 5).Content.Trim(); Write-Host \"IP Público: $ip\" -ForegroundColor Cyan}catch{Write-Host \'Falha ao obter IP público\' -ForegroundColor Red}"',
            self.terminal, "OK"
        )

    def _check_internet(self):
        run_cmd(
            'powershell -NoProfile -Command "'
            '$hosts=@(\'8.8.8.8\',\'1.1.1.1\',\'google.com\');'
            'foreach($h in $hosts){'
            '$r=Test-Connection $h -Count 2 -Quiet -ErrorAction SilentlyContinue;'
            '$s=if($r){\'OK\'}else{\'FALHOU\'};'
            'Write-Host \"$h : $s\"'
            '}"',
            self.terminal, "Verificação concluída!"
        )


# ════════════════════════════════════════════════════════
#  NOVO — GERENCIAR IMPRESSORAS E FILA
# ════════════════════════════════════════════════════════
class PrinterPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "IMPRESSORAS", YELLOW_NEON)
        t = self.terminal

        self.add_section_label("VISUALIZAR")
        self.add_button(1, "Listar impressoras instaladas",     self._list_printers)
        self.add_button(2, "Ver fila de impressão",             self._show_queue)
        self.add_button(3, "Impressora padrão",                 self._default_printer)

        self.add_section_label("LIMPAR FILA")
        self.add_button(4, "★ LIMPAR fila de impressão (tudo)", self._clear_queue, RED_NEON)
        self.add_button(5, "Reiniciar serviço Print Spooler",   self._restart_spooler, ORANGE_NEON)
        self.add_button(6, "Abrir Gerenciador de Impressão",    lambda: run_cmd("printmanagement.msc", t))

        self.add_section_label("DRIVERS E CONFIGURAÇÕES")
        self.add_button(7,  "Listar drivers de impressora",     lambda: run_cmd('powershell -NoProfile -Command "Get-PrinterDriver | Format-Table Name,PrinterEnvironment -AutoSize"', t))
        self.add_button(8,  "Adicionar porta TCP/IP (IP fixa)", self._add_tcp_port)
        self.add_button(9,  "Remover impressora (por nome)",    self._remove_printer)
        self.add_button(10, "Instalar drivers automático (Windows Update)", lambda: run_cmd('powershell -NoProfile -Command "Install-Module -Name PrintManagement -Force -ErrorAction SilentlyContinue; Add-PrinterDriver -Name \'Microsoft PS Class Driver\'"', t))
        self.add_button(11, "Abrir Dispositivos e Impressoras", lambda: run_cmd("control printers", t))
        self.add_button(12, "Testar impressão (página de teste)", self._test_print)

    def _list_printers(self):
        run_cmd(
            'powershell -NoProfile -Command "Get-Printer | Format-Table Name,DriverName,PortName,PrinterStatus -AutoSize"',
            self.terminal, "OK"
        )

    def _show_queue(self):
        run_cmd(
            'powershell -NoProfile -Command "Get-PrintJob -PrinterName (Get-Printer | Select-Object -First 1 -ExpandProperty Name) -ErrorAction SilentlyContinue | Format-Table DocumentName,JobStatus,TotalPages -AutoSize; Get-Printer | ForEach-Object { $jobs = Get-PrintJob -PrinterName $_.Name -ErrorAction SilentlyContinue; if($jobs){Write-Host \\"Fila: $($_.Name)\\"; $jobs | Format-Table DocumentName,JobStatus -AutoSize}}"',
            self.terminal, "OK"
        )

    def _default_printer(self):
        run_cmd(
            'powershell -NoProfile -Command "(Get-CimInstance Win32_Printer | Where-Object {$_.Default -eq $true}).Name"',
            self.terminal, "OK"
        )

    def _clear_queue(self):
        if messagebox.askyesno("Limpar Fila", "Isso cancela TODOS os trabalhos de impressão.\n\nConfirma?"):
            run_cmd(
                'net stop spooler & '
                'del /Q /F /S "%systemroot%\\system32\\spool\\PRINTERS\\*" & '
                'net start spooler',
                self.terminal, "Fila de impressão limpa!"
            )

    def _restart_spooler(self):
        run_cmd(
            'net stop spooler & net start spooler',
            self.terminal, "Print Spooler reiniciado!"
        )

    def _add_tcp_port(self):
        popup = ctk.CTkInputDialog(text="IP da impressora (ex: 192.168.1.100):", title="Adicionar Porta TCP/IP")
        ip = (popup.get_input() or "").strip()
        if ip:
            run_cmd(
                f'powershell -NoProfile -Command "Add-PrinterPort -Name \'IP_{ip}\' -PrinterHostAddress \'{ip}\'; Write-Host \'Porta IP_{ip} criada.\' -ForegroundColor Green"',
                self.terminal, f"Porta TCP/IP para {ip} criada!"
            )

    def _remove_printer(self):
        popup = ctk.CTkInputDialog(text="Nome exato da impressora:", title="Remover Impressora")
        name = (popup.get_input() or "").strip()
        if name:
            if messagebox.askyesno("Remover", f"Remover '{name}'?"):
                run_cmd(
                    f'powershell -NoProfile -Command "Remove-Printer -Name \'{name}\'; Write-Host \'Impressora removida.\' -ForegroundColor Yellow"',
                    self.terminal, f"{name} removida!"
                )

    def _test_print(self):
        run_cmd(
            'powershell -NoProfile -Command "$p=Get-Printer -Default -ErrorAction SilentlyContinue; if($p){rundll32 printui.dll,PrintUIEntry /k /n \\"$($p.Name)\\"; Write-Host \\"Enviando página de teste para: $($p.Name)\\" -ForegroundColor Cyan}else{Write-Host \'Nenhuma impressora padrão encontrada.\' -ForegroundColor Yellow}"',
            self.terminal, "Página de teste enviada!"
        )


# ════════════════════════════════════════════════════════
#  NOVO — DISCO E ARMAZENAMENTO
# ════════════════════════════════════════════════════════
class DiskPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "DISCO", GREEN_NEON)
        t = self.terminal

        self.add_section_label("USO E ESPAÇO")
        self.add_button(1,  "Espaço em todos os drives",            self._drives_space)
        self.add_button(2,  "Top 20 arquivos maiores no PC ★",      self._top_files,    CYAN_NEON)
        self.add_button(3,  "Top 10 pastas maiores (C:)",           self._top_folders)
        self.add_button(4,  "Tamanho de pasta específica",          self._folder_size)

        self.add_section_label("SAÚDE DO DISCO")
        self.add_button(5,  "SMART — Status do disco (PowerShell)", self._smart_status)
        self.add_button(6,  "Verificar erros (CHKDSK /f /r)",       lambda: run_cmd("echo s | chkdsk C: /f /r", t))
        self.add_button(7,  "Desfragmentar C: (HDDs)",              lambda: run_cmd("defrag C: /U /V /X", t))
        self.add_button(8,  "Otimizar C: (SSDs — TRIM)",            lambda: run_cmd("defrag C: /O /V", t, "Otimização SSD concluída!"))
        self.add_button(9,  "Instalar CrystalDiskInfo",             lambda: run_winget("CrystalDewWorld.CrystalDiskInfo","CrystalDiskInfo",t))
        self.add_button(10, "Instalar CrystalDiskMark",             lambda: run_winget("CrystalDewWorld.CrystalDiskMark","CrystalDiskMark",t))

        self.add_section_label("LIMPEZA DE DISCO")
        self.add_button(11, "Analisar o que está ocupando espaço",  lambda: run_cmd('powershell -NoProfile -Command "$p=Get-Command windirstat -ErrorAction SilentlyContinue; if($p){Start-Process windirstat}else{Write-Host \'[!] WinDirStat nao instalado. Use o botao 12 para instalar.\' -ForegroundColor Yellow}"', t))
        self.add_button(12, "Instalar WinDirStat",                  lambda: run_winget("WinDirStat.WinDirStat","WinDirStat",t))
        self.add_button(13, "Limpar arquivos temporários (temp)",   lambda: run_cmd('del /q /s /f "%temp%\\*" 2>nul', t, "Temp limpo!"))
        self.add_button(14, "Limpar cache de atualizações Windows", lambda: run_cmd('del /q /s /f "C:\\Windows\\SoftwareDistribution\\Download\\*" 2>nul', t, "Cache WU limpo!"))

        self.add_section_label("PARTIÇÕES E VOLUMES")
        self.add_button(15, "Listar volumes e partições",           lambda: run_cmd('powershell -NoProfile -Command "Get-Disk | Format-Table Number,FriendlyName,@{N=\'Size(GB)\';E={[math]::Round($_.Size/1GB,2)}},PartitionStyle,HealthStatus -AutoSize; Get-Partition | Format-Table DiskNumber,PartitionNumber,DriveLetter,@{N=\'Size(GB)\';E={[math]::Round($_.Size/1GB,2)}},Type -AutoSize"', t, "OK"))
        self.add_button(16, "Informações de disco (fsutil)",        lambda: run_cmd('powershell -NoProfile -Command "Get-Disk | Format-Table Number,FriendlyName,Size,HealthStatus -AutoSize"', t))
        self.add_button(17, "Abrir Gerenciamento de Disco",         lambda: run_cmd("diskmgmt.msc", t))

    def _drives_space(self):
        run_cmd(
            'powershell -NoProfile -Command "Get-PSDrive -PSProvider FileSystem | Format-Table Name,@{N=\'Usado(GB)\';E={[math]::Round(($_.Used/1GB),2)}},@{N=\'Livre(GB)\';E={[math]::Round(($_.Free/1GB),2)}},@{N=\'Total(GB)\';E={[math]::Round((($_.Used+$_.Free)/1GB),2)}} -AutoSize"',
            self.terminal, "OK"
        )

    def _top_files(self):
        run_cmd(
            'powershell -NoProfile -Command "Get-ChildItem C:\\ -Recurse -ErrorAction SilentlyContinue | Where-Object {!$_.PSIsContainer} | Sort-Object Length -Descending | Select-Object -First 20 | Format-Table @{N=\'Tamanho(MB)\';E={[math]::Round($_.Length/1MB,1)}},FullName -AutoSize"',
            self.terminal, "OK"
        )

    def _top_folders(self):
        run_cmd(
            'powershell -NoProfile -Command "Get-ChildItem C:\\ -ErrorAction SilentlyContinue | ForEach-Object {$s=(Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum; [PSCustomObject]@{GB=[math]::Round($s/1GB,2);Pasta=$_.FullName}} | Sort-Object GB -Descending | Select-Object -First 10 | Format-Table GB,Pasta -AutoSize"',
            self.terminal, "OK"
        )

    def _folder_size(self):
        popup = ctk.CTkInputDialog(text="Caminho da pasta (ex: C:\\Users\\Voce\\Downloads):", title="Tamanho de Pasta")
        path = (popup.get_input() or "").strip()
        if path:
            run_cmd(
                f'powershell -NoProfile -Command "$s=(Get-ChildItem \'{path}\' -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum; Write-Host (\'Tamanho: \'+[math]::Round($s/1MB,2)+\' MB (\'+[math]::Round($s/1GB,2)+\' GB)\')"',
                self.terminal, "OK"
            )

    def _smart_status(self):
        run_cmd(
            'powershell -NoProfile -Command "Get-PhysicalDisk | Format-Table FriendlyName,MediaType,Size,HealthStatus,OperationalStatus -AutoSize"',
            self.terminal, "Status SMART verificado!"
        )


# ════════════════════════════════════════════════════════
#  CENTRAL DE DOSSIÊS (UNIFICADA)
# ════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════
#  CENTRAL DE DOSSIÊS (FIXED v8.0)
# ════════════════════════════════════════════════════════
class DossierMasterPanel(ctk.CTkFrame):
    """Central de Dossiês independente para total visibilidade no layout."""

    def __init__(self, master):
        super().__init__(master, fg_color=BG_DARK, corner_radius=0)
        self._color = CYAN_NEON
        
        # Header (Aparece no topo da área de conteúdo)
        self.header_frame = ctk.CTkFrame(self, fg_color=BG_DARK, height=45, corner_radius=0)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)
        
        title_text = MINI_ASCII.get("SYSINFO", "[ CENTRAL DE DOSSIÊS ]")
        self.lbl_title = GlitchLabel(self.header_frame, text=title_text, font=("Courier New", 14, "bold"), text_color=CYAN_NEON)
        self.lbl_title.pack(side="left", padx=10, pady=10)
        
        # Linha Neon Divisória
        self.sep = ctk.CTkFrame(self, height=2, fg_color=CYAN_NEON)
        self.sep.pack(fill="x", padx=0, pady=(0, 5))

        # Tabview central (Tabs: Geral e Individual)
        self.tabs = ctk.CTkTabview(self, fg_color=BG_PANEL, 
                                 segmented_button_selected_color=CYAN_NEON,
                                 segmented_button_selected_hover_color=GREEN_NEON,
                                 segmented_button_unselected_color=BG_DARK,
                                 text_color=WHITE_DIM,
                                 corner_radius=4)

        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_list = self.tabs.add("📊 RELATÓRIO GERAL")
        self.tab_indv = self.tabs.add("👤 DOSSIÊ INDIVIDUAL")

        # Inicia elementos das abas
        self._setup_indv_tab()
        self._setup_list_tab()

        self._refresh_all()

    def on_enter(self):
        """Atualiza ao abrir a aba."""
        self._refresh_all()

    def _refresh_all(self):
        try:
            self._update_list_tab()
            self._update_indv_tab()
        except:
            pass

    def _setup_indv_tab(self):
        self.indv_scroller = ctk.CTkScrollableFrame(self.tab_indv, fg_color="transparent")
        self.indv_scroller.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.sel_var = tk.StringVar(value="Selecione o PC do Cliente...")
        self.sel_menu = ctk.CTkOptionMenu(
            self.indv_scroller, variable=self.sel_var, values=[],
            command=self._on_pc_change, fg_color=BG_DARK,
            button_color=GREEN_DARK, button_hover_color=GREEN_NEON,
            dropdown_fg_color=BG_PANEL, text_color=GREEN_NEON,
            font=("Courier New", 12)
        )
        self.sel_menu.pack(fill="x", pady=(0, 15))
        
        self.data_lbl = ctk.CTkLabel(self.indv_scroller, text="", font=("Courier New", 12), text_color=CYAN_NEON, justify="left", anchor="w")
        self.data_lbl.pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.indv_scroller, text="── ADICIONAR NOTA TÉCNICA ──", font=("Courier New", 10), text_color=GRAY_DIM).pack(fill="x", pady=(15, 2))
        self.note_box = ctk.CTkTextbox(self.indv_scroller, height=70, font=("Courier New", 11), fg_color=BG_DARK, border_width=1, border_color=GREEN_DARK)
        self.note_box.pack(fill="x", pady=5)
        
        btn_frame = ctk.CTkFrame(self.indv_scroller, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)
        
        btn_add = ctk.CTkButton(btn_frame, text="[ REGISTRAR NOTA ]", command=self._add_note, fg_color=BG_HOVER, hover_color=GREEN_DARK, text_color=GREEN_NEON, font=("Courier New", 11, "bold"))
        btn_add.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_exp = ctk.CTkButton(btn_frame, text="[ EXPORTAR RELATÓRIO (.TXT) ]", command=self._export_report, fg_color=BG_HOVER, hover_color=GREEN_DARK, text_color=CYAN_NEON, font=("Courier New", 11, "bold"))
        btn_exp.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(self.indv_scroller, text="── LINHA DO TEMPO (AÇÕES E NOTAS) ──", font=("Courier New", 10), text_color=GRAY_DIM).pack(fill="x", pady=(15, 2))
        self.log_box = ctk.CTkTextbox(self.indv_scroller, height=350, font=("Courier New", 10), fg_color=BG_DARK, border_width=1, border_color=BG_HOVER)
        self.log_box.pack(fill="both", expand=True, pady=5)
        
        self._curr_hwid = HistoryManager.get_hwid()
        self._map_hwid = {}

    def _update_indv_tab(self, update_menu=True):
        hwid_main = HistoryManager.get_hwid()
        db = HistoryManager.load_db()
        if update_menu:
            opts = []
            self._map_hwid = {}
            for hid, info in db.items():
                lbl = f"{info.get('hostname','PC')} ({info.get('name','Técnico')})"
                if hid == hwid_main: lbl += " [ESTE PC]"
                opts.append(lbl)
                self._map_hwid[lbl] = hid
            if opts: self.sel_menu.configure(values=opts)
            for l, h in self._map_hwid.items():
                if h == self._curr_hwid: self.sel_var.set(l); break

        pc_data = db.get(self._curr_hwid, {"hostname":"Desconhecido"})
        pfx = " > ESTE PC <\n" if self._curr_hwid == hwid_main else ""
        self.data_lbl.configure(text=f"{pfx}◈ ID: {self._curr_hwid}\n◈ HOST: {pc_data.get('hostname','?')}\n◈ OS: {pc_data.get('os','?')}\n◈ CPU: {pc_data.get('cpu','?')}\n◈ RAM: {pc_data.get('ram','?')}")
        
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        combined = []
        for h in pc_data.get("history", []): combined.append({"d": h.get("date",""), "m": f"[AÇÃO] {h.get('action','')}"})
        for n in pc_data.get("notes", []): combined.append({"d": n.get("date",""), "m": f"[NOTA] {n.get('info','')}"})
        
        def _parse_d(s):
            try: return datetime.datetime.strptime(s, "%d/%m/%Y %H:%M:%S")
            except: return datetime.datetime(2000,1,1)
        
        combined.sort(key=lambda x: _parse_d(x["d"]))
        if not combined: self.log_box.insert("end", "Nenhum registro.")
        else:
            for item in reversed(combined):
                mark = "◈ " if "[NOTA]" in item["m"] else "  "
                self.log_box.insert("end", f"{mark}[{item['d']}] {item['m']}\n")
        self.log_box.configure(state="disabled")

    def _on_pc_change(self, choice):
        self._curr_hwid = self._map_hwid.get(choice)
        self._update_indv_tab(update_menu=False)

    def _add_note(self):
        msg = self.note_box.get("1.0", "end-1c").strip()
        if msg:
            HistoryManager.save_note(msg, self._curr_hwid)
            messagebox.showinfo("Sucesso", "Nota adicionada ao dossiê!")
            self.note_box.delete("1.0", "end")
            self._refresh_all()

    def _export_report(self):
        db = HistoryManager.load_db()
        pc_data = db.get(self._curr_hwid)
        if not pc_data:
            messagebox.showerror("Erro", "Sem dados para exportar.")
            return

        desk = os.path.join(os.environ.get("USERPROFILE","C:\\"), "Desktop")
        file_name = f"DOSSIE_{pc_data.get('hostname','PC')}_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        file_path = os.path.join(desk, file_name)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("="*60 + "\n")
                f.write(f"  DEDSEC TOOLBOX v{APP_VERSION} - RELATÓRIO TÉCNICO OFICIAL  \n")
                f.write("="*60 + "\n\n")
                f.write(f"◈ CLIENTE / PC: {pc_data.get('hostname','?')}\n")
                f.write(f"◈ TÉCNICO Resp: {pc_data.get('name','?')}\n")
                f.write(f"◈ OS Version:   {pc_data.get('os','?')}\n")
                f.write(f"◈ Processador:  {pc_data.get('cpu','?')}\n")
                f.write(f"◈ Memória RAM:  {pc_data.get('ram','?')}\n")
                f.write(f"◈ Primeiro Reg: {pc_data.get('first_seen','?')}\n\n")
                
                f.write("── LINHA DO TEMPO (ATIVIDADES E NOTAS) ──\n")
                content = self.log_box.get("1.0", "end-1c").strip()
                f.write(content + "\n\n")
                f.write("="*60 + "\n")
            
            messagebox.showinfo("Sucesso", f"Relatório exportado para a sua Área de Trabalho!\n\nSalvo como: {file_name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar relatório: {e}")

    def _setup_list_tab(self):
        self.list_view = ctk.CTkScrollableFrame(self.tab_list, fg_color="transparent")
        self.list_view.pack(fill="both", expand=True, padx=5, pady=5)

    def _update_list_tab(self):
        for child in self.list_view.winfo_children(): child.destroy()
        db = HistoryManager.load_db()
        me = HistoryManager.get_hwid()
        for hid, info in reversed(list(db.items())):
            card = ctk.CTkFrame(self.list_view, fg_color=BG_CARD, border_width=1, border_color=BG_HOVER)
            card.pack(fill="x", pady=4, padx=2)
            ctk.CTkLabel(card, text=f"◈ {info.get('hostname','?')} {'[ESTE PC]' if hid == me else ''}", font=("Courier New", 13, "bold"), text_color=GREEN_NEON, anchor="w").pack(fill="x", padx=10, pady=(8,2))
            ctk.CTkLabel(card, text=f"Técnico: {info.get('name','?')} | OS: {info.get('os','?')[:40]}", font=("Courier New", 10), text_color=CYAN_NEON, anchor="w").pack(fill="x", padx=15)
            notes = info.get("notes", [])
            if notes:
                ctk.CTkLabel(card, text="[ HISTÓRICO DE NOTAS ]", font=("Courier New", 10, "bold"), text_color=GRAY_DIM).pack(fill="x", padx=15, pady=(5,0))
                for n in reversed(notes): # Remove o limite de mostrar apenas 3! Mostramos todas!
                    ctk.CTkLabel(card, text=f"  ◈ [{n.get('date','')}] {n.get('info','')}", font=("Courier New", 10), text_color=WHITE_DIM, justify="left", anchor="w", wraplength=650).pack(fill="x", padx=20, pady=1)
            else:
                ctk.CTkLabel(card, text="[ Sem observações ]", font=("Courier New", 10, "italic"), text_color=GRAY_DIM).pack(fill="x", padx=15, pady=5)





# ════════════════════════════════════════════════════════
#  NOVO — WINDOWS DEBLOATER NINJA
# ════════════════════════════════════════════════════════
class DebloaterPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "CLEAN", RED_NEON)
        t = self.terminal
        self.add_section_label("PRIVACIDADE E TELEMETRIA")
        self.add_button(1, "Desativar Telemetria e Coleta de Dados", self._disable_telemetry)
        self.add_button(2, "Desativar Cortana e Pesquisa na Web", self._disable_cortana)
        self.add_button(3, "Remover OneDrive do Sistema", self._remove_onedrive, ORANGE_NEON)
        
        self.add_section_label("REMOVER BLOATWARE (APPS NATIVOS)")
        self.add_button(4, "Remover Apps Inúteis (Solitaire, News, etc.)", self._remove_bloat)
        self.add_button(5, "Remover Xbox Features (se não for gamer)", self._remove_xbox)
        
        self.add_section_label("OPTIMIZAÇÃO DE SISTEMA")
        self.add_button(6, "Desativar Hibernação (Economiza espaço)", lambda: run_cmd("powercfg -h off", t, "Hibernação desativada!"))
        self.add_button(7, "Ajustar para Melhor Performance", self._best_perf)

        self.add_section_label("NAVEGADORES NATIVOS")
        self.add_button(8, "Exterminar Microsoft Edge ☠", self._remove_edge, RED_NEON)

    def _disable_telemetry(self):
        cmd = (
            'reg add "HKLM\\Software\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f & '
            'reg add "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f & '
            'sc config DiagTrack start= disabled & sc stop DiagTrack'
        )
        run_cmd(cmd, self.terminal, "Telemetria desativada!")

    def _disable_cortana(self):
        cmd = (
            'reg add "HKLM\\Software\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f & '
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f'
        )
        run_cmd(cmd, self.terminal, "Cortana e Bing Search desativados!")

    def _remove_onedrive(self):
        run_cmd("taskkill /f /im OneDrive.exe & %SystemRoot%\\SysWOW64\\OneDriveSetup.exe /uninstall", self.terminal, "OneDrive removido!")

    def _remove_bloat(self):
        cmd = 'powershell -NoProfile -Command "Get-AppxPackage *3dbuilder* | Remove-AppxPackage; Get-AppxPackage *skypeapp* | Remove-AppxPackage; Get-AppxPackage *getstarted* | Remove-AppxPackage; Get-AppxPackage *bingnews* | Remove-AppxPackage"'
        run_cmd(cmd, self.terminal, "Bloatwares removidos!")

    def _remove_xbox(self):
        cmd = 'powershell -NoProfile -Command "Get-AppxPackage *xbox* | Remove-AppxPackage"'
        run_cmd(cmd, self.terminal, "Xbox features removidas!")

    def _best_perf(self):
        cmd = 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f'
        run_cmd(cmd, self.terminal, "Ajustado para performance!")

    def _remove_edge(self):
        msg = "⚠ EXTERMÍNIO TOTAL E DEFINITIVO\n\nIsso removerá rastros, arquivos, serviços e entradas de inicialização (startup).\nDeseja mesmo prosseguir?"
        if messagebox.askyesno("Exterminar Microsoft Edge", msg, icon="warning"):
            cmd = (
                # Matar processos
                'taskkill /F /IM msedge.exe /T 2>nul & '
                'taskkill /F /IM MicrosoftEdgeUpdate.exe /T 2>nul & '
                'taskkill /F /IM msedgewebview2.exe /T 2>nul & '
                # Parar e DELETAR Serviços
                'sc stop edgeupdate 2>nul & sc delete edgeupdate 2>nul & '
                'sc stop edgeupdatem 2>nul & sc delete edgeupdatem 2>nul & '
                'sc stop MicrosoftEdgeElevationService 2>nul & sc delete MicrosoftEdgeElevationService start= disabled 2>nul & '
                # Tentar desinstalar via setup
                'for /d %i in ("C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\*") do (if exist "%i\\Installer\\setup.exe" "%i\\Installer\\setup.exe" --uninstall --system-level --force-uninstall) & '
                # Limpeza Bruta de Startup e Ghost Entries
                'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "MicrosoftEdgeAutoLaunch" /f 2>nul & '
                'reg delete "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "MicrosoftEdgeAutoLaunch" /f 2>nul & '
                'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "msedge" /f 2>nul & '
                'reg delete "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "msedge" /f 2>nul & '
                'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run" /v "MicrosoftEdgeAutoLaunch" /f 2>nul & '
                'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run" /v "msedge" /f 2>nul & '
                # Remover Active Setup (impede volta em novos logins)
                'reg delete "HKLM\\SOFTWARE\\Microsoft\\Active Setup\\Installed Components\\{9459C573-5bcc-4c2b-99d7-d860ba3f60f6}" /f 2>nul & '
                # Remover tarefas agendadas
                'schtasks /delete /tn "MicrosoftEdgeUpdateTaskMachineCore" /f 2>nul & '
                'schtasks /delete /tn "MicrosoftEdgeUpdateTaskMachineUA" /f 2>nul & '
                'schtasks /delete /tn "MicrosoftEdgeUpdateBrowserReplacementService" /f 2>nul & '
                # Bloquear no Registro para sempre
                'reg add "HKLM\\SOFTWARE\\Microsoft\\EdgeUpdate" /v DoNotUpdateToEdgeWithChromium /t REG_DWORD /d 1 /f & '
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\EdgeUpdate" /v InstallDefault /t REG_DWORD /d 0 /f & '
                # Forçar POSSE e DELETAR pastas (Microsoft Edge, EdgeUpdate, EdgeCore)
                'takeown /f "C:\\Program Files (x86)\\Microsoft\\Edge" /r /d y 2>nul & icacls "C:\\Program Files (x86)\\Microsoft\\Edge" /grant everyone:F /t /q 2>nul & rd /s /q "C:\\Program Files (x86)\\Microsoft\\Edge" 2>nul & '
                'takeown /f "C:\\Program Files (x86)\\Microsoft\\EdgeUpdate" /r /d y 2>nul & icacls "C:\\Program Files (x86)\\Microsoft\\EdgeUpdate" /grant everyone:F /t /q 2>nul & rd /s /q "C:\\Program Files (x86)\\Microsoft\\EdgeUpdate" 2>nul & '
                'takeown /f "C:\\Program Files (x86)\\Microsoft\\EdgeCore" /r /d y 2>nul & icacls "C:\\Program Files (x86)\\Microsoft\\EdgeCore" /grant everyone:F /t /q 2>nul & rd /s /q "C:\\Program Files (x86)\\Microsoft\\EdgeCore" 2>nul & '
                'takeown /f "C:\\Program Files\\Microsoft\\Edge" /r /d y 2>nul & icacls "C:\\Program Files\\Microsoft\\Edge" /grant everyone:F /t /q 2>nul & rd /s /q "C:\\Program Files\\Microsoft\\Edge" 2>nul & '
                'rd /s /q "%LOCALAPPDATA%\\Microsoft\\Edge" 2>nul & '
                # Remover do Menu 'Aplicativos Instalados' (Painel de Controle / Configurações)
                'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Microsoft Edge" /f 2>nul & '
                'reg delete "HKLM\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Microsoft Edge" /f 2>nul & '
                'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Microsoft Edge Update" /f 2>nul & '
                'reg delete "HKLM\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Microsoft Edge Update" /f 2>nul & '
                'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Microsoft Edge" /f 2>nul & '
                'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Microsoft Edge Update" /f 2>nul & '
                # Tentar remover como pacote Appx por via das dúvidas
                'powershell -NoProfile -Command "Get-AppxPackage *MicrosoftEdge* | Remove-AppxPackage -ErrorAction SilentlyContinue" 2>nul & '
                # Atalhos finais
                'del /q /f "%PUBLIC%\\Desktop\\Microsoft Edge.lnk" 2>nul & '
                'del /q /f "%USERPROFILE%\\Desktop\\Microsoft Edge.lnk" 2>nul'
            )
            run_cmd(cmd, self.terminal, "Microsoft Edge EXTERMINADO COMPLETAMENTE!")


# ════════════════════════════════════════════════════════
#  NOVO — HARDWARE PRO MONITOR
# ════════════════════════════════════════════════════════
class MonitorPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "HARDWARE", GREEN_NEON)
        self.terminal.pack_forget()
        self._toggle_btn.pack_forget()

        self.add_section_label("MONITORAMENTO EM TEMPO REAL")

        self.cpu_lbl = ctk.CTkLabel(self.btn_frame, text="CPU: --%", font=("Courier New", 14, "bold"), text_color=GREEN_NEON)
        self.cpu_lbl.pack(pady=(10, 0))
        self.cpu_bar = ctk.CTkProgressBar(self.btn_frame, progress_color=GREEN_NEON, height=12)
        self.cpu_bar.set(0)
        self.cpu_bar.pack(fill="x", padx=20, pady=5)

        self.ram_lbl = ctk.CTkLabel(self.btn_frame, text="RAM: --%", font=("Courier New", 14, "bold"), text_color=CYAN_NEON)
        self.ram_lbl.pack(pady=(10, 0))
        self.ram_bar = ctk.CTkProgressBar(self.btn_frame, progress_color=CYAN_NEON, height=12)
        self.ram_bar.set(0)
        self.ram_bar.pack(fill="x", padx=20, pady=5)

        self.gpu_lbl = ctk.CTkLabel(self.btn_frame, text="DETALHES DO HARDWARE", font=("Courier New", 11), text_color=GRAY_DIM)
        self.gpu_lbl.pack(pady=20)
        
        self.details = ctk.CTkTextbox(self.btn_frame, height=200, font=("Courier New", 10), fg_color=BG_DARK)
        self.details.pack(fill="both", expand=True, padx=10, pady=10)

        self._active = True
        self._update_stats()

    def _update_stats(self):
        if not self._active: return
        def _collect():
            try:
                # Usa WMI de forma rápida
                c = subprocess.run('powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).LoadPercentage"', shell=True, capture_output=True, text=True).stdout.strip()
                m = subprocess.run('powershell -NoProfile -Command "$os=Get-CimInstance Win32_OperatingSystem; [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize)*100)"', shell=True, capture_output=True, text=True).stdout.strip()
                return int(c or 0), int(m or 0)
            except: return 0, 0

        def _sync(res):
            cpu, ram = res
            self.cpu_lbl.configure(text=f"CPU: {cpu}%")
            self.cpu_bar.set(cpu/100)
            self.ram_lbl.configure(text=f"RAM: {ram}%")
            self.ram_bar.set(ram/100)
            self.after(2000, self._update_stats)

        def _thread():
            res = _collect()
            try:
                self.after(0, lambda r=res: _sync(r))
            except Exception:
                pass
        threading.Thread(target=_thread, daemon=True).start()

    def on_leave(self):
        self._active = False


# ════════════════════════════════════════════════════════
#  NOVO — CENTRAL DE DRIVERS
# ════════════════════════════════════════════════════════
class DriverPanel(BasePanel):
    def __init__(self, master):
        super().__init__(master, "HARDWARE", YELLOW_NEON)
        t = self.terminal
        self.add_section_label("GERENCIAR DRIVERS")
        self.add_button(1, "Listar todos os Drivers instalados", lambda: run_cmd("pnputil /enum-drivers", t))
        self.add_button(2, "Verificar dispositivos com erro",   lambda: run_cmd("powershell -Command \"Get-PnpDevice | Where-Object {$_.Status -eq 'Error'}\"", t))
        self.add_button(3, "Backup de Drivers (Pasta Desktop)", self._backup_drivers)
        
        self.add_section_label("ATUALIZAÇÃO")
        self.add_button(4, "Procurar Drivers (Windows Update)", lambda: run_cmd("powershell -Command \"(New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().Search('IsInstalled=0 and Type=\\'Driver\\'').Updates\"", t))
        self.add_button(5, "Abrir Gerenciador de Dispositivos", lambda: run_cmd("devmgmt.msc", t))

    def _backup_drivers(self):
        path = os.path.join(os.environ["USERPROFILE"], "Desktop", "Drivers_Backup")
        if not os.path.exists(path): os.makedirs(path)
        run_cmd(f"pnputil /export-driver * \"{path}\"", self.terminal, f"Drivers exportados para: {path}")

# ════════════════════════════════════════════════════════
#  PAINEL PRINCIPAL — DedSec skull → WE ARE COMING
# ════════════════════════════════════════════════════════
class PrincipalPanel(ctk.CTkFrame):
    """Tela inicial: Terminal typewriter + GIF Animado."""

    def __init__(self, master):
        super().__init__(master, fg_color="#000000", corner_radius=0)
        self._running = True
        self._gif_frames = []
        self._base_frames = []
        self._current_frame = 0
        self._gif_id = None
        self._is_ready = False

        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.canvas.bind("<Configure>", self._on_resize)

        self.terminal_id = self.canvas.create_text(
            20, 20, anchor="nw", text="",
            font=("Courier New", 12, "bold"), fill=GREEN_NEON
        )
        self.breach_id = self.canvas.create_text(
            0, 0, anchor="center", text="",
            font=("Courier New", 14, "bold"), fill=GREEN_NEON
        )

        self.terminal_lines = [
            "Initializing DEDSEC sub-routines...",
            "Bypassing mainframe security protocols...",
            "Scanning nodes... [OK]",
            "Injecting payload... [██████████] 100%",
            "Authentication logic overridden.",
            "Root Access: GRANTED.",
            f"Welcome back, {USER_NAME}.",
            ""
        ]
        self.current_line = 0
        self.current_char = 0
        self.display_text = ""
        self.after(300, self._typewriter)

    # ── Typewriter & GIF Loading ───────────────────────────────
    def _typewriter(self):
        if not self._running: return
        if self.current_line < len(self.terminal_lines):
            line = self.terminal_lines[self.current_line]
            if self.current_char < len(line):
                self.display_text += line[self.current_char]
                self.canvas.itemconfig(self.terminal_id, text=self.display_text + "█")
                self.current_char += 1
                self.after(random.randint(5, 20), self._typewriter)
            else:
                self.display_text += "\n"
                self.current_line += 1
                self.current_char = 0
                self.after(150, self._typewriter)
        else:
            self.canvas.itemconfig(self.terminal_id, text=self.display_text)
            threading.Thread(target=self._load_gif_background, daemon=True).start()

    def _load_gif_background(self):
        try:
            path = asset("157084787880c1ead98ec92332da7094 (1).gif")
            if not os.path.exists(path):
                return
            
            img = Image.open(path)
            frames = []
            try:
                while True:
                    frame = img.copy().convert("RGBA")
                    frames.append(frame)
                    img.seek(img.tell() + 1)
            except EOFError:
                pass
            
            self._base_frames = frames
            self.after(0, self._on_gif_ready)
        except Exception:
            pass

    def _on_gif_ready(self):
        if not self._running: return
        self._is_ready = True
        self._place_gif()
        self._animate_gif()

    # ── Tela & Animação ───────────────────────────────────────
    def _on_resize(self, event):
        if self._is_ready:
            self._place_gif()

    def _place_gif(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100 or not self._base_frames:
            return

        cx, cy = w // 2, h // 2
        first_frame = self._base_frames[0]
        
        max_h = int(h * 0.65)
        ratio = min(max_h / first_frame.height, 1.0)
        new_w = int(first_frame.width * ratio)
        new_h = int(first_frame.height * ratio)

        self._gif_frames = []
        for bg_frame in self._base_frames:
            resized = bg_frame.resize((new_w, new_h), Image.LANCZOS)
            final = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 255))
            final = Image.alpha_composite(final, resized)
            self._gif_frames.append(ImageTk.PhotoImage(final.convert("RGB")))

        if self._gif_id:
            self.canvas.delete(self._gif_id)
        
        self._current_frame = 0
        self._gif_id = self.canvas.create_image(cx, cy, image=self._gif_frames[0], tags="gif_img")
        
        self.canvas.coords(self.breach_id, cx, cy + new_h // 2 + 30)
        self.canvas.itemconfig(self.breach_id, text="◈  SYSTEM BREACH IN PROGRESS...  ◈")
        self.canvas.tag_raise(self.breach_id)
        self.canvas.tag_raise(self.terminal_id)

    def _animate_gif(self):
        if not self._running or not self._gif_frames:
            return
            
        self._current_frame = (self._current_frame + 1) % len(self._gif_frames)
        self.canvas.itemconfig(self._gif_id, image=self._gif_frames[self._current_frame])
        
        # Piscar breach indicator
        self.canvas.itemconfig(self.breach_id,
            fill=GREEN_NEON if random.random() > 0.12 else "#000000")
            
        self.after(50, self._animate_gif)

    def on_leave(self):
        self._running = False



# ════════════════════════════════════════════════════════
#  JANELA PRINCIPAL
# ════════════════════════════════════════════════════════
class App(ctk.CTk):
    NAV_ITEMS = [
        ("●",  "PRINCIPAL",         PrincipalPanel,   GREEN_NEON),
        ("A",  "CENTRAL DE DOSSIÊS", DossierMasterPanel, CYAN_NEON),
        ("1",  "RUNTIMES & LIBS",    RuntimesPanel,    BLUE_NEON),
        ("2",  "NAVEGADORES & COM",  BrowsersPanel,    PURPLE_NEON),
        ("3",  "SUPORTE REMOTO",     RemotePanel,      CYAN_NEON),
        ("4",  "UTILITÁRIOS",        UtilsPanel,       GREEN_NEON),
        ("5",  "MANUTENÇÃO",         MaintenancePanel, ORANGE_NEON),
        ("6",  "REDE & CONEXÃO",     NetworkPanel,     CYAN_NEON),
        ("7",  "HARDWARE & DRIVERS", HardwarePanel,    YELLOW_NEON),
        ("8",  "SEGURANÇA",          SecurityPanel,    RED_NEON),
        ("9",  "INFO DO SISTEMA",    SysInfoPanel,     GREEN_NEON),
        ("10", "ATIVAR WIN/OFFICE",  ActivationPanel,  PURPLE_NEON),
        ("11", "LIMPEZA PROFUNDA",   CleanPanel,       CYAN_NEON),
        ("12", "BACKUP RÁPIDO",      BackupPanel,      GREEN_NEON),
        ("13", "PROCESSOS",          ProcessPanel,     ORANGE_NEON),
        ("14", "VELOCIDADE & REDE",  SpeedPanel,       CYAN_NEON),
        ("15", "IMPRESSORAS",        PrinterPanel,     YELLOW_NEON),
        ("16", "DISCO & STORAGE",    DiskPanel,        GREEN_NEON),
        ("DB", "DEBLOATER NINJA",    DebloaterPanel,   RED_NEON),
        ("M",  "HARDWARE MONITOR",   MonitorPanel,     GREEN_NEON),
        ("D",  "DRIVER CENTRAL",     DriverPanel,      YELLOW_NEON),
        ("K",  "KALI LINUX TOOLS",   KaliPanel,        RED_NEON),
        ("S",  "MEUS SCRIPTS ★",     CustomScriptsPanel, YELLOW_NEON),
        ("99", "KIT PC NOVO ★",      KitPanel,         GREEN_NEON),
    ]


    def __init__(self):
        super().__init__()
        self.title(f"DEDSEC TOOLBOX v{APP_VERSION}  —  {USER_NAME}")

        # ── Registro Automático no Dossiê ──
        HistoryManager.register_machine()

        # ── Centralizar janela antes de maximizar ──
        try:
            import ctypes as _ct
            user32 = _ct.windll.user32
            user32.SetProcessDPIAware()
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
        except Exception:
            self.update_idletasks()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
        self.geometry(f"1200x750+{(sw-1200)//2}+{(sh-750)//2}")
        self.minsize(1000, 600)
        self.configure(fg_color=BG_DARK)
        self.after(0, lambda: self.state("zoomed"))
        self._set_icon()
        self._build_ui()
        self._current_panel = None
        self._panels = {}
        self._select(0)          # Começa em PRINCIPAL
        self._setup_keybinds()
        # Screensaver: olho após 5 min de inatividade
        eye_path = self._find_eye_gif()
        self._screensaver = ScreenSaver(self, eye_path)

        # ── Update Check ao Iniciar a App ──
        self.after(3000, self._check_updates_bg)

    def _check_updates_bg(self):
        """Verifica atualizações em background 3 segundos após abrir o programa principal"""
        def _bg():
            latest, url = UpdateChecker.check()
            if latest and url:
                self.after(0, lambda: self._prompt_update(latest, url))
        threading.Thread(target=_bg, daemon=True).start()

    def _prompt_update(self, version, url):
        # Garante que a janela de prompt fica na frente
        self.attributes("-topmost", True)
        if messagebox.askyesno("Atualização Disponível", f"A versão v{version} foi encontrada no GitHub!\n\nDeseja realizar o download e atualizar agora?", parent=self):
            UpdateChecker.download_and_install(url, version)
            self.destroy()
            sys.exit()
        self.attributes("-topmost", False)

    @staticmethod
    def _find_eye_gif():
        for n in ("eye_screensaver.gif", "djon.gif", "eye.gif"):
            p = asset(n)
            if os.path.exists(p):
                return p
        return None

    def _setup_keybinds(self):
        """Atalhos: P=PRINCIPAL, 1-9=painéis, K=Kali, ESC=sair."""
        def _nav(idx):
            f = self.focus_get()
            # Ignora atalho se estiver digitando em campos de texto
            if isinstance(f, (tk.Text, tk.Entry)) or "entry" in str(f).lower() or "text" in str(f).lower():
                return
            self._select(idx)

        self.bind("p", lambda e: _nav(0))
        self.bind("P", lambda e: _nav(0))
        for i in range(1, 10):
            self.bind(str(i), lambda e, idx=i: _nav(idx))
            
        # K abre Kali Linux Tools
        kali_idx = next((i for i, item in enumerate(self.NAV_ITEMS) if item[1] == "KALI LINUX TOOLS"), None)
        if kali_idx is not None:
            self.bind("k", lambda e, idx=kali_idx: _nav(idx))
            self.bind("K", lambda e, idx=kali_idx: _nav(idx))
            
        # A abre Central de Dossiês
        hist_idx = next((i for i, item in enumerate(self.NAV_ITEMS) if item[1] == "CENTRAL DE DOSSIÊS"), None)
        if hist_idx is not None:
            self.bind("a", lambda e, idx=hist_idx: _nav(idx))
            self.bind("A", lambda e, idx=hist_idx: _nav(idx))

        self.bind("<Escape>", lambda e: self._on_close())
        # Intercepta o fechar pela janela para mostrar fsociety
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Fecha o aplicativo instantaneamente."""
        self.destroy()

    def _set_icon(self):
        icon_path = asset("icon.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except Exception: pass

    def _build_ui(self):
        # ── STATUS BAR no rodapé ─────────────────────────────
        self._build_status_bar()

        # ── HEADER com fundo de imagem ──────────────────────
        header = ctk.CTkFrame(self, fg_color=BG_DARK, height=138, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        self._header_canvas = tk.Canvas(header, bg="#000000", highlightthickness=0, height=138)
        self._header_canvas.pack(fill="both", expand=True)
        self._load_header_image()

        # Linha divisória neon
        sep = ctk.CTkFrame(self, height=2, fg_color=GREEN_NEON, corner_radius=0)
        sep.pack(fill="x")

        # ── Layout central ────────────────────────────────────
        center = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        center.pack(fill="both", expand=True)

        # ── SIDEBAR ───────────────────────────────────────────
        self._sidebar_frame = ctk.CTkFrame(center, width=220, fg_color=BG_PANEL, corner_radius=0)
        self._sidebar_frame.pack(side="left", fill="y", padx=(0, 2))
        self._sidebar_frame.pack_propagate(False)
        self._build_sidebar(self._sidebar_frame)

        # ── Área de conteúdo com fundo das mãos ASCII ────────
        self._content_outer = ctk.CTkFrame(center, fg_color=BG_PANEL, corner_radius=0)
        self._content_outer.pack(side="left", fill="both", expand=True)
        self._load_bg_image(self._content_outer)

        self._content = ctk.CTkFrame(self._content_outer, fg_color="transparent", corner_radius=0)
        self._content.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _build_status_bar(self):
        """Barra de status no rodapé: módulo ativo + atalhos + relógio ao vivo."""
        sep = ctk.CTkFrame(self, height=1, fg_color=GREEN_DARK, corner_radius=0)
        sep.pack(fill="x", side="bottom")
        bar = ctk.CTkFrame(self, fg_color="#060e08", height=22, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status_mod = ctk.CTkLabel(
            bar, text="● MÓDULO: PRINCIPAL",
            font=("Courier New", 9), text_color=GREEN_DIM, anchor="w"
        )
        self._status_mod.pack(side="left", padx=10)

        ctk.CTkLabel(bar, text="[P: principal]  [1-9: módulos]  [K: kali]  [ESC: sair]",
                     font=("Courier New", 9), text_color=GRAY_DIM).pack(side="left", padx=16)

        self._tick_status()

    def _tick_status(self):
        """Relógio ao vivo: atualiza header canvas E status bar."""
        try:
            now = datetime.datetime.now()
            txt = f"◷ {now.strftime('%H:%M:%S   %d/%m/%Y')}"
            if hasattr(self, '_clock_id') and hasattr(self, '_header_canvas'):
                self._header_canvas.itemconfig(self._clock_id, text=txt)
            self.after(1000, self._tick_status)
        except Exception:
            pass

    def _load_header_image(self):
        """
        Header: robô metálico cobre TODO o header de ponta a ponta.
        Carrega fonte, depois usa bind Configure para preencher 100% da largura.
        """
        self._header_img_ref = None
        self._header_source_img = None

        # Pré-carrega imagem fonte — mãos ASCII como prioridade para o header
        candidates = [
            "hands_ascii.jpg",
            "25e45cf3153f5d88e4833a5133ffd821.jpg",
            "robot.jpg",
            "hello_world.jpg",
        ]
        for fname in candidates:
            path = asset(fname)
            if not os.path.exists(path):
                continue
            try:
                self._header_source_img = Image.open(path).convert("RGB")
                break
            except Exception:
                continue

        # Bind: toda vez que o canvas mudar de tamanho, redesenha a imagem
        self._header_canvas.bind("<Configure>", self._on_header_resize)

        # Textos fixos (fica sempre na frente da imagem)
        self._header_canvas.create_text(
            20, 42, anchor="nw",
            text=f"◈ DEDSEC TOOLBOX  v{APP_VERSION}",
            font=("Courier New", 18, "bold"),
            fill="#00ff41",
            tags="htext"
        )
        self._header_canvas.create_text(
            20, 80, anchor="nw",
            text="// SISTEMA DE MANUTENÇÃO AVANÇADO  //  BY GabrielRj6",
            font=("Courier New", 10),
            fill="#00b32c",
            tags="htext"
        )

        # Badge de Administrador
        if IS_ADMIN:
            self._header_canvas.create_rectangle(20, 105, 160, 125, fill="#00ff41", outline="#00ff41", tags="htext")
            self._header_canvas.create_text(90, 115, text="ROOT / ADMIN ACCESS", font=("Courier New", 9, "bold"), fill="#000000", tags="htext")
        else:
            self._header_canvas.create_rectangle(20, 105, 160, 125, fill="#ff5252", outline="#ff5252", tags="htext")
            self._header_canvas.create_text(90, 115, text="USER MODE / DENIED", font=("Courier New", 9, "bold"), fill="#ffffff", tags="htext")

        # Info do sistema (canto direito) — posição Y distribuída no header
        self._info_ids = {}
        self._info_keys = ["user_pc", "os", "cpu", "ram"]
        self._info_colors = ["#00ff41", "#c8c8c8", "#00f5ff", "#ffff00"]
        h_header = 138
        total_items = 5  # 4 info + 1 relógio
        spacing = h_header / (total_items + 1)
        for i, (key, color) in enumerate(zip(self._info_keys, self._info_colors)):
            y_pos = int(spacing * (i + 1))
            tid = self._header_canvas.create_text(
                1190, y_pos, anchor="ne",
                text="...",
                font=("Courier New", 10),
                fill=color,
                tags="htext"
            )
            self._info_ids[key] = tid
        # Relógio ao vivo — última posição na distribuição
        self._clock_id = self._header_canvas.create_text(
            1190, int(spacing * (total_items)), anchor="ne",
            text="",
            font=("Courier New", 11, "bold"),
            fill="#00ff41",
            tags="htext"
        )
        self._tick_status()
        self._load_sysinfo_async()

    def _on_header_resize(self, event):
        """Redesenha imagem do header para preencher 100% do canvas a cada resize."""
        w, h = event.width, event.height
        if w < 10 or h < 10:
            return
        self._header_canvas.delete("hbg")
        if self._header_source_img is None:
            return
        try:
            img = self._header_source_img.resize((w, h), Image.LANCZOS)
            # Brilho 40% — visível mas texto legível
            img = ImageEnhance.Brightness(img).enhance(0.40)
            r, g, b = img.split()
            img = Image.merge("RGB", (
                r.point(lambda x: int(x * 0.15)),
                g.point(lambda x: min(255, int(x * 1.5))),
                b.point(lambda x: int(x * 0.15))
            ))
            self._header_img_ref = ImageTk.PhotoImage(img)
            # Cria imagem com tag "hbg" e manda pra trás dos textos
            self._header_canvas.create_image(0, 0, anchor="nw",
                                              image=self._header_img_ref, tags="hbg")
            self._header_canvas.tag_lower("hbg")
            # Scanlines decorativas
            for y in range(0, h, 5):
                self._header_canvas.create_line(0, y, w, y,
                                                fill="#001200", width=1, tags="hbg")
            self._header_canvas.tag_lower("hbg")
            # Reposiciona info do sistema — distribuição dinâmica
            total_items = 5  # 4 info + 1 relógio
            spacing = h / (total_items + 1)
            for i, key in enumerate(self._info_keys):
                if key in self._info_ids:
                    self._header_canvas.coords(self._info_ids[key], w - 10, int(spacing * (i + 1)))
            # Reposiciona relógio na última posição
            if hasattr(self, '_clock_id'):
                self._header_canvas.coords(self._clock_id, w - 10, int(spacing * total_items))
        except Exception:
            pass

    def _load_bg_image(self, parent):
        """
        Fundo da área de conteúdo: mãos ASCII se tocando (visível, brilho 30%)
        Fica centralizado e cobre toda a área de conteúdo.
        """
        self._bg_canvas = tk.Canvas(parent, bg="#0f1a0f", highlightthickness=0)
        self._bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._bg_img_ref = None

        # Usa as mãos ASCII como fundo do conteúdo — é a imagem principal
        candidates = [
            "25e45cf3153f5d88e4833a5133ffd821.jpg",
            "hands_ascii.jpg",
            "25e45cf3153f5d88e4833a5133ffd821-1920x1080.jpg",
        ]
        for fname in candidates:
            path = asset(fname)
            if not os.path.exists(path):
                continue
            try:
                img = Image.open(path).convert("RGB")
                # Redimensiona para cobrir toda a área (980x630 aprox.)
                img = img.resize((980, 630), Image.LANCZOS)
                # Brilho 30% — aparece claramente mas não atrapalha os botões
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(0.30)
                # Tinge de verde
                r, g, b = img.split()
                img = Image.merge("RGB", (
                    r.point(lambda x: int(x * 0.1)),
                    g.point(lambda x: min(255, int(x * 1.4))),
                    b.point(lambda x: int(x * 0.1))
                ))
                self._bg_img_ref = ImageTk.PhotoImage(img)
                self._bg_canvas.create_image(490, 315, image=self._bg_img_ref, anchor="center")
                break
            except Exception:
                continue

    def _build_sidebar(self, sidebar):
        """Sidebar: botões de navegação + samurai no rodapé"""
        scroll_area = ctk.CTkScrollableFrame(
            sidebar, fg_color=BG_PANEL,
            scrollbar_button_color=GREEN_DARK,
            corner_radius=0
        )
        scroll_area.pack(fill="both", expand=True)

        self._sidebar_logo = GlitchLabel(
            scroll_area, text=f"◈ {USER_NAME}",
            font=("Courier New", 13, "bold"),
            text_color=GREEN_NEON, fg_color=BG_PANEL
        )
        self._sidebar_logo.pack(pady=(12, 4), padx=8)

        sub = ctk.CTkLabel(
            scroll_area, text=f"DEDSEC TOOLBOX v{APP_VERSION}",
            font=("Courier New", 10),
            text_color=GRAY_DIM, fg_color=BG_PANEL
        )
        sub.pack(pady=(0, 6))

        sep2 = ctk.CTkFrame(scroll_area, height=1, fg_color=GREEN_DARK)
        sep2.pack(fill="x", padx=8, pady=(0, 8))

        self._nav_buttons = []
        for i, (num, label, _, color) in enumerate(self.NAV_ITEMS):
            btn = ctk.CTkButton(
                scroll_area,
                text=f"  [{num}]  {label}",
                font=("Courier New", 11, "bold"),
                fg_color=BG_PANEL, hover_color=BG_HOVER,
                text_color=color, border_color=BG_PANEL,
                border_width=1, corner_radius=2,
                anchor="w", height=34,
                command=lambda idx=i: self._select(idx)
            )
            btn.pack(fill="x", padx=6, pady=2)
            self._nav_buttons.append(btn)

        sep3 = ctk.CTkFrame(scroll_area, height=1, fg_color=GREEN_DARK)
        sep3.pack(fill="x", padx=8, pady=8)

        exit_btn = ctk.CTkButton(
            scroll_area, text="  [0]  SAIR",
            font=("Courier New", 11, "bold"),
            fg_color=BG_PANEL, hover_color="#300000",
            text_color=RED_NEON, border_color=BG_PANEL,
            border_width=1, corner_radius=2,
            anchor="w", height=34, command=self._on_close
        )
        exit_btn.pack(fill="x", padx=6, pady=2)

        # ── GIF animado no rodapé da sidebar com borda neon ──────────────
        sidebar_img_frame = ctk.CTkFrame(sidebar, fg_color=GREEN_DARK, height=112, corner_radius=0)
        sidebar_img_frame.pack(fill="x", side="bottom", padx=0, pady=0)
        sidebar_img_frame.pack_propagate(False)

        # Borda neon: padding interno 2px
        border_inner = ctk.CTkFrame(sidebar_img_frame, fg_color="#000000", corner_radius=0)
        border_inner.pack(fill="both", expand=True, padx=2, pady=2)

        # Tenta carregar GIF da caveira — looping infinito, cobre tudo
        self._sidebar_gif_player = None
        skull_gif_names = [
            "b6e1b7f9ef3227a4294385d9980a50d3.gif",
            "skull.gif", "dedsec_skull_sidebar.gif",
        ]
        skull_gif_path = None
        for fname in skull_gif_names:
            p = asset(fname)
            if os.path.exists(p):
                skull_gif_path = p
                break

        if skull_gif_path:
            self._sidebar_gif_player = GifPlayer(
                border_inner,
                skull_gif_path,
                one_shot=False,   # loop infinito
                tint=False,       # cores originais do gif
                contain=False,    # cover: preenche tudo sem bordas pretas
                bg="#000000"
            )
            self._sidebar_gif_player.place(relx=0, rely=0, relwidth=1, relheight=1)
        else:
            # Fallback: imagem estática se gif não existir
            for fname in ["dark_triad.jpg", "pixel_404.jpg"]:
                path_img = asset(fname)
                if not os.path.exists(path_img):
                    continue
                try:
                    img_s = Image.open(path_img).convert("RGB")
                    self._sidebar_img_ref = ImageTk.PhotoImage(img_s.resize((216, 108), Image.LANCZOS))
                    c = tk.Canvas(border_inner, bg="#000000", highlightthickness=0)
                    c.pack(fill="both", expand=True)
                    c.create_image(108, 54, anchor="center", image=self._sidebar_img_ref)
                    break
                except Exception:
                    continue

    def _select(self, idx):
        for i, btn in enumerate(self._nav_buttons):
            btn.configure(fg_color=BG_PANEL, border_color=BG_PANEL)
        _, label, _, color = self.NAV_ITEMS[idx]
        self._nav_buttons[idx].configure(fg_color=BG_HOVER, border_color=color)
        if hasattr(self, '_status_mod'):
            self._status_mod.configure(text=f"● MÓDULO: {label}", text_color=color)
        # Notifica painel atual ao sair
        if self._current_panel and hasattr(self._current_panel, 'on_leave'):
            try: self._current_panel.on_leave()
            except: pass
        if self._current_panel:
            self._current_panel.place_forget()
        # PrincipalPanel (idx=0) sempre destruído e recriado — GIFs tocam do início
        if idx == 0 and 0 in self._panels:
            try: self._panels[0].destroy()
            except: pass
            del self._panels[0]
        if idx not in self._panels:
            _, _, PanelClass, _ = self.NAV_ITEMS[idx]
            self._panels[idx] = PanelClass(self._content)
        self._current_panel = self._panels[idx]
        if hasattr(self._current_panel, 'on_enter'):
            try: self._current_panel.on_enter()
            except: pass
        self._current_panel.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _load_sysinfo_async(self):
        def _collect():
            try:
                import platform
                user = os.environ.get("USERNAME","?")
                pc   = os.environ.get("COMPUTERNAME","?")
                os_name = platform.system() + " " + platform.release()
                cpu_name = "?"; ram_total = "?"
                try:
                    r = subprocess.run('powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).Name"', shell=True, capture_output=True, text=True, timeout=5)
                    cpu_name = r.stdout.strip()[:38] or "?"
                    r2 = subprocess.run('powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)"', shell=True, capture_output=True, text=True, timeout=5)
                    ram_total = r2.stdout.strip() + " GB"
                except Exception: pass
                return user, pc, os_name, cpu_name, ram_total
            except Exception: return "?","?","?","?","?"

        def _update(result):
            user, pc, os_name, cpu, ram = result
            try:
                self._header_canvas.itemconfig(self._info_ids["user_pc"], text=f"USER: {user}  |  PC: {pc}")
                self._header_canvas.itemconfig(self._info_ids["os"],      text=f"OS:   {os_name}")
                self._header_canvas.itemconfig(self._info_ids["cpu"],     text=f"CPU:  {cpu}")
                self._header_canvas.itemconfig(self._info_ids["ram"],     text=f"RAM:  {ram}")
            except Exception: pass

        def _thread():
            result = _collect()
            self.after(0, lambda: _update(result))
        threading.Thread(target=_thread, daemon=True).start()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--context-delete":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        if target and os.path.exists(target):
            if sys.platform == "win32":
                try: is_admin = ctypes.windll.shell32.IsUserAnAdmin()
                except Exception: is_admin = False
                if not is_admin:
                    args_str = " ".join([f'"{a}"' if ' ' in a else a for a in sys.argv[1:]])
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, args_str, None, 1)
                    sys.exit()
            
            if os.path.isfile(target):
                cmd = f'takeown /f "{target}" /a & icacls "{target}" /grant administrators:F /c /l /q & del /f /q /a "{target}"'
            else:
                cmd = f'takeown /f "{target}" /a /r /d y & icacls "{target}" /grant administrators:F /t /c /l /q & rd /s /q "{target}"'
            
            subprocess.run(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            root = tk.Tk()
            root.withdraw()
            if not os.path.exists(target):
                messagebox.showinfo("DEDSEC", f"Alvo ANIQUILADO com sucesso:\n\n{target}", master=root)
            else:
                messagebox.showwarning("DEDSEC", f"Falha ao apagar alvo (pode estar em uso):\n\n{target}", master=root)
            root.destroy()
        sys.exit(0)

    global USER_NAME

    if sys.platform == "win32" and not IS_ADMIN:
        try:
            # Determina o executável e os argumentos corretamente
            if getattr(sys, 'frozen', False):
                # Rodando como executável compilado (.exe)
                prog = sys.executable
                args = " ".join([f'"{a}"' for a in sys.argv[1:]])
            else:
                # Rodando como script (.py)
                prog = sys.executable
                # Garante caminho absoluto para o script
                script = os.path.abspath(sys.argv[0])
                args = f'"{script}" ' + " ".join([f'"{a}"' for a in sys.argv[1:]])
            
            # ShellExecuteW com 'runas' solicita elevação ao Windows
            ctypes.windll.shell32.ShellExecuteW(None, "runas", prog, args, None, 1)
            sys.exit(0)
        except Exception as e:
            # Se o usuário recusar o UAC ou der erro catastrófico
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("ERRO DE ELEVAÇÃO", 
                f"O Toolbox precisa de privilégios de Administrador para funcionar corretamente.\n\nErro: {e}", 
                master=root)
            sys.exit(1)

    root = ctk.CTk()
    root.withdraw()

    def launch_splash(name):
        """Depois do nome confirmado, roda splash e abre App."""
        global USER_NAME
        USER_NAME = name

        def launch_app():
            root.destroy()
            app = App()
            app.mainloop()

        SplashScreen(root, launch_app)

    # Verifica se já tem nome salvo
    saved = load_username()
    if saved:
        # Já tem nome — vai direto pra splash
        launch_splash(saved)
    else:
        # Primeira vez — mostra tela de boas-vindas
        WelcomeDialog(root, launch_splash)

    root.mainloop()


if __name__ == "__main__":
    main()
