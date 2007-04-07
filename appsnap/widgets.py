import defines
import process
import strings
import threading
import time
import wx
import wx.lib.hyperlink

# Application panel
class ApplicationPanel(wx.Panel):
    # Constructor
    def __init__(self, parent, label, description, url, gui, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL | wx.NO_BORDER):
        wx.Panel.__init__(self, parent, -1, pos=pos, size=size, style=style)

        # State information
        self.gui = gui
        self.app_name = label
        self.selected = False
        self.process = False
        
        # Widgets
        self.label = wx.StaticText(self, -1, label)
        self.label.SetFont(self.gui.objects['sectionfont'])

        self.checkbox = wx.CheckBox(self, -1)
        self.description = wx.StaticText(self, -1, description)

        self.version = wx.StaticText(self, -1, '')
        self.installed_version = wx.StaticText(self, -1, '')
        
        self.url = wx.lib.hyperlink.HyperLinkCtrl(self)
        self.url.SetFont(self.gui.objects['urlfont'])
        self.url.SetLabel(">>")
        self.url.SetURL(url)
        self.url.SetToolTipString(url)
        self.url.SetUnderlines(False, False, False)
        self.url.SetColours(self.gui.objects['bluecolour'], self.gui.objects['bluecolour'])
        
        self.status = wx.StaticText(self, -1, '')
        
        # Size
        self.SetMinSize(size)
        self.SetMaxSize(size)
        
        # Events
        self.setup_click_event([self, self.label, self.description, self.version, self.installed_version])
        wx.EVT_CHECKBOX(self.gui.objects['frame'], self.checkbox.GetId(), self.on_checkbox_click)
    
    #####
    # Setup helpers
    
    # Set the position of all elements
    def set_position(self):
        self.label.SetPosition((40, 10))
        self.checkbox.SetPosition((10, 20))
        self.description.SetPosition((40, 30))
        self.url.SetPosition((45 + self.label.GetSize().GetWidth(), 10))
        if self.version.GetLabel() != '':
            self.version.SetPosition((40, 45))
        if self.installed_version.GetLabel() != '':
            self.installed_version.SetPosition((40, 60))

    # Set event object
    def set_event(self, event):
        self.event = event

    # Setup left click event
    def setup_click_event(self, widgets):
        for widget in widgets:
            wx.EVT_LEFT_DOWN(widget, self.on_click)
            wx.EVT_LEFT_DCLICK(widget, self.on_click)
        
    # Set the colour of panel based on row number
    def set_colour_by_row(self, row):
        self.save_colour_by_row(row)
        self.SetBackgroundColour(self.row_colour)

    #####
    # Display helpers

    # Display version information
    def set_version(self, version):
        if self.selected == True:
            self.version.SetLabel(version)
            self.version.SetPosition((40, 45))

    # Hide version information
    def unset_version(self):
        self.version.SetLabel('')
        self.version.SetPosition((0, 0))

    # Display installed version
    def set_installed_version(self, installed_version):
        if self.selected == True:
            self.installed_version.SetLabel(installed_version)
            self.installed_version.SetPosition((40, 60))

    # Hide installed version
    def unset_installed_version(self):
        self.installed_version.SetLabel('')
        self.installed_version.SetPosition((0, 0))
        
    # Set status text
    def set_status_text(self, text):
        self.status.SetLabel(strings.STATUS + ' : ' + text)

    # Display status information
    def display_status(self):
        if self.selected == True:
            if self.installed_version.GetLabel() != '':
                self.status.SetPosition((40, 75))
            else:
                self.status.SetPosition((40, 60))
            self.set_status_text(strings.STARTING + ' ...')
            self.update_layout()
            
    # Hide status information
    def hide_status(self):
        self.status.SetLabel('')
        self.status.SetPosition((0, 0))

    # Show version information
    def show_info(self):
        # Get configuration
        items = self.event.configuration.get_section_items(self.app_name)

        # Get installed version
        installed_version = self.event.configuration.get_installed_version(self.app_name)
        if installed_version != '':
            installed_version = strings.INSTALLED_VERSION + ' : ' + installed_version
            self.set_installed_version(installed_version)

        # Display latest version text
        self.set_version(strings.LATEST_VERSION + ' : ' + strings.LOADING + ' ...')
        
        # Update layout
        self.update_layout()
        
        # Get the latest version
        if not self.process:
            self.process = process.process(self.event.configuration, self.event.curl_instance, self.app_name, items)
        latest_version = self.process.get_latest_version()
        if latest_version == None:
            latest_version = strings.FAILED_TO_CONNECT
        self.set_version(strings.LATEST_VERSION + ' : ' + latest_version)

    # Hide information
    def hide_info(self):
        self.unset_version()
        self.unset_installed_version()
        self.hide_status()
        self.update_layout()

    # Update the layout of this panel
    def update_layout(self):
        # Get event lock
        self.event.lock.acquire()
        
        height = defines.SECTION_HEIGHT
        if self.version.GetLabel() != '': height += defines.SECTION_HEIGHT_INCREMENT
        if self.installed_version.GetLabel() != '': height += defines.SECTION_HEIGHT_INCREMENT
        if self.status.GetLabel() != '': height += defines.SECTION_HEIGHT_INCREMENT
        
        self.SetMinSize((self.GetMinWidth(), height))
        self.SetMaxSize((self.GetMinWidth(), height))
        self.Refresh()
        self.gui.objects['bsizer'].Layout()
        self.gui.objects['bsizer'].FitInside(self.gui.objects['scrollwindow'])
        self.gui.objects['scrollwindow'].Refresh()
        
        # Release lock
        self.event.lock.release()

    # Select if upgradeable
    def display_if_upgradeable(self, sizeritem):
        # Get the version information populated
        self.selected = True
        self.SetBackgroundColour(self.gui.objects['lightbluecolour'])
        self.show_info()
        
        installed_version = self.event.configuration.get_installed_version(self.app_name)
        latest_version = self.process.get_latest_version()
        if installed_version >= latest_version:
            self.select(False)
            sizeritem.Show(False)

    #####
    # State helpers

    # Select application
    def select(self, value):
        if value == True:
            self.selected = True
            self.SetBackgroundColour(self.gui.objects['lightredcolour'])
            child = threading.Thread(target=self.show_info)
            child.setDaemon(True)
            child.start()
        else:
            self.selected = False
            self.SetBackgroundColour(self.row_colour)
            self.checkbox.SetValue(False)
            self.hide_info()
        
    # Reset state
    def reset(self):
        self.selected = False
        self.checkbox.SetValue(False)
        self.unset_version()
        self.unset_installed_version()
        self.hide_status()
        self.SetMinSize((self.GetMinWidth(), defines.SECTION_HEIGHT))
        
    # Save row colour
    def save_colour_by_row(self, row):
        # Color
        if (row % 4 == 0):
            self.row_colour = self.gui.objects['darkgreycolour']
        elif (row % 2 == 0):
            self.row_colour = self.gui.objects['lightgreycolour']
        else:
            self.row_colour = self.gui.objects['whitecolour']

    #####
    # Event methods
    
    # When panel or text is clicked
    def on_click(self, event):
        self.SetFocus()
        if self.selected == True and self.checkbox.IsChecked() == False:
            self.select(False)
        elif self.selected == False and self.checkbox.IsChecked() == False:
            self.selected = True
            self.SetBackgroundColour(self.gui.objects['lightbluecolour'])
            child = threading.Thread(target=self.show_info)
            child.setDaemon(True)
            child.start()
        
    # When checkbox is clicked
    def on_checkbox_click(self, event):
        self.SetFocus()
        if event.IsChecked() == True:
            self.select(True)
        else:
            self.select(False)

    # Perform specified action
    def do_action(self, action):
        # Display status field
        self.display_status()
        
        if action == process.ACT_DOWNLOAD or action == process.ACT_INSTALL or action == process.ACT_UPGRADE:
            # Download latest version
            self.set_status_text(strings.WAITING + ' ...')
            if self.process.download_latest_version(self.update_download_status) == False:
                return self.error_out(strings.DOWNLOAD_FAILED)

        if action == process.ACT_UNINSTALL or (action == process.ACT_UPGRADE and self.process.app_config[process.APP_UPGRADES] == 'true'):
            # Perform the uninstall, use lock to ensure only one install/uninstall at a time
            self.set_status_text(strings.UNINSTALLING + ' ...')
            self.event.lock.acquire()
            uninstall_successful = self.process.uninstall_version()
            self.event.lock.release()
            if uninstall_successful == False:
                return self.error_out(strings.UNINSTALL_FAILED)

        if action == process.ACT_INSTALL or action == process.ACT_UPGRADE:
            # Perform the install, use lock to ensure only one install/uninstall at a time
            self.set_status_text(strings.INSTALLING + ' ...')
            self.event.lock.acquire()
            install_successful = self.process.install_latest_version()
            self.event.lock.release()
            if install_successful == False:
                return self.error_out(strings.INSTALL_FAILED)

        # Done
        self.set_status_text(strings.DONE)
        time.sleep(defines.SLEEP_GUI_SECTION_ACTION_DONE)

        # Succeeded so unselect
        self.select(False)
        
    # Callback function for PyCurl
    def update_download_status(self, dl_total, dl_current, ul_total, ul_current):
        # Create current string
        if dl_current < 1024 * 1024:
            dl_current_string = round((dl_current / 1024), 2).__str__() + ' KB'
        else:
            dl_current_string = round((dl_current / 1024 / 1024), 2).__str__() + ' MB'

        # Create total string
        if dl_total < 1024 * 1024:
            dl_total_string = round((dl_total / 1024), 2).__str__() + ' KB'
        else:
            dl_total_string = round((dl_total / 1024 / 1024), 2).__str__() + ' MB'
            
        # Percentage string
        if dl_total != 0:
            percentage_string = ' [' + int(dl_current / dl_total * 100).__str__() + '%]'
        else:
            percentage_string = ''

        self.set_status_text(strings.DOWNLOADED + ' ' + dl_current_string + ' / ' + dl_total_string + percentage_string)

    # Error out if any action fails
    def error_out(self, action):
        # Mark as failed
        self.set_status_text(action)
        
        # Return
        return False