################################################################################
#      Copyright (C) 2019 drinfernoo                                           #
#                                                                              #
#  This Program is free software; you can redistribute it and/or modify        #
#  it under the terms of the GNU General Public License as published by        #
#  the Free Software Foundation; either version 2, or (at your option)         #
#  any later version.                                                          #
#                                                                              #
#  This Program is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                #
#  GNU General Public License for more details.                                #
#                                                                              #
#  You should have received a copy of the GNU General Public License           #
#  along with XBMC; see the file COPYING.  If not, write to                    #
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.       #
#  http://www.gnu.org/copyleft/gpl.html                                        #
################################################################################

import xbmc
import xbmcgui

import os

from resources.libs import check
from resources.libs import db
from resources.libs import extract
from resources.libs import install
from resources.libs import skin
from resources.libs.common import logging
from resources.libs.common import tools
from resources.libs.common.config import CONFIG
from resources.libs.downloader import Downloader


class Wizard:

    def __init__(self):
        tools.ensure_folders(CONFIG.PACKAGES)
        
        self.dialog = xbmcgui.Dialog()
        self.dialogProgress = xbmcgui.DialogProgress()

    def _prompt_for_wipe(self):
        # Should we wipe first?
        if self.dialog.yesno(CONFIG.ADDONTITLE,
                           "[COLOR {0}]¿Desea restaurar la configuracion de Kodi".format(CONFIG.COLOR2) +'\n' + "a los valores predeterminados" + '\n' + "antes de instalar la copia de seguridad de la build?[/COLOR]",
                           nolabel='[B][COLOR white]NO[/COLOR][/B]',
                           yeslabel='[B][COLOR white]SI[/COLOR][/B]'):
            install.wipe()

    def build(self, name, over=False):
        # if action == 'normal':
            # if CONFIG.KEEPTRAKT == 'true':
                # from resources.libs import traktit
                # traktit.auto_update('all')
                # CONFIG.set_setting('traktnextsave', tools.get_date(days=3, formatted=True))
            # if CONFIG.KEEPDEBRID == 'true':
                # from resources.libs import debridit
                # debridit.auto_update('all')
                # CONFIG.set_setting('debridnextsave', tools.get_date(days=3, formatted=True))
            # if CONFIG.KEEPLOGIN == 'true':
                # from resources.libs import loginit
                # loginit.auto_update('all')
                # CONFIG.set_setting('loginnextsave', tools.get_date(days=3, formatted=True))

        temp_kodiv = int(CONFIG.KODIV)
        buildv = int(float(check.check_build(name, 'kodi')))

        if not temp_kodiv == buildv:
            warning = True
        else:
            warning = False

        if warning:
            yes_pressed = self.dialog.yesno("{0} - [COLOR white]ADVERTENCIA!![/COLOR]".format(CONFIG.ADDONTITLE), '[COLOR {0}]Existe la posibilidad de que el skin no aparezca correctamente'.format(CONFIG.COLOR2) + '\n' + 'al instalar una {0} build en kodi'.format(check.check_build(name, 'kodi'), CONFIG.KODIV) + '\n' + '¿Quieres instalar: [COLOR {0}]{1} v{2}[/COLOR]?[/COLOR]'.format(CONFIG.COLOR1, name, check.check_build(name, 'version')), nolabel='[B][COLOR white]NO[/COLOR][/B]', yeslabel='[B][COLOR white]SI[/COLOR][/B]')
        else:
            if over:
                yes_pressed = 1
            else:
                yes_pressed = self.dialog.yesno(CONFIG.ADDONTITLE, '[COLOR {0}]¿Te gustaria descargar e instalar: '.format(CONFIG.COLOR2) + '[COLOR {0}]{1} v{2}[/COLOR]?[/COLOR]'.format(CONFIG.COLOR1, name, check.check_build(name,'version')), yeslabel='[B][COLOR white]SI[/COLOR][/B]', nolabel='[B][COLOR white]NO[/COLOR][/B]')
        if yes_pressed:
            CONFIG.clear_setting('build')
            buildzip = check.check_build(name, 'url')
            zipname = name.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')

            self.dialogProgress.create(CONFIG.ADDONTITLE, '[COLOR {0}][B]Descargando:[/B][/COLOR] [COLOR {1}]{2} v{3}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name, check.check_build(name, 'version')) + '\n' + 'Por favor, espere')

            lib = os.path.join(CONFIG.MYBUILDS, '{0}.zip'.format(zipname))
            
            try:
                os.remove(lib)
            except:
                pass

            Downloader().download(buildzip, lib)
            xbmc.sleep(500)
            
            if os.path.getsize(lib) == 0:
                try:
                    os.remove(lib)
                except:
                    pass
                    
                return
                
            install.wipe()
                
            skin.look_and_feel_data('save')
            
            title = '[COLOR {0}][B]Instalando:[/B][/COLOR] [COLOR {1}]{2} v{3}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name, check.check_build(name, 'version'))
            self.dialogProgress.update(0, title + '\n' + 'Por favor, espere')
            percent, errors, error = extract.all(lib, CONFIG.HOME, title=title)
            
            skin.skin_to_default('Instalar Build')

            if int(float(percent)) > 0:
                db.fix_metas()
                CONFIG.set_setting('buildname', name)
                CONFIG.set_setting('buildversion', check.check_build(name, 'version'))
                CONFIG.set_setting('buildtheme', '')
                CONFIG.set_setting('latestversion', check.check_build(name, 'version'))
                CONFIG.set_setting('nextbuildcheck', tools.get_date(days=CONFIG.UPDATECHECK, formatted=True))
                CONFIG.set_setting('installed', 'true')
                CONFIG.set_setting('extract', percent)
                CONFIG.set_setting('errors', errors)
                logging.log('INSTALLED {0}: [ERRORS:{1}]'.format(percent, errors))

                try:
                    os.remove(lib)
                except:
                    pass

                if int(float(errors)) > 0:
                    yes_pressed = self.dialog.yesno(CONFIG.ADDONTITLE,
                                       '[COLOR {0}][COLOR {1}]{2} v{3}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name, check.check_build(name, 'version')) +'\n' + 'Completado: [COLOR {0}]{1}{2}[/COLOR] [Errores:[COLOR {3}]{4}[/COLOR]]'.format(CONFIG.COLOR1, percent, '%', CONFIG.COLOR1, errors) + '\n' + '¿Te gustaria ver los errores?[/COLOR]',
                                       yeslabel='[B][COLOR white]SI[/COLOR][/B]',
                                       nolabel='[B][COLOR white]NO[/COLOR][/B]')
                    if yes_pressed:
                        from resources.libs.gui import window
                        window.show_text_box("Vista de Errores de Instalacion de la Build", error)
                self.dialogProgress.close()

                from resources.libs.gui.build_menu import BuildMenu
                themecount = BuildMenu().theme_count(name)

                if themecount > 0:
                    self.theme(name)

                db.addon_database(CONFIG.ADDON_ID, 1)
                db.force_check_updates(over=True)
                if os.path.exists(os.path.join(CONFIG.USERDATA, '.enableall')):
                	CONFIG.set_setting('enable_all', 'true')

                self.dialog.ok(CONFIG.ADDONTITLE, "[COLOR {0}]Ahora pulsa OK para forzar el cierre de Kodi y guardar los cambios[/COLOR]".format(CONFIG.COLOR2))
                tools.kill_kodi(over=True)
            else:
                from resources.libs.gui import window
                window.show_text_box("Vista de Errores de Instalacion de la Build", error)
        else:
            logging.log_notify(CONFIG.ADDONTITLE,
                               '[COLOR {0}]Instalacion de Build Cancelada[/COLOR]'.format(CONFIG.COLOR2))

    def gui(self, name, over=False):
        if name == CONFIG.get_setting('buildname'):
            if over:
                yes_pressed = 1
            else:
                yes_pressed = self.dialog.yesno(CONFIG.ADDONTITLE,
                                   '[COLOR {0}]¿Quiere aplicar el Parche para:'.format(CONFIG.COLOR2) + '\n' + '[COLOR {0}]{1}[/COLOR]?[/COLOR]'.format(CONFIG.COLOR1, name),
                                   yeslabel='[B][COLOR white]SI[/COLOR][/B]',
                                   nolabel='[B][COLOR white]NO[/COLOR][/B]')
        else:
            yes_pressed = self.dialog.yesno("{0} - [COLOR white]ADVERTENCIA:[/COLOR]".format(CONFIG.ADDONTITLE),
                               "[COLOR {0}][COLOR {1}]{2}[/COLOR] La build no esta instalada todavia.".format(CONFIG.COLOR2, CONFIG.COLOR1, name) + '\n' + "¿Le gustaria aplicar el parche de todos modos?[/COLOR]",
                               yeslabel='[B][COLOR white]SI[/COLOR][/B]',
                               nolabel='[B][COLOR white]NO[/COLOR][/B]')
        if yes_pressed:
            guizip = check.check_build(name, 'gui')
            zipname = name.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')

            response = tools.open_url(guizip, check=True)
            if not response:
                logging.log_notify(CONFIG.ADDONTITLE,
                                   '[COLOR {0}]Parche: URL Zip incorrecta[/COLOR]'.format(CONFIG.COLOR2))
                return

            self.dialogProgress.create(CONFIG.ADDONTITLE, '[COLOR {0}][B]Descargando Parche:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name), '', 'Por favor, espere')

            lib = os.path.join(CONFIG.PACKAGES, '{0}_guisettings.zip'.format(zipname))
            
            try:
                os.remove(lib)
            except:
                pass

            Downloader().download(guizip, lib)
            xbmc.sleep(500)
            
            if os.path.getsize(lib) == 0:
                try:
                    os.remove(lib)
                except:
                    pass
                    
                return
            
            title = '[COLOR {0}][B]Instalando:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, name)
            self.dialogProgress.update(0, title + '\n' + 'Por favor, espere')
            extract.all(lib, CONFIG.USERDATA, title=title)
            self.dialogProgress.close()
            skin.skin_to_default('Instalar Build')
            skin.look_and_feel_data('save')
            installed = db.grab_addons(lib)
            db.addon_database(installed, 1, True)

            self.dialog.ok(CONFIG.ADDONTITLE, "[COLOR {0}]Ahora pulsa OK para forzar el cierre de Kodi y guardar los cambios[/COLOR]".format(CONFIG.COLOR2))
            tools.kill_kodi(over=True)
        else:
            logging.log_notify(CONFIG.ADDONTITLE,
                               '[COLOR {0}]Parche: Cancelado[/COLOR]'.format(CONFIG.COLOR2))

    def theme(self, name, theme='', over=False):
        installtheme = False

        if not theme:
            themefile = check.check_build(name, 'theme')

            response = tools.open_url(themefile, check=True)
            if response:
                from resources.libs.gui.build_menu import BuildMenu
                themes = BuildMenu().theme_count(name, False)
                if len(themes) > 0:
                    if self.dialog.yesno(CONFIG.ADDONTITLE, "[COLOR {0}]La Build [COLOR {1}]{2}[/COLOR] viene con [COLOR {3}]{4}[/COLOR] diferentes temas".format(CONFIG.COLOR2, CONFIG.COLOR1, name, CONFIG.COLOR1, len(themes)) + '\n' + "¿Le gustaria instalar uno ahora?[/COLOR]",
                                    yeslabel="[B][COLOR white]SI[/COLOR][/B]",
                                    nolabel="[B][COLOR white]NO[/COLOR][/B]"):
                        logging.log("Lista de Temas: {0}".format(str(themes)))
                        ret = self.dialog.select(CONFIG.ADDONTITLE, themes)
                        logging.log("Instalar Tema Seleccionado: {0}".format(ret))
                        if not ret == -1:
                            theme = themes[ret]
                            installtheme = True
                        else:
                            logging.log_notify(CONFIG.ADDONTITLE,
                                               '[COLOR {0}]Instalar Tema: Cancelado[/COLOR]'.format(CONFIG.COLOR2))
                            return
                    else:
                        logging.log_notify(CONFIG.ADDONTITLE,
                                           '[COLOR {0}]Instalar Tema: Cancelado[/COLOR]'.format(CONFIG.COLOR2))
                        return
            else:
                logging.log_notify(CONFIG.ADDONTITLE,
                                   '[COLOR {0}]Instalar Tema: No Encontrado[/COLOR]'.format(CONFIG.COLOR2))
        else:
            installtheme = self.dialog.yesno(CONFIG.ADDONTITLE, '[COLOR {0}]¿Le gustaria instalar el tema:'.format(CONFIG.COLOR2) +' \n' + '[COLOR {0}]{1}[/COLOR]'.format(CONFIG.COLOR1, theme) + '\n' + 'para [COLOR {0}]{1} v{2}[/COLOR]?[/COLOR]'.format(CONFIG.COLOR1, name, check.check_build(name,'version')),yeslabel="[B][COLOR white]SI[/COLOR][/B]", nolabel="[B][COLOR white]NO[/COLOR][/B]")
                                        
        if installtheme:
            themezip = check.check_theme(name, theme, 'url')
            zipname = name.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')

            response = tools.open_url(themezip, check=True)
            if not response:
                logging.log_notify(CONFIG.ADDONTITLE,
                                   '[COLOR {0}]Instalar Tema: URL Zip incorrecta[/COLOR]'.format(CONFIG.COLOR2))
                return False

            self.dialogProgress.create(CONFIG.ADDONTITLE, '[COLOR {0}][B]Descargando:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, zipname) +' \n' + 'Por favor, espere')

            lib = os.path.join(CONFIG.PACKAGES, '{0}.zip'.format(zipname))
            
            try:
                os.remove(lib)
            except:
                pass

            Downloader().download(themezip, lib)
            xbmc.sleep(500)
            
            if os.path.getsize(lib) == 0:
                try:
                    os.remove(lib)
                except:
                    pass
                    
                return
            
            self.dialogProgress.update(0, '\n' + "Instalando {0}".format(name))

            test1 = False
            test2 = False
            
            from resources.libs import skin
            from resources.libs import test
            test1 = test.test_theme(lib) if CONFIG.SKIN not in skin.DEFAULT_SKINS else False
            test2 = test.test_gui(lib) if CONFIG.SKIN not in skin.DEFAULT_SKINS else False

            if test1:
                skin.look_and_feel_data('save')
                swap = skin.skin_to_default('Instalar Tema')

                if not swap:
                    return False

                xbmc.sleep(500)

            title = '[COLOR {0}][B]Instalando Tema:[/B][/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, theme)
            self.dialogProgress.update(0, title + '\n' + 'Por favor, espere')
            percent, errors, error = extract.all(lib, CONFIG.HOME, title=title)
            CONFIG.set_setting('buildtheme', theme)
            logging.log('INSTALLED {0}: [ERRORS:{1}]'.format(percent, errors))
            self.dialogProgress.close()

            db.force_check_updates(over=True)
            installed = db.grab_addons(lib)
            db.addon_database(installed, 1, True)

            if test2:
                skin.look_and_feel_data('save')
                skin.skin_to_default("Instalar Tema")
                gotoskin = CONFIG.get_setting('defaultskin')
                skin.switch_to_skin(gotoskin, "Instalar Tema")
                skin.look_and_feel_data('restore')
            elif test1:
                skin.look_and_feel_data('save')
                skin.skin_to_default("Instalar Tema")
                gotoskin = CONFIG.get_setting('defaultskin')
                skin.switch_to_skin(gotoskin, "Instalar Tema")
                skin.look_and_feel_data('restore')
            else:
                xbmc.executebuiltin("ReloadSkin()")
                xbmc.sleep(1000)
                xbmc.executebuiltin("Container.Refresh()")
        else:
            logging.log_notify(CONFIG.ADDONTITLE,
                               '[COLOR {0}]Instalar Tema: Cancelado[/COLOR]'.format(CONFIG.COLOR2))


def wizard(action, name, url):
    cls = Wizard()

    if action in ['fresh', 'normal']:
        cls.build(action, name)
    elif action == 'gui':
        cls.gui(name)
    elif action == 'theme':
        cls.theme(name, url)
