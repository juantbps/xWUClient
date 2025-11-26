#!/usr/bin/env python3
import gi

gi.require_version('Gtk', '3.0')
# Si instalaste gir1.2-webkit2-4.0, cambia a '4.0'
gi.require_version('WebKit2', '4.1')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk, WebKit2, AppIndicator3, Notify, GLib

WHATSAPP_URL = "https://web.whatsapp.com"


class RunRunWhatsApp:
    def __init__(self):
        # Inicializar notificaciones
        Notify.init("RunRun WhatsApp")

        # Ventana principal
        self.window = Gtk.Window(title="RunRun WhatsApp")
        self.window.set_default_size(900, 700)
        self.window.connect("delete-event", self.on_window_delete)

        # WebView con WhatsApp Web
        self.webview = WebKit2.WebView()
        self.webview.connect("decide-policy", self.on_decide_policy)
        self.webview.load_uri(WHATSAPP_URL)

        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.webview)
        self.window.add(scrolled)

        # Indicador de bandeja
        self.indicator = AppIndicator3.Indicator.new(
            "runrun-whatsapp",
            "applications-internet",  # icono base del sistema
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

        self.window.show_all()

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
        # En lugar de salir, esconder a la bandeja
        self.window.hide()

        # Notificación informativa la primera vez que cierras
        note = Notify.Notification.new(
            "RunRun WhatsApp",
            "La ventana se ha minimizado a la bandeja.",
            None
        )
        try:
            note.show()
        except Exception:
            # Si Notify falla por permisos/compositor, ignoramos
            pass

        return True  # True = no destruir la ventana

    def on_decide_policy(self, webview, decision, decision_type):
        # Bloquear navegación fuera de WhatsApp Web
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            nav_decision = decision
            request = nav_decision.get_request()
            uri = request.get_uri()

            if not uri.startswith(WHATSAPP_URL):
                # Aquí solo bloqueamos; más adelante si quieres
                # podemos abrir estos links en el navegador por defecto.
                nav_decision.ignore()
                return True

        return False  # comportamiento por defecto

    def quit(self, *_args):
        Gtk.main_quit()


if __name__ == "__main__":
    app = RunRunWhatsApp()
    Gtk.main()
