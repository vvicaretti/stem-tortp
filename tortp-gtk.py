#!/usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk
import gobject
import gettext
import tortp

gettext.bindtextdomain('./locale')
gettext.textdomain('tortp')
_ = gettext.gettext


class Icon(gtk.StatusIcon):

    def __init__(self):
        gtk.StatusIcon.__init__(self)
        self.set_from_file('/usr/share/pixmaps/anonymous.ico')
        self.connect("activate", self.load)
        self.connect("popup-menu", self.right_click_event)
        self.set_tooltip("TorTP")
        self.window = None
        self.load(None)

    def start(self):
        gtk.main()

    def stop(self):
        gtk.main_quit()

    def load(self, param):
        if self.window is None:
            self.window = MainWindow()
            self.window.connect("destroy", self.clear_window)

    def clear_window(self, widget, data=None):
        self.window = None

    def right_click_event(self, icon, button, time):
        menu = gtk.Menu()
        about = gtk.MenuItem("About")
        quit = gtk.MenuItem("Quit")

        about.connect("activate", self.show_about_dialog)
        quit.connect("activate", gtk.main_quit)

        menu.append(about)
        menu.append(quit)
        menu.show_all()
        menu.popup(None, None, gtk.status_icon_position_menu, button, time, self)

    def show_about_dialog(self, widget):
        about_dialog = gtk.AboutDialog()
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name("TorTransparentProxy")
        about_dialog.set_website("https://github.com/vinc3nt/stem-tortp")
        about_dialog.set_version("0.1")
        about_dialog.set_authors(["vinc3nt", "paskao"])

        about_dialog.run()
        about_dialog.destroy()


class MainWindow(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_border_width(10)

        box = gtk.VBox(False, 0)
        notebook = gtk.Notebook()
        box.add(notebook)
        self.add(box)

        tp = TransparentProxyBox()
        label = gtk.Label(_("Transparent Proxy"))
        notebook.append_page(tp, label)

        tpinfo = TransparentProxyInfoBox()
        tpinfo.set_scroll_adjustments(None, None)
	scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        scroll.add_with_viewport(tpinfo)
        label_info = gtk.Label(_("Infos"))
        notebook.append_page(scroll, label_info)

        self.show_all()


class TransparentProxyInfoBox(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self, False, 0)
        self.liststore = gtk.ListStore(str, str, str)
        self.treeview = gtk.TreeView(model=self.liststore)
        self.add(self.treeview)
        renderer_text = gtk.CellRendererText()
        column0 = gtk.TreeViewColumn("Fingerprint", renderer_text, text=0)
        self.treeview.append_column(column0)
        column1 = gtk.TreeViewColumn("Nickname", renderer_text, text=1)
        self.treeview.append_column(column1)
        column2 = gtk.TreeViewColumn("IP address", renderer_text, text=2)
        self.treeview.append_column(column2)
        self.load_model()

    def load_model(self):
       self.liststore.clear()
       try:
           for item in tortp.get_info():
               self.liststore.append(item)
       except:
           pass
       gobject.timeout_add_seconds(5, self.load_model)


class TransparentProxyBox(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self, False, 0)
	self.description_text = _("""TorTP Redirige in maniera trasparente tutto il traffico TCP ed UDP (dns) generato dall'utente paranoid verso la rete Tor.\r\n
    Dopo aver avviato TORtp assicurati che Tor stia funzionando visitando questa pagina: https://check.torproject.org""")

        self.buttons_box = gtk.HButtonBox()
        self.buttons_box.set_layout(gtk.BUTTONBOX_START)
        self.description = gtk.Label(self.description_text)
        self.start_button = gtk.Button("Start")
        self.change_button = gtk.Button("New circuit")
        self.stop_button = gtk.Button("Stop")
        self.description.set_line_wrap(True)
        self.description.set_single_line_mode(False)

        self.start_button.connect("clicked", self.start, None)
        self.change_button.connect("clicked", self.change, None)
        self.stop_button.connect("clicked", self.stop, None)

        # Add components
        self.buttons_box.add(self.start_button)
        self.buttons_box.add(self.change_button)
        self.buttons_box.add(self.stop_button)
        self.add(self.description)
        self.add(self.buttons_box)

        is_running = tortp.is_running()
        self.start_button.set_sensitive(not is_running)
        self.change_button.set_sensitive(is_running)
        self.stop_button.set_sensitive(is_running)

    def start(self, widget, data=None):
        tortp.do_start()
        self.start_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)
        self.change_button.set_sensitive(True)

    def change(self, widget, data=None):
        tortp.tor_new()

    def stop(self, widget, data=None):
        tortp.do_stop()
        self.start_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.change_button.set_sensitive(False)


if __name__ == "__main__":
    icon = Icon()
    icon.start()
