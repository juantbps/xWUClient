#!/usr/bin/env python3
import gi
import subprocess

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')   # o '4.0' según tu sistema
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk, WebKit2, AppIndicator3, Notify, Gdk


WHATSAPP_URL = "https://web.whatsapp.com"
ICON_PATH = "/home/juantbps/.local/share/icons/whatsapp.png"


class WhatsAppTrayApp:
    def __init__(self):
        # Inicializar notificaciones
        Notify.init("WhatsApp Desktop")

        # Último título visto
        self.last_title = ""

        # Ventana principal
        self.window = Gtk.Window(title="WhatsApp Desktop")
        self.window.set_default_size(900, 700)
        self.window.connect("delete-event", self.on_window_delete)
        self.window.connect("window-state-event", self.on_window_state_event)

        # WebView con WhatsApp Web
        self.webview = WebKit2.WebView()
        self.webview.connect("decide-policy", self.on_decide_policy)
        self.webview.connect("notify::title", self.on_title_changed)
        self.webview.load_uri(WHATSAPP_URL)

        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.webview)
        self.window.add(scrolled)

        # Indicador de bandeja
        self.indicator = AppIndicator3.Indicator.new(
            "whatsapp-indicator",            # ID interno del indicador
            ICON_PATH,                       # nombre de icono del tema
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_icon_full(ICON_PATH, "WhatsApp Desktop")
        self.indicator.set_menu(self.build_menu())

        self.window.show_all()

        # Notificación de inicio para verificar que Notify funciona
        self.show_notification(
            "WhatsApp Desktop",
            "Cliente iniciado."
        )

    # ---------- Notificaciones ----------

    def show_notification(self, title, body):
        # Intento 1: libnotify
        try:
            note = Notify.Notification.new(title, body, None)
            note.show()
        except Exception as e:
            print(f"[Notify] Error libnotify: {e}")

        # Intento 2: notify-send (CLI)
        try:
            subprocess.run(["notify-send", title, body])
        except Exception as e:
            print(f"[Notify] Error notify-send: {e}")

    # ---------- Menú de bandeja ----------

    def build_menu(self):
        menu = Gtk.Menu()

        item_show = Gtk.MenuItem(label="Mostrar / Ocultar")
        item_show.connect("activate", self.toggle_window_visibility)
        menu.append(item_show)

        item_quit = Gtk.MenuItem(label="Salir")
        item_quit.connect("activate", self.quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def toggle_window_visibility(self, *_args):
        if self.window.get_visible():
            self.window.hide()
        else:
            self.window.show_all()
            self.window.present()

    def on_window_delete(self, *args):
        # Ocultar en vez de salir
        self.window.hide()
        self.show_notification(
            "WhatsApp Desktop",
            "La ventana se ha minimizado a la bandeja."
        )
        return True

    # ---------- Cambios de título (nuevos mensajes) ----------

    def on_title_changed(self, webview, pspec):
        title = webview.get_title() or ""
        print(f"[DEBUG] Título cambió a: {title}")

        has_unread = title.startswith("(")

        # Notificar cada vez que cambie el título y haya no leídos
        # solo cuando la ventana está oculta
        if has_unread and title != self.last_title:
            visible = self.window.get_visible()
            print(f"[DEBUG] visible={visible}, last_title={self.last_title}")

            if not visible:
                self.show_notification(
                    "Nuevo mensaje en WhatsApp",
                    f"Tienes nuevos mensajes ({title})."
                )

        self.last_title = title

    # ---------- Bloquear navegación fuera de WhatsApp ----------

    def on_decide_policy(self, webview, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            nav_action = decision.get_navigation_action()
            request = nav_action.get_request()
            uri = request.get_uri()

            if not uri.startswith(WHATSAPP_URL):
                decision.ignore()
                return True

        return False

    def quit(self, *_args):
        Gtk.main_quit()

    def on_window_state_event(self, window, event):
        """
        Si la ventana pasa a estado minimizado (iconified),
        la tratamos como si se hubiera "cerrado": la ocultamos
        y mostramos el mensaje de bandeja.
        """
        # ¿Cambió el estado de "iconified"?
        if event.changed_mask & Gdk.WindowState.ICONIFIED:
            # ¿Nuevo estado incluye minimizada?
            if event.new_window_state & Gdk.WindowState.ICONIFIED:
                # Reutilizamos la misma lógica de cerrar (X)
                return self.on_window_delete(window, None)

        # Para otros cambios de estado, no hacemos nada especial
        return False



if __name__ == "__main__":
    app = WhatsAppTrayApp()
    Gtk.main()
