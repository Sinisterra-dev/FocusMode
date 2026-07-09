# Focus Mode

Aplicación de escritorio para Windows (Python + CustomTkinter) que bloquea sitios web durante sesiones de estudio mediante el archivo `HOSTS`.

## Características

- Interfaz moderna en tema oscuro.
- Gestión dinámica de sitios bloqueados desde la UI.
- Temporizador con presets (15m, 30m, 45m, 1h, 2h, 3h) y modo personalizado.
- Cuenta regresiva grande en tiempo real.
- Bloqueo real de dominios (`dominio`, `www.dominio`, `m.dominio`).
- Respaldo y restauración segura del archivo HOSTS.
- Persistencia JSON de sesión, duración y sitios.
- Recuperación automática de sesión activa tras reinicio del sistema/app.
- Solicitud automática de privilegios de administrador (UAC).
- Modo estricto opcional (bloquea intentos de cierre y registra intentos en log).

## Estructura

- `main.py`: punto de entrada.
- `ui.py`: interfaz y flujo principal.
- `hosts_manager.py`: edición/restauración segura de HOSTS.
- `timer.py`: temporizador en hilo separado.
- `config.py`: persistencia JSON.
- `utils.py`: privilegios, lock de instancia y utilidades.
- `assets/`: recursos visuales.
- `INSTRUCCIONES.md`: documentación técnica profunda.

## Requisitos

- Python 3.13+
- Windows (obligatorio para bloqueo real en `C:\Windows\System32\drivers\etc\hosts`)

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

> La app solicitará elevación UAC automáticamente si no tiene privilegios de administrador.

## Compilar a ejecutable (PyInstaller)

Instala PyInstaller:

```bash
pip install pyinstaller
```

Compila:

```bash
pyinstaller --noconfirm --onefile --windowed --name "FocusMode" main.py
```

El ejecutable quedará en `dist/FocusMode.exe`.

## Persistencia

La configuración se guarda en:

- `%APPDATA%\FocusMode\config.json`
- `%APPDATA%\FocusMode\strict_mode.log` (si aplica)

## Advertencia

Esta aplicación modifica el archivo HOSTS del sistema. Usar bajo responsabilidad y solo para propósitos legítimos de productividad/estudio.
